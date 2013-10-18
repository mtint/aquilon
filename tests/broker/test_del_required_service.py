#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del required service command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand

archetype_required = {
    'aquilon': ["aqd", "bootserver", "dns", "lemon", "ntp", "support-group",
                "syslogng"],
    'esx_cluster': ["esx_management_server"],
    'vmhost': ["dns", "ntp", "syslogng"],
}


class TestDelRequiredService(TestBrokerCommand):

    def testdelrequiredafs(self):
        command = "del required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testdelrequiredafsnojustification(self):
        command = "del required service --service afs --archetype aquilon"
        out = self.unauthorizedtest(command.split(" "), auth=True,
                                    msgcheck=False)
        self.matchoutput(out,
                         "Changing the required services of an archetype "
                         "requires --justification.",
                         command)

    def testdelrequirednetmap(self):
        command = ["del_required_service", "--service=netmap",
                   "--personality=eaitools", "--archetype=aquilon"]
        self.noouttest(command)

    def testdelrequiredafsagain(self):
        command = "del required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.notfoundtest(command.split(" "))

    def testdelrequiredall(self):
        for archetype, services in archetype_required.items():
            for service in services:
                self.noouttest(["del_required_service", "--service", service,
                                "--archetype", archetype,
                                "--justification", "tcm=12345678"])

            command = ["show_archetype", "--archetype", archetype]
            out = self.commandtest(command)
            for service in services:
                self.matchclean(out, "Service: %s" % service, command)

    def testdelrequiredpersonality(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["del_required_service", "--service", service,
                       "--archetype=aquilon", "--personality=unixeng-test"]
            self.noouttest(command)

    def testdelrequiredpersonalityagain(self):
        command = ["del", "required", "service", "--service", "chooser1",
                   "--archetype=aquilon", "--personality=unixeng-test"]
        self.notfoundtest(command)

    def testverifydelrequiredpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=unixeng-test"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: chooser1", command)
        self.matchclean(out, "Service: chooser2", command)
        self.matchclean(out, "Service: chooser3", command)

    def testdelrequiredbadpersonality(self):
        command = ["del_required_service", "--service", "badservice",
                   "--archetype=aquilon", "--personality=badpersonality2"]
        self.noouttest(command)

    def testverifydelrequiredbadpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=badpersonality2"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: badservice", command)

    def testdelrequiredesx(self):
        command = ["del_required_service", "--service=esx_management_server",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)
        command = ["del_required_service", "--service=vmseasoning",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testverifydelrequiredesx(self):
        command = ["show_personality",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: esx_management_server", command)
        self.matchclean(out, "Service: vmseasoning", command)
        command = ["show_personality",
                   "--archetype=esx_cluster"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: esx_management_server", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)
