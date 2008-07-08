#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add host`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.domain import verify_domain
from aquilon.server.dbwrappers.status import get_status
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.server.dbwrappers.host import hostname_to_domain_and_string
from aquilon.aqdb.systems import Host
from aquilon.server.templates import PlenaryMachineInfo


class CommandAddHost(BrokerCommand):

    required_parameters = ["hostname", "machine", "archetype", "domain",
            "status"]

    @add_transaction
    @az_check
    def render(self, session, hostname, machine, archetype, domain, status,
            user, **arguments):
        dbdomain = verify_domain(session, domain,
                self.config.get("broker", "servername"))
        dbstatus = get_status(session, status)
        dbmachine = get_machine(session, machine)
        dbarchetype = get_archetype(session, archetype)

        if dbmachine.type() not in ('blade', 'workstation', 'rackmount'):
            raise ArgumentError("Machine is of type %s, and must be a blade, workstation, or rackmount to add a host." %
                    (dbmachine.type()))

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
        (short, dbdns_domain) = hostname_to_domain_and_string(session, hostname)
        # Archetype must be a plain string...
        dbhost = Host(dbmachine, dbdomain, dbstatus, name=short,
                dns_domain=dbdns_domain, archetype=archetype)
        session.save(dbhost)
        session.flush()
        # Working around funky archetype handling in host creation...
        # Might not be necessary if/when Host uses the declarative mapper.
        session.refresh(dbhost)

        # FIXME: Call out to dsdb.  Use code in processes.py.

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return


#if __name__=='__main__':
