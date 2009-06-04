# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq add interface --machine`."""


from twisted.python import log
from sqlalchemy import String
from sqlalchemy.sql.expression import asc, desc, bindparam

from aquilon.exceptions_ import (ArgumentError, ProcessException,
                                 IncompleteError, UnimplementedError)
from aquilon.aqdb.model import Interface, Machine, Manager
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.interface import describe_interface
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.processes import DSDBRunner


class CommandAddInterfaceMachine(BrokerCommand):

    required_parameters = ["interface", "machine"]

    def render(self, session, interface, machine, mac, automac, comments,
               **arguments):
        dbmachine = get_machine(session, machine)
        extra = {}
        if interface == 'eth0':
            extra['bootable'] = True
        if comments:
            extra['comments'] = comments

        prev = session.query(Interface).filter_by(
                name=interface,hardware_entity=dbmachine).first()
        if prev:
            raise ArgumentError("machine %s already has an interface named %s"
                    % (machine, interface))

        itype = 'public'
        management_types = ['bmc', 'ilo', 'ipmi']
        for mtype in management_types:
            if interface.startswith(mtype):
                itype = 'management'
                break

        dbmanager = None
        pending_removals = []
        if mac:
            prev = session.query(Interface).filter_by(mac=mac).first()
            if prev and prev.hardware_entity == dbmachine:
                raise ArgumentError("machine %s already has an interface "
                                    "with mac %s" % (dbmachine.name, mac))
            # Is the conflicting interface something that can be
            # removed?  It is if:
            # - we are currently attempting to add a management interface
            # - the old interface belongs to a machine
            # - the old interface is associated with a host
            # - that host was blindly created, and thus can be removed safely
            if prev and itype == 'management' and \
               prev.hardware_entity.hardware_entity_type == 'machine' and \
               prev.system and prev.system.system_type == 'host' and \
               prev.system.status.name == 'blind':
                # FIXME: Is this just always allowed?  Maybe restrict
                # to only aqd-admin and the host itself?
                dummy_machine = prev.hardware_entity
                dummy_ip = prev.system.ip
                old_network = prev.system.network
                self.remove_prev(session, prev, pending_removals)
                session.flush()
                self.remove_dsdb(dummy_ip)
                self.consolidate_names(session, dbmachine, dummy_machine.name,
                                       pending_removals)
                # It seems like a shame to throw away the IP address that
                # had been allocated for the blind host.  Try to use it
                # as it should be used...
                dbmanager = self.add_manager(session, dbmachine, dummy_ip,
                                             old_network)
            elif prev:
                msg = describe_interface(session, prev)
                raise ArgumentError("Mac '%s' already in use: %s" % (mac, msg))
        elif automac:
            mac = self.generate_mac(session, dbmachine)
        else:
            raise ArgumentError("Interface requires a MAC address.")

        dbinterface = Interface(name=interface, hardware_entity=dbmachine,
                                mac=mac, interface_type=itype, **extra)
        # So far, we're *only* creating a manager if we happen to be
        # removing a blind entry and we can steal its IP address.
        if dbmanager:
            dbinterface.system = dbmanager
            dbmanager.mac = dbinterface.mac
            session.add(dbmanager)
        session.add(dbinterface)
        session.flush()
        session.refresh(dbinterface)
        session.refresh(dbmachine)

        if dbmanager:
            dsdb_runner = DSDBRunner()
            try:
                dsdb_runner.add_host(dbinterface)
            except ProcessException, e:
                log.msg("Could not reserve IP %s for %s in dsdb: %s" %
                        (dbmanager.ip, dbmanager.fqdn, e))
                dbinterface.system = None
                session.add(dbinterface)
                session.remove(dbmanager)
                session.flush()
                session.refresh(dbinterface)
                session.refresh(dbmachine)

        try:
            compileLock()
            plenary_info = PlenaryMachineInfo(dbmachine)
            plenary_info.write(locked=True)

            for old_plenary_info in pending_removals:
                old_plenary_info.remove(locked=True)
                plenary_info.remove(locked=True)
            if pending_removals and dbmachine.host:
                # Not an exact test, but the file won't be re-written
                # if the contents are the same so calling too often is
                # not a major expense.
                try:
                    plenary_info = PlenaryHost(dbmachine.host)
                    plenary_info.write(locked=True)
                except IncompleteError, e:
                    pass
        finally:
            compileRelease()

        if dbmachine.host:
            # FIXME: reconfigure host
            pass

        return

    def remove_prev(self, session, prev, pending_removals):
        """Remove the interface 'prev' and its host and machine."""
        # This should probably be re-factored to call code used elsewhere.
        # The below seems too simple to warrant that, though...
        log.msg("Removing blind host '%s', machine '%s', and interface '%s'" %
                (prev.system.fqdn, prev.hardware_entity.name, prev.name))
        host_plenary_info = PlenaryHost(prev.system)
        # FIXME: Should really do everything that del_host.py does, not
        # just remove the host plenary but adjust all the service
        # plenarys and dependency files.
        pending_removals.append(host_plenary_info)
        session.delete(prev.system)
        dbmachine = prev.hardware_entity
        machine_plenary_info = PlenaryMachineInfo(prev.hardware_entity)
        pending_removals.append(machine_plenary_info)
        for disk in dbmachine.disks:
            session.delete(disk)
        session.delete(prev)
        session.delete(dbmachine)
        session.flush()

    def remove_dsdb(self, old_ip):
        # If this is a host trying to update itself, this would be annoying.
        # Hopefully whatever the problem is here, it's transient.
        try:
            dsdb_runner = DSDBRunner()
            dsdb_runner.delete_host_details(old_ip)
        except ProcessException, e:
            raise ArgumentError("Could not remove host entry with ip %s from dsdb: %s" %
                                (old_ip, e))

    def consolidate_names(self, session, dbmachine, dummy_machine_name,
                          pending_removals):
        short = dbmachine.name[:-1]
        if short != dummy_machine_name[:-1]:
            log.msg("Not altering name of machine '%s', name of machine being removed '%s' is too different" %
                    (dbmachine.name, dummy_machine_name))
            return
        if not dbmachine.name[-1].isalpha():
            log.msg("Not altering name of machine '%s', name does not end with a letter." %
                    dbmachine.name)
            return
        if session.query(Machine).filter_by(name=short).first():
            log.msg("Not altering name of machine '%s', target name '%s' is already in use" %
                    (dbmachine.name, short))
            return
        log.msg("Renaming machine '%s' as '%s'" % (dbmachine.name, short))
        pending_removals.append(PlenaryMachineInfo(dbmachine))
        dbmachine.name = short
        session.add(dbmachine)
        session.flush()

    def add_manager(self, session, dbmachine, old_ip, old_network):
        if not old_ip:
            log.msg("No IP available for system being removed, not auto-creating manager for %s" %
                    dbmachine.name)
            return
        if not dbmachine.host:
            log.msg("Machine %s is not linked to a host, not auto-creating manager for %s with IP %s" %
                    (dbmachine.name, old_ip))
            return
        dbhost = dbmachine.host
        manager = "%sr.%s" % (dbhost.name, dbhost.dns_domain.name)
        try:
            (short, dbdns_domain) = parse_system_and_verify_free(session,
                                                                 manager)
        except ArgumentError, e:
            log.msg("Could not create manager with name %s and ip %s for machine %s: %s" %
                    (manager, old_ip, dbmachine.name, e))
            return
        dbmanager = Manager(name=short, dns_domain=dbdns_domain,
                            machine=dbmachine,
                            ip=old_ip, network=old_network)
        return dbmanager

    def generate_mac(self, session, dbmachine):
        """ Generate a mac address for virtual hardware.

        Algorithm:

        * Query for first mac address in aqdb starting with vendor prefix,
          order by mac descending.
        * If no address, or address less than prefix start, use prefix start.
        * If the found address is not suffix end, increment by one and use it.
        * If the address is suffix end, requery for the full list and scan
          through for holes. Use the first hole.
        * If no holes, error. [In this case, we're still not completely dead
          in the water - the mac address would just need to be given manually.]

        """
        if dbmachine.model.machine_type != "virtual_machine":
            raise ArgumentError("Can only automatically generate mac "
                                "addresses for virtual hardware.")
        if not dbmachine.cluster or dbmachine.cluster.cluster_type != 'esx':
            raise UnimplementedError("MAC auto-generation has only been "
                                     "enabled for ESX clusters.")
        # FIXME: These values should probably be configurable.
        mac_prefix_esx = "00:50:56"
        mac_start_esx = "01:00:00"
        mac_end_esx = "3f:ff:ff"
        mac_prefix = mac_prefix_esx
        mac_start = MACAddress(mac_prefix + ":" + mac_start_esx)
        mac_end = MACAddress(mac_prefix + ":" + mac_end_esx)
        q = session.query(Interface.mac)
        # Need to explicitly bypass AqMac conversion here so that we
        # do not get an error about the prefix being an invalid mac.
        # This implies that the prefix must already be lower cased
        # and include colons.
        q = q.filter(Interface.mac.startswith(bindparam('prefix',
                                                        type_=String)))
        q = q.params(prefix=mac_prefix_esx)
        # This query (with a different order_by) is used below.
        mac = q.order_by(desc(Interface.mac)).first()
        if not mac:
            return mac_start.get_address()
        highest_mac = MACAddress(mac[0])
        if highest_mac < mac_start:
            return mac_start.get_address()
        if highest_mac < mac_end:
            return highest_mac.next().get_address()
        potential_hole = mac_start
        for mac in q.order_by(asc(Interface.mac)).all():
            current_mac = MACAddress(mac[0])
            if current_mac < mac_start:
                continue
            if potential_hole < current_mac:
                return potential_hole.get_address()
            potential_hole = current_mac.next()
        raise ArgumentError("All MAC addresses between %s and %s inclusive "
                            "are currently in use." % (mac_start, mac_end))


class MACAddress(object):
    def __init__(self, address=None, value=None):
        if address is not None:
            if value is None:
                value = long(address.replace(':', ''), 16)
        elif value is None:
            raise ValueError("Must specify either address or value")
        self.address = address
        self.value = value

    def __cmp__(self, other):
        return cmp(self.value, other.value)

    def next(self):
        next_value = self.value + 1
        return MACAddress(value=next_value)

    def get_address(self):
        """Address is created as needed."""
        if not self.address:
            self.address = "%012x" % self.value
        return self.address

    def __str__(self):
        a = self.get_address()
        if a.find(':'):
            return a
        # This is almost perl-esque, ain't it?  Basically, stich a colon
        # in between every two characters of the address.
        return ":".join(["".join(t) for t in
                         zip(a[0:len(a):2], a[1:len(a):2])])


