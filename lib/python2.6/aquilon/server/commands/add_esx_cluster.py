# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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


from aquilon.server.broker import (BrokerCommand, validate_basic,
                                   force_int, force_ratio)
from aquilon.aqdb.model import (Cluster, EsxCluster, MetaCluster,
                                MetaClusterMember, Domain, Personality)
from aquilon.exceptions_ import ArgumentError
from aquilon.server.dbwrappers.branch import get_branch_and_author
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.dbwrappers.tor_switch import get_tor_switch


class CommandAddESXCluster(BrokerCommand):

    required_parameters = ["cluster", "metacluster"]

    def render(self, session, logger, cluster, metacluster, archetype,
               personality, max_members, vm_to_host_ratio, domain, sandbox,
               tor_switch, down_hosts_threshold, comments, **arguments):
        validate_basic("cluster", cluster)
        cluster_type = 'esx'

        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        dblocation = get_location(session, **arguments)
        if not dblocation:
            raise ArgumentError("Adding a cluster requires a location "
                                "constraint.")
        if not dblocation.campus:
            raise ArgumentError("%s %s is not within a campus." %
                                (dblocation.location_type.capitalize(),
                                 dblocation.name))

        Cluster.get_unique(session, cluster, preclude=True)

        dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)

        if not max_members:
            max_members = self.config.get("broker",
                                          "esx_cluster_max_members_default")
        max_members = force_int("max_members", max_members)

        if vm_to_host_ratio is None:
            vm_to_host_ratio = self.config.get("broker",
                                               "esx_cluster_vm_to_host_ratio")
        (vm_count, host_count) = force_ratio("vm_to_host_ratio",
                                             vm_to_host_ratio)
        down_hosts_threshold = force_int("down_hosts_threshold",
                                         down_hosts_threshold)

        if tor_switch:
            dbtor_switch = get_tor_switch(session, tor_switch)
        else:
            dbtor_switch = None

        dbcluster = EsxCluster(name=cluster,
                               location_constraint=dblocation,
                               personality=dbpersonality,
                               max_hosts=max_members,
                               vm_count=vm_count, host_count=host_count,
                               branch=dbbranch, sandbox_author=dbauthor,
                               switch=dbtor_switch,
                               down_hosts_threshold=down_hosts_threshold,
                               comments=comments)
        session.add(dbcluster)

        try:
            # AQDB checks the max_members attribute.
            dbmcm = MetaClusterMember(metacluster=dbmetacluster,
                                      cluster=dbcluster)
            session.add(dbmcm)
        except ValueError, e:
            raise ArgumentError(e.message)

        session.flush()
        session.refresh(dbcluster)

        plenary = PlenaryCluster(dbcluster, logger=logger)
        plenary.write()

        return
