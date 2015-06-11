#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the vulcan2 related commands."""

import os
from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin
from machinetest import MachineTestMixin
from personalitytest import PersonalityTestMixin


class TestVulcan20(VerifyNotificationsMixin, MachineTestMixin,
                   PersonalityTestMixin, TestBrokerCommand):
    # Metacluster / cluster / Switch tests

    def test_000_add_personalities(self):
        vmhost_maps = {
            "esx_management_server": {
                "ut.a": {
                    "building": ["ut"],
                },
            },
            "vcenter": {
                "ut": {
                    "building": ["ut"],
                },
            },
        }
        esx_cluster_maps = {
            "esx_management_server": {
                "ut.a": {
                    "building": ["ut"],
                },
            },
        }

        # We can't set up the vcenter bindings/maps here, because the first
        # batch of tests do not work with it. Sigh.
        self.create_personality("vmhost", "vulcan2-server-dev",
                                grn="grn:/ms/ei/aquilon/aqd",
                                required=["esx_management_server"],
                                maps=vmhost_maps)
        self.create_personality("esx_cluster", "vulcan2-server-dev",
                                grn="grn:/ms/ei/aquilon/aqd",
                                maps=esx_cluster_maps)
        self.create_personality("metacluster", "vulcan2")

    def test_010_addutmc8(self):
        command = ["add_metacluster", "--metacluster=utmc8",
                   "--personality=vulcan2", "--archetype=metacluster",
                   "--domain=unittest", "--building=ut",
                   "--comments=autopg_v2_tests"]
        self.noouttest(command)

    def add_utcluster(self, name, metacluster):
        command = ["add_esx_cluster", "--cluster=%s" % name,
                   "--metacluster=%s" % metacluster, "--room=utroom1",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan2-server-dev"]
        self.noouttest(command)

    # see testaddutmc4
    def test_020_addutpgcl(self):
        for i in range(0, 2):
            self.add_utcluster("utpgcl%d" % i, "utmc8")

    # for each cluster's hosts
    def test_060_add10gigracks(self):
        for i in range(0, 2):
            machine = "utpgs01p%d" % i
            self.create_machine(machine, "vb1205xm", rack="ut3",
                                eth0_mac=self.net["autopg2"].usable[i].mac)

    def test_070_populate10gigrackhosts(self):
        for i in range(0, 2):
            ip = self.net["autopg2"].usable[i]
            hostname = "utpgh%d.aqd-unittest.ms.com" % i
            machine = "utpgs01p%d" % i

            self.dsdb_expect_add(hostname, ip, "eth0", ip.mac)
            command = ["add", "host", "--hostname", hostname, "--ip", ip,
                       "--machine", machine,
                       "--domain", "unittest", "--buildstatus", "build",
                       "--osname", "esxi", "--osversion", "5.0.0",
                       "--archetype", "vmhost", "--personality", "vulcan2-server-dev"]
            self.noouttest(command)
        self.dsdb_verify()

    def test_080_makeclusters(self):
        for i in range(0, 2):

            host = "utpgh%s.aqd-unittest.ms.com" % i
            cluster = "utpgcl%d" % i
            self.statustest(["make", "cluster", "--cluster", cluster])

            self.statustest(["cluster",
                             "--hostname", host, "--cluster", cluster])

    def test_090_addmachines(self):
        for i in range(0, 3):
            cluster = "utpgcl%d" % (i // 2)
            machine = "utpgm%d" % i

            self.noouttest(["add", "machine", "--machine", machine,
                            "--cluster", cluster, "--model", "utmedium"])

    def test_095_search_host_by_metacluster(self):
        command = "search host --cluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utpgh0.aqd-unittest.ms.com", command)
        self.matchoutput(out, "utpgh1.aqd-unittest.ms.com", command)

    def test_097_search_machine_by_metacluster(self):
        command = "search machine --cluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utpgm0", command)
        self.matchoutput(out, "utpgm1", command)
        self.matchoutput(out, "utpgm2", command)
        self.matchclean(out, "utpgs01p0", command)

    # switch tests
    def test_100_addswitch(self):
        self.noouttest(["update_metacluster", "--metacluster", "utmc8",
                        "--virtual_switch", "utvswitch"])

    def test_105_cat_utmc8(self):
        command = ["cat", "--metacluster", "utmc8", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/metacluster/virtual_switch" = "utvswitch";',
                         command)

    def test_105_show_utmc8_proto(self):
        net = self.net["autopg1"]
        command = ["show_metacluster", "--metacluster", "utmc8",
                   "--format", "proto"]
        mc = self.protobuftest(command, expect=1)[0]
        self.assertEqual(mc.name, "utmc8")
        self.assertEqual(mc.virtual_switch.name, "utvswitch")
        self.assertEqual(len(mc.virtual_switch.portgroups), 1)
        self.assertEqual(mc.virtual_switch.portgroups[0].ip, str(net.ip))
        self.assertEqual(mc.virtual_switch.portgroups[0].cidr, 29)
        self.assertEqual(mc.virtual_switch.portgroups[0].network_tag, 710)
        self.assertEqual(mc.virtual_switch.portgroups[0].usage, "user")

    def test_110_addstorageips(self):
        # storage IPs
        for i in range(0, 2):
            ip = self.net["vm_storage_net"].usable[i + 26]
            machine = "utpgs01p%d" % i

            self.noouttest(["add", "interface", "--interface", "eth1",
                            "--machine", machine,
                            "--mac", ip.mac])

            self.dsdb_expect_add("utpgh%d-eth1.aqd-unittest.ms.com" % i,
                                 ip, "eth1", ip.mac,
                                 primary="utpgh%d.aqd-unittest.ms.com" % i)
            command = ["add", "interface", "address", "--machine", machine,
                       "--interface", "eth1", "--ip", ip]
            self.noouttest(command)
        self.dsdb_verify()

    def test_120_catutpgcl0(self):
        data_command = ["cat", "--cluster", "utpgcl0", "--data"]
        data = self.commandtest(data_command)

        self.matchoutput(data, '"system/cluster/rack/room" = "utroom1";',
                         data_command)

        data_command = ["cat", "--machine", "utpgs01p0"]
        data = self.commandtest(data_command)

        self.matchoutput(data, '"rack/name" = "ut3";',
                         data_command)
        self.matchoutput(data, '"rack/room" = "utroom1";',
                         data_command)

    # Autopg test
    def test_130_addinterfaces(self):
        self.noouttest(["add", "interface", "--machine", "utpgm0",
                        "--interface", "eth0", "--automac", "--autopg"])

        # Consume available IP addresses
        self.dsdb_expect_add("utpgm0-ip1.aqd-unittest.ms.com",
                             self.net["autopg1"].usable[0], "eth0_ip1")
        self.dsdb_expect_add("utpgm0-ip2.aqd-unittest.ms.com",
                             self.net["autopg1"].usable[1], "eth0_ip2")
        self.noouttest(["add_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip1", "--autoip",
                        "--fqdn", "utpgm0-ip1.aqd-unittest.ms.com"])
        self.noouttest(["add_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip2", "--autoip",
                        "--fqdn", "utpgm0-ip2.aqd-unittest.ms.com"])
        self.dsdb_verify()

        # All IPs gone, this should fail
        command = ["add", "interface", "--machine", "utpgm1",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on virtual switch "
                         "utvswitch.",
                         command)

        # Free up the IP addresses
        self.dsdb_expect_delete(self.net["autopg1"].usable[0])
        self.dsdb_expect_delete(self.net["autopg1"].usable[1])
        self.noouttest(["del_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip1"])
        self.noouttest(["del_interface_address", "--machine", "utpgm0",
                        "--interface", "eth0", "--label", "ip2"])
        self.dsdb_verify()

        # Now it should succeed
        self.noouttest(["add", "interface", "--machine", "utpgm1",
                        "--interface", "eth0", "--automac", "--autopg"])

        # The third one shall fail
        command = ["add", "interface", "--machine", "utpgm2",
                   "--interface", "eth0", "--automac", "--autopg"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No available user port groups on virtual switch "
                         "utvswitch.",
                         command)

    def test_140_verify_audit(self):
        command = ["search_audit", "--command", "add_interface",
                   "--keyword", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "pg=user-v710", command)

    # resourcegroup tests
    def test_150_add_rg_to_cluster(self):
        command = ["add_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--required_type=share"]
        out = self.statustest(command)
        self.matchoutput(out,
                         "Please use the --metacluster option for metaclusters.",
                         command)

        command = ["show_resourcegroup", "--metacluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Bound to: ESX Metacluster utmc8", command)

        command = ["add_resourcegroup", "--resourcegroup=utmc8as2",
                   "--metacluster=utmc8", "--required_type=share"]
        self.noouttest(command)

        command = ["show_resourcegroup", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Resource Group: utmc8as2", command)

    def test_160_verify_metacluster(self):
        self.statustest(["make", "cluster", "--metacluster", "utmc8"])

        command = ["cat", "--metacluster", "utmc8", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template clusterdata/utmc8;", command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc8";', command)
        self.matchoutput(out, '"system/metacluster/type" = "meta";', command)
        self.searchoutput(out,
                          r'"system/metacluster/members" = list\(\s*'
                          r'"utpgcl0",\s*'
                          r'"utpgcl1"\s*'
                          r'\);',
                          command)
        self.matchoutput(out, '"system/build" = "build";', command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/location" = "ut.ny.na";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/continent" = "na";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/city" = "ny";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/campus" = "ny";',
                         command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/building" = "ut";',
                         command)
        self.matchoutput(out,
                         '"system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utmc8/'
                         'resourcegroup/utmc8as1/config"));',
                         command)
        self.matchoutput(out,
                         '"system/resources/resourcegroup" = '
                         'append(create("resource/cluster/utmc8/'
                         'resourcegroup/utmc8as2/config"));',
                         command)

    # share tests
    def test_200_add_share_to_rg(self):
        command = ["add_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        self.noouttest(command)

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchclean(out, "Latency", command)

        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        self.noouttest(command)

        command = ["show_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as2", command)

    def test_210_add_same_share_name_fail(self):
        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--share=test_v2_share"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Share test_v2_share, "
                         "resource group utmc8as2 already exists.", command)

    def test_220_cat_resourcegroup(self):
        command = ["cat", "--resourcegroup=utmc8as1", "--metacluster=utmc8",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/config;",
                         command)
        self.matchoutput(out, '"name" = "utmc8as1', command)
        self.matchoutput(out,
                         '"resources/share" = '
                         'append(create("resource/cluster/utmc8/resourcegroup/'
                         'utmc8as1/share/test_v2_share/config"));',
                         command)

    def test_230_cat_share(self):
        command = ["cat", "--share=test_v2_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/share/test_v2_share/config;",
                         command)
        self.matchoutput(out, '"name" = "test_v2_share";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_v2_share";',
                         command)
        self.matchclean(out, 'latency', command)

    def test_240_verify_resourcegroup_share(self):
        command = ["show_resourcegroup", "--metacluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_250_verify_metacluster_share(self):
        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_260_search_metacluster_by_share(self):
        command = ["search_metacluster", "--share", "test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc8", command)

    def test_265_search_cluster_by_share(self):
        self.noouttest(["search_cluster", "--share", "test_v2_share"])

    # disk tests
    def test_300_add_disk_to_share(self):
        for i in range(0, 3):
            self.noouttest(["add", "disk", "--machine", "utpgm%d" % i,
                            "--disk", "sda", "--controller", "scsi",
                            "--snapshot", "--share", "test_v2_share",
                            "--size", "34", "--resourcegroup", "utmc8as1",
                            "--address", "0:0", "--iops_limit", "20"])

    def test_305_search_machine_by_share(self):
        command = ["search_machine", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utpgm0", command)
        self.matchclean(out, "evm2", command)
        self.matchclean(out, "evm10", command)

    def test_310_verify_add_disk_to_share(self):
        command = "show machine --machine utpgm0"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$", command)
        self.searchoutput(out, r"IOPS Limit: 20", command)

        command = ["show_machine", "--machine", "utpgm0", "--format", "proto"]
        machine = self.protobuftest(command, expect=1)[0]
        self.assertEqual(machine.name, "utpgm0")
        self.assertEqual(len(machine.disks), 1)
        self.assertEqual(machine.disks[0].device_name, "sda")
        self.assertEqual(machine.disks[0].disk_type, "scsi")
        self.assertEqual(machine.disks[0].capacity, 34)
        self.assertEqual(machine.disks[0].address, "0:0")
        self.assertEqual(machine.disks[0].bus_address, "")
        self.assertEqual(machine.disks[0].wwn, "")
        self.assertEqual(machine.disks[0].snapshotable, True)
        self.assertEqual(machine.disks[0].backing_store.name, "test_v2_share")
        self.assertEqual(machine.disks[0].backing_store.type, "share")
        self.assertEqual(machine.disks[0].iops_limit, 20)
        self.assertEqual(machine.vm_host.fqdn, "")
        self.assertEqual(machine.vm_cluster.name, "utpgcl0")
        self.assertEqual(machine.vm_cluster.metacluster, "utmc8")

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Disk Count: 3", command)

        command = ["cat", "--machine", "utpgm0", "--generate"]

        out = self.commandtest(command)
        self.matchoutput(out, '"harddisks/{sda}" = nlist(', command)
        self.searchoutput(out,
                          r'"mountpoint", "/vol/lnn30f1v1/test_v2_share",\s*'
                          r'"path", "utpgm0/sda.vmdk",\s*'
                          r'"server", "lnn30f1",\s*'
                          r'"sharename", "test_v2_share",\s*'
                          r'"snapshot", true',
                          command)

    def test_320_add_filesystem_fail(self):
        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--resourcegroup=utmc8as1"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Resource Group utmc8as1 may contain resources "
                         "of type share only.", command)

    # machine move tests
    def test_350_move_machine_pre(self):
        command = ["show_machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utpgcl0", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$",
                          command)

    def test_360_move_machine(self):
        # Moving the machine from one cluster to the other exercises the case in
        # the disk movement logic when the old share is inside a resource group.
        command = ["update_machine", "--machine", "utpgm0",
                   "--cluster", "utpgcl1"]
        self.noouttest(command)

    def test_370_verify_move(self):
        command = ["show_machine", "--machine", "utpgm0"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hosted by: ESX Cluster utpgcl1", command)
        self.searchoutput(out,
                          r"Disk: sda 34 GB scsi "
                          r"\(virtual_disk stored on share test_v2_share\) "
                          r"\[boot, snapshot\]$",
                          command)

    def test_380_fail_update_disk(self):
        command = ["update_disk", "--disk", "sda", "--machine", "utpgm0",
                   "--share", "non_existent_share",
                   "--resourcegroup", "utmc8as1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "ESX Cluster utpgcl1 does not have share "
                         "non_existent_share assigned to it in "
                         "resourcegroup utmc8as1.",
                         command)

#    metacluster aligned svc tests
    def test_400_addvcenterservices(self):
        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-server-dev"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

    def test_410_bindvcenterservices(self):
        command = ["bind_client", "--metacluster", "utmc8",
                   "--service", "vcenter", "--instance", "ut"]
        err = self.statustest(command)
        # The service should be bound to the metacluster and to the hosts, but
        # not to the clusters as they do not require it
        self.matchoutput(err, "Metacluster utmc8 adding binding for "
                         "service instance vcenter/ut", command)
        self.matchoutput(err, "Host utpgh0.aqd-unittest.ms.com adding binding "
                         "for service instance vcenter/ut", command)
        self.matchoutput(err, "Host utpgh1.aqd-unittest.ms.com adding binding "
                         "for service instance vcenter/ut", command)
        self.matchclean(err, "utpgcl", command)

        command = ["show", "host", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Uses Service: vcenter Instance: ut",
                         command)

        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Member Alignment: Service vcenter Instance ut", command)

    def test_420_failmaxclientcount(self):
        command = ["update_service", "--service", "vcenter", "--instance", "ut",
                   "--max_clients", "17"]
        self.noouttest(command)

        command = ["map", "service", "--service", "vcenter", "--instance", "ut",
                   "--building", "ut"]
        self.noouttest(command)

        self.add_utcluster("utpgcl2", "utmc8")

        command = ["make", "cluster", "--cluster", "utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Please use the --metacluster option for "
                         "metaclusters.", command)
        self.matchoutput(out,
                         "The available instances ['ut'] for service vcenter "
                         "are at full capacity.",
                         command)

        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut"]
        self.noouttest(command)

        self.statustest(["del_cluster", "--cluster=utpgcl2"])

    def test_430_unbindvcenterservices(self):
        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-server-dev"]
        self.noouttest(command)

        self.noouttest(["unbind_client", "--metacluster", "utmc8",
                        "--service", "vcenter"])

    def test_440_unmapvcenterservices(self):
        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut",
                   "--personality", "vulcan2-server-dev", "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Host utpgh0.aqd-unittest.ms.com removing "
                         "binding for service instance vcenter/ut", command)

        command = ["show", "host", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out,
                        "Uses Service: vcenter Instance: ut",
                        command)

    #
    # service binding conflicts
    #
    def test_500_add_mc_esx_service(self):
        command = ["add", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["map", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        command = ["rebind_client", "--metacluster", "utmc8",
                   "--service", "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Metacluster utmc8 adding binding for service "
                         "instance esx_management_server/ut.mc",
                         command)
        for cluster in ["utpgcl0", "utpgcl1"]:
            self.matchoutput(err,
                             "ESX Cluster %s removing binding for service "
                             "instance esx_management_server/ut.a" % cluster,
                             command)
            self.matchoutput(err,
                             "ESX Cluster %s adding binding for service "
                             "instance esx_management_server/ut.mc" % cluster,
                             command)
        for host in ["utpgh0", "utpgh1"]:
            self.matchoutput(err,
                             "Host %s.aqd-unittest.ms.com removing binding for "
                             "service instance esx_management_server/ut.a" % host,
                             command)
            self.matchoutput(err,
                             "Host %s.aqd-unittest.ms.com adding binding for "
                             "service instance esx_management_server/ut.mc" % host,
                             command)

    def test_510_fail_make_host(self):
        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for "
                         "host utpgh0.aqd-unittest.ms.com.",
                         command)

    def test_510_fail_make_cluster(self):
        command = ["make", "cluster", "--cluster", "utpgcl0"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for ESX cluster utpgcl0.",
                         command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for "
                         "host utpgh0.aqd-unittest.ms.com.",
                         command)

    def test_520_verify_client_count(self):
        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 16$", command)

    def test_530_verify_mixed_client_count(self):
        self.add_utcluster("utpgcl3", "utmc8")
        command = ["bind_client", "--cluster", "utpgcl3", "--service",
                   "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err, "ESX Cluster utpgcl3 adding binding for service "
                         "instance esx_management_server/ut.mc", command)

        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 24$", command)

        # Can't unbind an an aligned service here and don't want unalign it

    def test_538_del_utpgcl3(self):
        self.statustest(["del_cluster", "--cluster=utpgcl3"])

    def test_540_remove_mc_esx_service(self):
        command = ["del_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["unbind_client", "--metacluster", "utmc8",
                   "--service", "esx_management_server"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        out = self.statustest(["make_cluster", "--cluster", "utpgcl0"])
        self.matchoutput(out, "removing binding for service instance "
                         "esx_management_server/ut.mc", command)
        self.matchoutput(out, "adding binding for service instance "
                         "esx_management_server/ut.a", command)
        out = self.statustest(["make_cluster", "--cluster", "utpgcl1"])
        self.matchoutput(out, "removing binding for service instance "
                         "esx_management_server/ut.mc", command)
        self.matchoutput(out, "adding binding for service instance "
                         "esx_management_server/ut.a", command)

        command = ["del", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

#    Storage group related deletes

    def test_600_delutpgmdisk(self):
        for i in range(0, 3):
            self.noouttest(["del_disk", "--machine", "utpgm%d" % i, "--disk", "sda"])

    def test_610_delresourcegroup(self):
        command = ["del_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        self.noouttest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8"]
        self.noouttest(command)

        command = ["del_share", "--resourcegroup=utmc8as2",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        self.noouttest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as2",
                   "--metacluster=utmc8"]
        self.noouttest(command)

    # Metacluster / cluster / Switch deletes
    def test_700_delinterfaces(self):
        for i in range(0, 2):
            ip = self.net["vm_storage_net"].usable[i + 26]
            machine = "utpgs01p%d" % i

            self.dsdb_expect_delete(ip)
            command = ["del", "interface", "address", "--machine", machine,
                       "--interface", "eth1", "--ip", ip]
            self.noouttest(command)

            self.noouttest(["del", "interface", "--interface", "eth1",
                            "--machine", machine])
        self.dsdb_verify()

    def test_710_delmachines(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            self.noouttest(["del", "machine", "--machine", machine])

    def test_720_uncluster(self):
        for i in range(0, 2):
            host = "utpgh%s.aqd-unittest.ms.com" % i
            cluster = "utpgcl%d" % i
            self.noouttest(["uncluster", "--hostname", host,
                            "--cluster", cluster,
                            "--personality", "esx_standalone"])

    def test_725_del10gigrackhosts(self):
        for i in range(0, 2):
            basetime = datetime.now()
            ip = self.net["autopg2"].usable[i]
            hostname = "utpgh%d.aqd-unittest.ms.com" % i

            self.dsdb_expect_delete(ip)
            command = ["del", "host", "--hostname", hostname]
            self.statustest(command)
            self.wait_notification(basetime, 1)
        self.dsdb_verify()

    def test_730_del10gigracks(self):
        for port in range(0, 2):
            self.noouttest(["del", "machine", "--machine",
                            "utpgs01p%d" % port])

    def test_750_delutpgcl(self):
        command = ["del_metacluster", "--metacluster=utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "ESX Metacluster utmc8 is still in use by "
                         "clusters: utpgcl0, utpgcl1.", command)

        for i in range(0, 2):
            command = ["del_cluster", "--cluster=utpgcl%d" % i]
            self.statustest(command)

    def test_760_delutmc8(self):
        basetime = datetime.now()
        self.statustest(["del_metacluster", "--metacluster=utmc8"])
        self.wait_notification(basetime, 1)

        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utmc8%s" % self.xml_suffix)))

    def test_800_cleanup(self):
        self.drop_personality("vmhost", "vulcan2-server-dev")
        self.drop_personality("esx_cluster", "vulcan2-server-dev")
        self.drop_personality("metacluster", "vulcan2")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcan20)
    unittest.TextTestRunner(verbosity=2).run(suite)
