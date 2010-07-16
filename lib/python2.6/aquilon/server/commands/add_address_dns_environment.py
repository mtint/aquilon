# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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

from aquilon.exceptions_ import UnimplementedError
from aquilon.aqdb.model import System, FutureARecord
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.interface import restrict_tor_offsets
from aquilon.server.dbwrappers.system import parse_system
from aquilon.server.processes import DSDBRunner


class CommandAddAddressDNSEnvironment(BrokerCommand):

    required_parameters = ["fqdn", "ip", "dns_environment"]

    def render(self, session, logger, fqdn, ip, dns_environment, comments,
               **arguments):
        default = self.config.get("broker", "default_dns_environment")
        if str(dns_environment).strip().lower() != default.strip().lower():
            raise UnimplementedError("Only the '%s' DNS environment is "
                                     "currently supported." % default)

        (short, dbdns_domain) = parse_system(session, fqdn)
        System.get_unique(session, name=short, dns_domain=dbdns_domain,
                          preclude=True)

        ipnet = get_net_id_from_ip(session, ip)
        restrict_tor_offsets(ipnet, ip)
        dbaddress = FutureARecord(name=short, dns_domain=dbdns_domain,
                                  ip=ip, network=ipnet, comments=comments)
        session.add(dbaddress)

        session.flush()

        dsdb_runner = DSDBRunner(logger=logger)
        dsdb_runner.add_host_details(fqdn=dbaddress.fqdn, ip=dbaddress.ip,
                                     name=None, mac=None)
        return