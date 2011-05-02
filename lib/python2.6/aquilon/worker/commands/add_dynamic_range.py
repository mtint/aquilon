# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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

from ipaddr import IPv4Address

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import (DynamicStub, ARecord, DnsDomain, Fqdn,
                                NetworkEnvironment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.dbwrappers.interface import check_ip_restrictions
from aquilon.server.processes import DSDBRunner


class CommandAddDynamicRange(BrokerCommand):

    required_parameters = ["startip", "endip", "dns_domain"]

    def render(self, session, logger, startip, endip, dns_domain, prefix,
               **arguments):
        if not prefix:
            prefix = 'dynamic'
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)
        startnet = get_net_id_from_ip(session, startip, dbnet_env)
        endnet = get_net_id_from_ip(session, endip, dbnet_env)
        if startnet != endnet:
            raise ArgumentError("IP addresses %s (%s) and %s (%s) must be on "
                                "the same subnet." %
                                (startip, startnet.ip, endip, endnet.ip))
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)
        q = session.query(ARecord)
        q = q.filter_by(network=startnet)
        q = q.filter(ARecord.ip >= startip)
        q = q.filter(ARecord.ip <= endip)
        q = q.order_by(ARecord.ip)
        conflicts = q.all()
        if conflicts:
            raise ArgumentError("Cannot allocate IP address range because the "
                                "following hosts already exist:\n" +
                                "\n".join([format(c, "a") for c in conflicts]))

        stubs = []
        for ipint in range(int(startip), int(endip) + 1):
            ip = IPv4Address(ipint)
            check_ip_restrictions(startnet, ip)
            name = "%s-%s" % (prefix, str(ip).replace('.', '-'))
            dbfqdn = Fqdn.get_or_create(session, name=name,
                                        dns_domain=dbdns_domain, preclude=True)
            dbdynamic_stub = DynamicStub(fqdn=dbfqdn, ip=ip, network=startnet)
            session.add(dbdynamic_stub)
            stubs.append(dbdynamic_stub)

        if not stubs:
            return

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        stubs_added = []
        try:
            for dbstub in stubs:
                logger.client_info("Adding {0:a} to DSDB.".format(dbstub))
                dsdb_runner.add_host_details(fqdn=dbstub.fqdn, ip=dbstub.ip,
                                             name=None, mac=None)
                stubs_added.append(dbstub)
        except ProcessException, err:
            # Try to roll back anything that had succeeded...
            for dbstub in stubs_added:
                try:
                    dsdb_runner.delete_host_details(dbstub.ip)
                except ProcessException, pe2:
                    logger.client_info("Failed rolling back DSDB entry for "
                                       "%s with IP address %s: %s" %
                                       (dbstub.fqdn, dbstub.ip, pe2))
            raise ArgumentError("Could not add addresses to DSDB: %s" % err)
        return