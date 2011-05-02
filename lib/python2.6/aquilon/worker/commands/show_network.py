# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq show network`."""

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Interface, Network, NetworkEnvironment
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.server.formats.network import SimpleNetworkList
from aquilon.server.formats.network import NetworkHostList


class CommandShowNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, ip, network_environment, all, discovered,
               discoverable, style, type=False, hosts=False, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dbnetwork = network and get_network_byname(session, network, dbnet_env) or None
        dbnetwork = ip and get_network_byip(session, ip, dbnet_env) or dbnetwork
        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.options(joinedload('location'))
        if dbnetwork:
            if hosts:
                return NetworkHostList([dbnetwork])
            else:
                return dbnetwork
        if type:
            q = q.filter_by(network_type = type)
        if discoverable is not None:
            q = q.filter_by(is_discoverable = discoverable)
        if discovered is not None:
            q = q.filter_by(is_discovered = discovered)
        dblocation = get_location(session, **arguments)
        if dblocation:
            childids = dblocation.offspring_ids()
            q = q.filter(Network.location_id.in_(childids))
        q = q.order_by(Network.ip)
        if hosts or style == "proto":
            q = q.options(subqueryload("assignments"))
            q = q.options(joinedload("assignments.dns_records"))
        if hosts:
            return NetworkHostList(q.all())
        else:
            return SimpleNetworkList(q.all())