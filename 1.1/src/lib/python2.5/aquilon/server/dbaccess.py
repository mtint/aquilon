#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""All database access should funnel through this module to ensure that it
is properly backgrounded within twisted, and not blocking execution.

Most methods will be called as part of a callback chain, and should
expect to handle a generic result from whatever happened earlier in
the chain.

"""

import os
import re
import exceptions

from sasync.database import AccessBroker, transact
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy import and_, or_
from twisted.internet import defer
from twisted.python import log
from twisted.python.failure import Failure

from aquilon import const
from aquilon.exceptions_ import RollbackException, NotFoundException, \
        AuthorizationException, ArgumentError
from formats import printprep
from aquilon.aqdb.location import Location, LocationType, Company, Hub, \
        Continent, Country, City, Building, Rack, Chassis, Desk
from aquilon.aqdb.network import DnsDomain
from aquilon.aqdb.service import Host, QuattorServer, Domain, Service, BuildItem
from aquilon.aqdb.configuration import Archetype, CfgPath, CfgTLD
from aquilon.aqdb.auth import UserPrincipal, Realm
from aquilon.aqdb.hardware import *
from aquilon.aqdb.interface import PhysicalInterface

# FIXME: This probably belongs in location.py
const.location_types = ("company", "hub", "continent", "country", "city",
        "building", "rack", "chassis", "desk")

class DatabaseBroker(AccessBroker):
    """All database access eventually funnels through this class, to
    correctly handle backgrounding / threading within twisted.

    As a general rule, the methods here should reflect the actions
    being invoked by the client.
    """
    def __init__(self, *url, **kwargs):
        AccessBroker.__init__(self, *url, **kwargs)
        self.safe_url = url and url[0] or ""
        m = re.match(r'^(oracle://.*?:)(.*)(@.*?)$', self.safe_url)
        if m:
            self.safe_url = m.group(1) + '********' + m.group(3)

    def startup(self):
        """This method normally creates Deferred objects for setting up
        the tables.  However, in our setup, all this work has already
        been done by importing aquilon.aqdb modules.
        """
        pass

    # expects to be run in a transact with a session...
    def _get_domain(self, domain):
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError, e:
            raise NotFoundException("Domain %s not found: %s"
                    % (domain, str(e)))
        return dbdomain

    # expects to be run in a transact with a session...
    def _get_status(self, status):
        try:
            dbstatus = self.session.query(Status).filter_by(name=status).one()
        except InvalidRequestError, e:
            raise ArgumentError("Status %s invalid (try one of %s): %s"
                    % (status, str(self.session.query(Status).all()), str(e)))
        return dbstatus

    # expects to be run in a transact with a session...
    def _get_machine(self, machine):
        try:
            dbmachine = self.session.query(Machine).filter_by(
                    name=machine).one()
        except InvalidRequestError, e:
            raise NotFoundException("Machine %s not found: %s"
                    % (machine, str(e)))
        return dbmachine

    # expects to be run in a transact with a session...
    def _get_service(self, service):
        try:
            dbservice = self.session.query(Service).filter_by(
                    name=service).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service '%s' not found: %s" % (service, e))
        return dbservice

    @transact
    def verify_add_host(self, result, hostname, machine, domain, status,
            **kwargs):
        # To be able to enter this host into DSDB, there must be
        # - A valid machine being attached
        # - A bootable interface attached to the machine
        # - An IP Address attached to the interface
        # Assumes domain has been verified separately with verify_domain...
        dbdomain = self._get_domain(domain)
        dbstatus = self._get_status(status)
        dbmachine = self._get_machine(machine)
        if not dbmachine.interfaces:
            raise ArgumentError("Machine '%s' has no interfaces." % machine)
        found_boot = False
        for interface in dbmachine.interfaces:
            if interface.boot:
                if found_boot:
                    # FIXME: Is this actually a problem?
                    raise ArgumentError("Multiple interfaces on machine '%s' are marked bootable" % machine)
                found_boot = True
        if not found_boot:
            raise ArgumentError("Machine '%s' requires a bootable interface." % machine)
        (short, dbdns_domain) = self._hostname_to_domain_and_string(hostname)
        if self.session.query(Host).filter_by(name=short,
                dns_domain=dbdns_domain).all():
            # The dsdb call would fail since the IP address is already in use...
            raise ArgumentError("Host '%s' already exists." % hostname)
        return printprep((short, dbdns_domain, dbmachine))

    @transact
    def add_host(self, result, hostname, machine, archetype, domain, status, **kwargs):
        # Assumes host has been added to dsdb.
        dbdomain = self._get_domain(domain)
        dbstatus = self._get_status(status)
        dbmachine = self._get_machine(machine)
        (short, dbdns_domain) = self._hostname_to_domain_and_string(hostname)
        host = Host(dbmachine, dbdomain, dbstatus, name=short,
                dns_domain=dbdns_domain,archetype=archetype)
        self.session.save(host)
        return printprep(host)

    @transact
    def verify_del_host(self, result, hostname, **kwargs):
        host = self._hostname_to_host(hostname)
        return printprep(host.machine)

    @transact
    def del_host(self, result, hostname, **kwargs):
        # Assumes host has been deleted from dsdb.
        host = self._hostname_to_host(hostname)
        # Hack to make sure the machine object is refreshed in future queries.
        dbmachine = host.machine
        for template in host.templates:
            log.msg("Before deleting host '%s', removing template '%s'"
                    % (host.fqdn, template.cfg_path))
            self.session.delete(template)
        self.session.delete(host)
        self.session.flush()
        self.session.refresh(dbmachine)
        return

    @transact
    def show_host_all(self, result, **kwargs):
        """Hacked such that printing the list out to a client only
        shows fqdn.  Ideally, the printing layer would handle this
        intelligently - print only fqdn for a list of hosts in raw 
        mode, or fqdn plus links in html.
        
        """
        return [host.fqdn for host in self.session.query(Host).all()]

    @transact
    def show_host(self, result, hostname, **kwargs):
        return printprep(self._hostname_to_host(hostname))

    @transact
    def verify_host(self, result, hostname, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        return dbhost.fqdn

    @transact
    def add_location(self, result, name, type, parentname, parenttype,
            fullname, comments, user, **kwargs):
        newLocation = self.session.query(Location).filter_by(name=name
                ).join('type').filter_by(type=type).first()
        if newLocation:
            # FIXME: Technically this is coming in with an http PUT,
            # which should try to adjust state and succeed if everything
            # is alright.
            raise ArgumentError("Location name=%s type=%s already exists."
                    % (name, type))
        try:
            parent = self.session.query(Location).filter_by(name=parentname
                    ).join('type').filter_by(type=parenttype).one()
        except InvalidRequestError:
            raise ArgumentError(
                    "Parent Location type='%s' name='%s' not found."
                    % (parenttype, parentname))
        # Incoming looks like 'city', need the City class.
        location_type = globals()[type.capitalize()]
        if not issubclass(location_type, Location):
            raise ArgumentError("%s is not a known location type" % type)
        try:
            dblt = self.session.query(LocationType).filter_by(type=type).one()
        except InvalidRequestError:
            raise ArgumentError("Invalid type '%s'" % type)

        # Figure out if it is valid to add this type of child to the parent...
        found_parent = False
        found_new = False
        for t in const.location_types:
            if t == parenttype:
                # Great, found the parent type in the list before requested type
                found_parent = True
                continue
            if t != type:
                # This item is neither parent nor new, keep going...
                continue
            # Moment of truth.
            if found_parent:
                # We saw the parent earlier - life is good.
                found_new = True
                break
            raise ArgumentError("type %s cannot be a parent of %s",
                    (parenttype, type))
        if not found_new:
            raise ArgumentError("unknown type %s", type)

        optional_args = {}
        if fullname:
            optional_args["fullname"] = fullname
        if comments:
            optional_args["comments"] = comments

        newLocation = location_type(name=name, type_name=dblt,
                parent=parent, owner=user, **optional_args)
        return printprep([newLocation])

    @transact
    def del_location(self, result, name, type, user, **kwargs):
        try:
            oldLocation = self.session.query(Location).filter_by(name=name
                    ).join('type').filter_by(type=type).one()
        except InvalidRequestError:
            raise NotFoundException(
                    "Location type='%s' name='%s' not found."
                    % (type, name))
        self.session.delete(oldLocation)
        return

    @transact
    def show_location(self, result, type=None, name=None, **kwargs):
        #log.msg("Attempting to generate a query...")
        query = self.session.query(Location)
        if type:
            # Not this easy...
            #kwargs["LocationType.type"] = type
            #log.msg("Attempting to add a type...")
            query = query.join('type').filter_by(type=type)
            query = query.reset_joinpoint()
        if name:
            try:
                #log.msg("Attempting query for one...")
                return printprep([query.filter_by(name=name).one()])
            except InvalidRequestError:
                raise NotFoundException(
                        "Location type='%s' name='%s' not found."
                        % (type, name))
        #log.msg("Attempting to query for all...")
        return printprep(query.all())

    @transact
    def show_location_type(self, result, user, **kwargs):
        return printprep(
                self.session.query(LocationType).filter_by(**kwargs).all())

    @transact
    def make_aquilon(self, result, build_info, hostname, os, **kwargs):
        """This takes the specified parameters and sets up the database
        relationships to create a quattor managed host.

        It does *not* create the pan template or compile the template -
        that logic is outside this method.
        """

        dbhost = self._hostname_to_host(hostname)
        # Currently, for the Host to be created it *must* be associated with
        # a Machine already.  If that ever changes, need to check here and
        # bail if dbhost.machine does not exist.

        # FIXME: This should be saved/stored with the Host.
        # The archetype will factor into the include path for the compiler.
        # There are several other scattered FIXMEs that where the aquilon
        # archetype is hard coded.
        archetype = self.session.query(Archetype).filter(
                Archetype.name=="aquilon").one()

        # Need to get all the BuildItem objects for this host.
        # They should include:
        # - exactly one OS
        # - exactly one personality
        # And may include:
        # - many services
        # - many features

        try:
            os_cfgpath = self.session.query(CfgPath).filter_by(relative_path=os
                    ).join('tld').filter_by(type="os").one()
        except InvalidRequestError, e:
            raise NotFoundException(
                "OS '%s' config path information not found: %s"
                % (os, str(e)))
        os_bi = self.session.query(BuildItem).filter_by(host=dbhost).join(
                'cfg_path').filter_by(tld=os_cfgpath.tld).first()
        if os_bi:
            os_bi.cfg_path = os_cfgpath
        else:
            # FIXME: This could fail if there is already an item at 0
            os_bi = BuildItem(dbhost, os_cfgpath, 0)
        self.session.save_or_update(os_bi)

        try:
            personality = kwargs.get("personality", "ms/fid/spg/ice")
            personality_cfgpath = self.session.query(CfgPath).filter_by(
                    relative_path=personality).join('tld').filter_by(
                    type="personality").one()
        except InvalidRequestError, e:
            raise NotFoundException(
                "Personality '%s' config path information not found: %s"
                % (personality, str(e)))
        personality_bi = self.session.query(BuildItem).filter_by(
                host=dbhost).join('cfg_path').filter_by(
                tld=personality_cfgpath.tld).first()
        if personality_bi:
            personality_bi.cfg_path = personality_cfgpath
        else:
            # FIXME: This could fail if there is already an item at 1
            personality_bi = BuildItem(dbhost, personality_cfgpath, 1)
        self.session.save_or_update(personality_bi)

        # FIXME: auto-configuration of services for the host goes here.

        self.session.flush()
        self.session.refresh(dbhost)
        build_info["dbhost"] = printprep(dbhost)
        # FIXME: Save this to the build table... maybe just carry around
        # the database object...
        build_info["buildid"] = -1
        return True

    @transact
    def verify_aquilon(self, result, build_info, hostname, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        self.session.refresh(dbhost)

        found_os = False
        found_personality = False
        for t in dbhost.templates:
            if t.cfg_path.tld.type == 'os':
                found_os = True
            elif t.cfg_path.tld.type == 'personality':
                found_personality = True
            if found_os and found_personality:
                break
        if not found_os or not found_personality:
            raise ArgumentError("Please run `make aquilon --hostname %s` to give the host an os and personality." % hostname)

        build_info["dbhost"] = printprep(dbhost)
        # FIXME: Save this to the build table... maybe just carry around
        # the database object...
        build_info["buildid"] = -1
        return True

    @transact
    def cancel_make(self, failure, build_info):
        """Gets called as an Errback if the make_aquilon build fails."""
        error = failure.check(RollbackException)
        if not error:
            return failure
        # FIXME: Do the actual work of cancelling the make.
        return Failure(failure.value.cause)

    @transact
    def confirm_make(self, result, build_info):
        """Gets called if the make_aquilon build succeeds."""
        # FIXME: Should finalize the build table...

    # This should probably move over to UserPrincipal
    principal_re = re.compile(r'^(.*)@([^@]+)$')

    # This should be run under a @transact with a session
    def _get_or_create_UserPrincipal(self, user):
        if user is None:
            return user
        m = self.principal_re.match(user)
        if not m:
            raise ArgumentError("Could not parse user principal '%s'" % user)
        realm = m.group(2)
        user = m.group(1)
        dbrealm = self.session.query(Realm).filter_by(name=realm).first()
        if not dbrealm:
            dbrealm = Realm(realm)
            self.session.save(dbrealm)
            dbuser = UserPrincipal(user, realm=dbrealm)
            self.session.save(dbuser)
            return dbuser
        dbuser = self.session.query(UserPrincipal).filter_by(
                name=user.strip().lower(), realm=dbrealm).first()
        if not dbuser:
            dbuser = UserPrincipal(user, dbrealm)
            self.session.save(dbuser)
        return dbuser

    @transact
    def add_domain(self, result, domain, user, **kwargs):
        """Add the domain to the database, initialize as necessary."""
        dbuser = self._get_or_create_UserPrincipal(user)
        if not dbuser:
            raise AuthorizationException("Cannot create a domain without"
                    + " an authenticated connection.")
        # NOTE: Defaulting the name of the quattor server to quattorsrv.
        quattorsrv = self.session.query(QuattorServer).filter_by(
                name='quattorsrv').one()
        # For now, succeed without error if the domain already exists.
        dbdomain = self.session.query(Domain).filter_by(name=domain).first()
        # FIXME: Check that the domain name is composed only of characters
        # that are valid for a directory name.
        if not dbdomain:
            dbdomain = Domain(domain, quattorsrv, dbuser)
            self.session.save_or_update(dbdomain)
        # We just need to confirm that the new domain can be added... do
        # not need anything from the DB to be passed to pbroker.
        return dbdomain.name

    @transact
    def del_domain(self, result, domain, user, **kwargs):
        """Remove the domain from the database."""
        # NOTE: Defaulting the name of the quattor server to quattorsrv.
        quattorsrv = self.session.query(QuattorServer).filter_by(
                name='quattorsrv').one()
        # For now, succeed without error if the domain does not exist.
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            return domain
        if quattorsrv != dbdomain.server:
            log.err("FIXME: Should be redirecting this operation.")
        # FIXME: Entitlements will need to happen at this point.
        if dbdomain:
            self.session.delete(dbdomain)
        # We just need to confirm that domain was removed from the db...
        # do not need anything from the DB to be passed to pbroker.
        return domain

    @transact
    def verify_domain(self, result, domain, **kwargs):
        """This checks both that the domain exists *and* that this is
        the correct server to handle requests for the domain."""
        # NOTE: Defaulting the name of the quattor server to quattorsrv.
        quattorsrv = self.session.query(QuattorServer).filter_by(
                name='quattorsrv').one()
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            raise NotFoundException("Domain '%s' not found." % domain)
        if quattorsrv != dbdomain.server:
            log.err("FIXME: Should be redirecting this operation.")
        return dbdomain.name

    @transact
    def status(self, result, stat, user, **kwargs):
        """Return status information from the database."""
        stat.extend(self.session.query(Domain).all())
        dbuser = self._get_or_create_UserPrincipal(user)
        if dbuser:
            stat.append("Connected as: %s" % dbuser)
        for line in stat:
            printprep(line)

    @transact
    def add_cpu(self, result, name, vendor, speed, **kwargs):
        v = self.session.query(Vendor).filter_by(name=vendor).first()
        if (v is None):
            raise ArgumentError("Vendor '"+vendor+"' not found!")

        c = Cpu (name=name, vendor=v, speed=speed)
        try:
            self.session.save(c)
        except InvalidRequestError, e:
            raise ValueError("Requested operation could not be completed!\n"+ e.__str__())

    @transact
    def add_disk(self, result, machine, type, capacity, **kwargs):
        m = self.session.query(Machine).filter_by(name=machine).first()
        if (m is None):
            raise ArgumentError('Unknown machine name')
        dt = self.session.query(DiskType).filter_by(type=type).one()
        if (dt is None):
            raise ArgumentError('Unknown disk type')

        d = Disk(machine=m,type=dt,capacity=capacity)
        try:
            self.session.save(d)
        except InvalidRequestError, e:
            raise ValueError("Requested operation could not be completed!\n"+ e.__str__())
        # Hack to make sure machine is accessible...
        printprep(d.machine)
        return d

    @transact
    def add_model(self, result, name, vendor, type, **kw):
        m = self.session.query(Model).filter_by(name=name).first()
        if (m is not None):
            raise ArgumentError('Specified model already exists')
        v = self.session.query(Vendor).filter_by(name = vendor).first()
        if (v is None):
            raise ArgumentError("Vendor '"+vendor+"' not found!")

        m = self.session.query(MachineType).filter_by(type=type).first()
        if (m is None):
            raise ArgumentError("Machine type '"+type+"' not found!")

        model = Model(name, v, m)
        self.session.save(model)

        if (kw.has_key('cputype') and kw['cputype'] is not None):
            ms = MachineSpecs(
                model=model,
                cpu=kw['cputype'],
                cpu_quantity=kw['cpunum'],
                memory=kw['mem'],
                disk_type=kw['disktype'],
                disk_capacity=kw['disksize'],
                nic_count=kw['nics']
            )
            self.session.save(ms)
        return "New model successfully created"

    @transact
    def show_model(self, result, **kwargs):
        q = self.session.query(Model)
        if (kwargs['name'] is not None):
            q = q.filter(Model.name.like(kwargs['name']+'%'))
        if (kwargs['vendor'] is not None):
            q = q.join('vendor').filter(Vendor.name.like(kwargs['vendor']+'%')).reset_joinpoint()
        if (kwargs['type'] is not None):
            q = q.join('machine_type').filter(MachineType.type.like(kwargs['type']+'%'))
        return printprep(q.all())

    @transact
    def del_model(self, result, name, vendor, hardware, **kwargs):
        v = self.session.query(Vendor).filter_by(name = vendor).first()
        if (v is None):
            raise ArgumentError("Vendor '"+vendor+"' not found!")

        h = self.session.query(HardwareType).filter_by(type = hardware).first()
        if (h is None):
            raise ArgumentError("Hardware type '"+hardware+"' not found!")

        m = self.session.query(Model).filter_by(name = name, vendor = v, hardware_type = h).first()
        if (m is None):
            raise ArgumentError('Requested model was not found in the database')

        try:
            self.session.delete(m)
        except InvalidRequestError, e:
            raise ValueError("Requested operation could not be completed!\n"+ e.__str__())
        return "Model successfully deleted"

    # FIXME: This utility method may be better suited elsewhere.
    def force_int(self, label, value):
        if value is None:
            return None
        try:
            result = int(value)
        except Exception, e:
            raise ArgumentError("Expected an integer for %s: %s" % (label, e))
        return result

    @transact
    def add_machine(self, result, machine, location, type, model,
            cpuname, cpuvendor, cpuspeed, cpucount, memory, serial,
            **kwargs):
        if (type not in ['chassis', 'rack', 'desk']):
            raise ArgumentError ('Invalid location type: '+type)
        if (type == 'chassis'):
            loc = self.session.query(Chassis).filter_by(name = location).first()
        elif (type == 'rack'):
            loc = self.session.query(Rack).filter_by(name = location).first()
        else:
            loc = self.session.query(Desk).filter_by(name = location).first()
        if (loc is None):
            raise ArgumentError("Location name '"+location+"' not found!")

        cpuspeed = self.force_int("cpuspeed", cpuspeed)
        cpucount = self.force_int("cpucount", cpucount)
        memory = self.force_int("memory", memory)

        mod = self.session.query(Model).filter_by(name = model).first()
        if (mod is None):
            raise ArgumentError("Model name '"+model+"' not found!");

        try:
            # If cpu.name format changes (currently name_speed), may need
            # to revisit this.
            cpu = self.session.query(Cpu).filter(
                    Cpu.name.like(cpuname.lower() + '%')).filter_by(
                    speed=cpuspeed).join('vendor').filter_by(
                    name=cpuvendor.lower()).one()
        except InvalidRequestError, e:
            raise NotFoundException("Could not find cpu with name like '%s%%', speed='%d', and vendor='%s': %s"
                    % (cpuname, cpuspeed, cpuvendor, e))

        try:
            # FIXME: These should have been optional.  Only override as needed.
            optional = {"cpu":cpu, "cpu_quantity":cpucount, "memory":memory}
            if serial:
                optional["serial_no"] = serial
            m = Machine(loc, mod, name=machine, **optional)
            self.session.save(m)
        except InvalidRequestError, e:
            raise ValueError("Requested machine could not be created!\n"+e.__str__())
        return printprep(m)

    @transact
    def show_machine(self, result, **kwargs):
        try:
            q = self.session.query(Machine)
            if (kwargs['machine'] is not None):
                q = q.filter(Machine.name.like(kwargs['machine']+'%'))
            if (kwargs['location'] is not None and 
                kwargs['type'] is not None):
                if (kwargs['type'] not in ['chassis', 'rack', 'desk']):
                    raise ArgumentError ('Invalid location type')
                q = q.join('location').filter(Location.name.like(kwargs['location']+'%'))
                q = q.filter(LocationType.type == kwargs['type'])
                q = q.reset_joinpoint()
            if (kwargs['model'] is not None):
                q = q.join('model').filter(Model.name.like(kwargs['model']+'%'))
            return printprep(q.all())
        except InvalidRequestError, e:
            raise ValueError("Error while querying the database!\n"+e.__str__())

    @transact
    def verify_machine(self, result, machine, **kwargs):
        dbmachine = self._get_machine(machine)
        return printprep(dbmachine)

    @transact
    def del_machine(self, result, machine, **kwargs):
        try:
            m = self.session.query(Machine).filter_by(name=machine).one()
            for iface in m.interfaces:
                log.msg("Before deleting machine '%s', removing interface '%s' [%s] [%s] boot=%s)" % (m.name, iface.name, iface.mac, iface.ip, iface.boot))
                self.session.delete(iface)
            for disk in m.disks:
                log.msg("Before deleting machine '%s', removing disk '%s'" % (m.name, disk))
                self.session.delete(disk)
            self.session.delete(m)
        except InvalidRequestError, e:
            raise ValueError("Requested machine could not be deleted!\n"+e.__str__())
        return "Successfull deletion"

    @transact
    def add_interface(self, result, **kwargs):
        if (kwargs['interface'] is None):
            raise ArgumentError ('Interface name is not set!')
        if (kwargs['mac'] is None):
            raise ArgumentError('MAC address not set!')
        if (kwargs['machine'] is None):
            raise ArgumentError('Machine name isnot set!')
        ip_addr = (kwargs['ip'] is None) and '' or kwargs['ip']
        m = self.session.query(Machine).filter_by(name = kwargs['machine']).one()
        extra = {}
        if kwargs['interface'] == 'eth0':
            extra["boot"] = True
        i = PhysicalInterface(kwargs['interface'], kwargs['mac'], m, ip=ip_addr,
                **extra)
        self.session.save(i)
        # Hack to make sure machine is accessible...
        printprep(i.machine)
        return printprep(i)

    # Expects to run under a transact with a session.
    def _find_interface(self, interface, machine, mac, ip):
        q = self.session.query(PhysicalInterface)
        if interface:
            q = q.filter_by(name=interface)
        if machine:
            q = q.join('machine').filter_by(name=machine)
            q = q.reset_joinpoint()
        if mac:
            q = q.filter_by(mac=mac)
        if ip:
            q = q.filter_by(ip=ip)
        try:
            dbinterface = q.one()
        except InvalidRequestError, e:
            raise ArgumentError("Could not locate the interface, make sure it has been specified uniquely: " + str(e))
        return dbinterface

    @transact
    def del_interface(self, result, interface, machine, mac, ip, **kwargs):
        dbinterface = self._find_interface(interface, machine, mac, ip)
        dbmachine = dbinterface.machine
        if dbmachine.host and dbinterface.boot:
            raise ArgumentError("Cannot remove the bootable interface from a host.  Use `aq del host --hostname %s` first." % dbmachine.host.fqdn)
        self.session.delete(dbinterface)
        self.session.flush()
        self.session.refresh(dbmachine)
        return printprep(dbmachine)

    @transact
    def manage(self, result, domain, hostname, user, **kwargs):
        try:
            dbdomain = self.session.query(Domain).filter_by(name=domain).one()
        except InvalidRequestError:
            raise NotFoundException("Domain '%s' not found." % domain)
        dbhost = self._hostname_to_host(hostname)
        dbhost.domain = dbdomain
        self.session.save_or_update(dbhost)
        return

    @transact
    def add_service(self, result, service, instance, **kwargs):
        dbservice = self.session.query(Service).filter_by(name=service).first()
        if not dbservice:
            dbservice = Service(service)
            self.session.save(dbservice)
        if not instance:
            return printprep(dbservice)
        # FIXME: Treatment of instance is over-simplified, and needs to be
        # revisited.
        relative_path = "%s/%s/client" % (service, instance)
        dbinstance = self.session.query(CfgPath).filter_by(
                relative_path=relative_path,
                tld=dbservice.cfg_path.tld).first()
        if not dbinstance:
            dbinstance = CfgPath(dbservice.cfg_path.tld,
                    'service/' + relative_path)
            self.session.save(dbinstance)
            self.session.flush()
            self.session.refresh(dbservice)
        return printprep(dbservice)

    @transact
    def show_service(self, result, service, **kwargs):
        q = self.session.query(Service)
        if not service:
            return printprep(q.all())
        try:
            dbservice = q.filter_by(name=service).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service '%s' not found: %s" % (service, e))
        # FIXME: Treatment of instance is over-simplified, and needs to be
        # revisited.  This hack treats CfgPath as a ServiceInstance and shows
        # them after showing the service.
        q = self.session.query(CfgPath).filter(
                CfgPath.tld==dbservice.cfg_path.tld).filter(
                CfgPath.relative_path.like(service + "/%"))
        instances = q.all()
        instances.insert(0, dbservice)
        return printprep(instances)

    @transact
    def del_service(self, result, service, instance, **kwargs):
        dbservice = self._get_service(service)
        if not instance:
            self.session.delete(dbservice)
            return "Success"
        # FIXME: Treatment of instance is over-simplified, and needs to be
        # revisited.  For delete, this may be just plain wrong.
        relative_path = "%s/%s/client" % (service, instance)
        try:
            dbinstance = self.session.query(CfgPath).filter_by(
                    relative_path=relative_path,
                    tld=dbservice.cfg_path.tld).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service instance '%s/%s' not found: %s"
                    % (service, instance, e))
        self.session.delete(dbinstance)
        return "Success"

    @transact
    def bind_service(self, result, hostname, service, instance, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        dbservice = self._get_service(service)
        # FIXME: Treatment of instance is over-simplified, and needs to be
        # revisited.
        relative_path = "%s/%s/client" % (service, instance)
        try:
            dbinstance = self.session.query(CfgPath).filter_by(
                    relative_path=relative_path,
                    tld=dbservice.cfg_path.tld).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service instance '%s/%s' not found: %s"
                    % (service, instance, e))
        positions = []
        self.session.refresh(dbhost)
        for template in dbhost.templates:
            positions.append(template.position)
            if template.cfg_path == dbinstance:
                return printprep(dbhost)
        # Do not bind to 0 (os) or 1 (personality)
        i = 2
        while i in positions:
            i += 1
        bi = BuildItem(dbhost, dbinstance, i)
        self.session.save(bi)
        self.session.flush()
        self.session.refresh(dbhost)
        return printprep(dbhost)

    @transact
    def unbind_service(self, result, hostname, service, instance, **kwargs):
        dbhost = self._hostname_to_host(hostname)
        dbservice = self._get_service(service)
        # FIXME: Treatment of instance is over-simplified, and needs to be
        # revisited.
        relative_path = "%s/%s/client" % (service, instance)
        try:
            dbinstance = self.session.query(CfgPath).filter_by(
                    relative_path=relative_path,
                    tld=dbservice.cfg_path.tld).one()
        except InvalidRequestError, e:
            raise NotFoundException("Service instance '%s/%s' not found: %s"
                    % (service, instance, e))
        bi = self.session.query(BuildItem).filter_by(host=dbhost,
                cfg_path=dbinstance).first()
        if bi:
            self.session.delete(bi)
            self.session.flush()
            self.session.refresh(dbhost)
        return printprep(dbhost)

    # Expects to be run under a @transact method with session=True.
    def _hostname_to_domain_and_string(self, hostname):
        if not hostname:
            raise ArgumentError("No hostname specified.")
        (short, dot, dns_domain) = hostname.partition(".")
        if not dns_domain:
            raise ArgumentError(
                    "'%s' invalid, hostname must be fully qualified."
                    % hostname)
        if not short:
            raise ArgumentError( "'%s' invalid, missing host name." % hostname)
        try:
            dbdns_domain = self.session.query(DnsDomain).filter_by(
                    name=dns_domain).one()
        except InvalidRequestError, e:
            raise NotFoundException("DNS domain '%s' for '%s' not found: %s"
                    % (dns_domain, hostname, e))
        return (short, dbdns_domain)

    # Expects to be run under a @transact method with session=True.
    def _hostname_to_host(self, hostname):
        (short, dbdns_domain) = self._hostname_to_domain_and_string(hostname)
        try:
            host = self.session.query(Host).filter_by(
                    name=short, dns_domain=dbdns_domain).one()
        except InvalidRequestError, e:
            raise NotFoundException("Host '%s' not found." % hostname)
        return host

