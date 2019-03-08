#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Module for testing the add_entitlement command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddEntitlement(TestBrokerCommand):

    #
    # 1xx => test all working "to_" options
    #

    def test_100_add_etype_all_to_human_on_hostname(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.noouttest(command)

    def test_105_show_etype_all_to_human_on_hostname(self):
        command = [
            'show_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser1',
                       '  On Host: unittest02.one-nyp.ms.com'))
        self.output_equals(out, expected_out, command)

    def test_110_add_etype_human_to_human_on_hostname(self):
        command = [
            'add_entitlement',
            '--type', 'etype_human',
            '--to_user', 'testuser1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.noouttest(command)

    def test_115_show_etype_human_to_human_on_hostname(self):
        command = [
            'show_entitlement',
            '--type', 'etype_human',
            '--to_user', 'testuser1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_human',
                       '  To Human User: testuser1',
                       '  On Host: unittest02.one-nyp.ms.com'))
        self.output_equals(out, expected_out, command)

    def test_120_add_etype_all_to_robot_on_hostname(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testbot1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.noouttest(command)

    def test_125_show_etype_all_to_robot_on_hostname(self):
        command = [
            'show_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testbot1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Robot User: testbot1',
                       '  On Host: unittest02.one-nyp.ms.com'))
        self.output_equals(out, expected_out, command)

    def test_130_add_etype_robot_to_robot_on_hostname(self):
        command = [
            'add_entitlement',
            '--type', 'etype_robot',
            '--to_user', 'testbot1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.noouttest(command)

    def test_135_show_etype_robot_to_robot_on_hostname(self):
        command = [
            'show_entitlement',
            '--type', 'etype_robot',
            '--to_user', 'testbot1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_robot',
                       '  To Robot User: testbot1',
                       '  On Host: unittest02.one-nyp.ms.com'))
        self.output_equals(out, expected_out, command)

    def test_140_add_etype_all_to_grn_on_hostname(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_grn', 'grn:/ms/ei/aquilon/aqd',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.noouttest(command)

    def test_145_show_etype_all_to_grn_on_hostname(self):
        command = [
            'show_entitlement',
            '--type', 'etype_all',
            '--to_grn', 'grn:/ms/ei/aquilon/aqd',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To GRN: grn:/ms/ei/aquilon/aqd',
                       '  On Host: unittest02.one-nyp.ms.com'))
        self.output_equals(out, expected_out, command)

    def test_150_add_etype_grn_to_grn_on_hostname(self):
        command = [
            'add_entitlement',
            '--type', 'etype_grn',
            '--to_grn', 'grn:/ms/ei/aquilon/aqd',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.noouttest(command)

    def test_155_show_etype_grn_to_grn_on_hostname(self):
        command = [
            'show_entitlement',
            '--type', 'etype_grn',
            '--to_grn', 'grn:/ms/ei/aquilon/aqd',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_grn',
                       '  To GRN: grn:/ms/ei/aquilon/aqd',
                       '  On Host: unittest02.one-nyp.ms.com'))
        self.output_equals(out, expected_out, command)

    def test_160_add_etype_grn_to_eon_id_on_hostname(self):
        command = [
            'add_entitlement',
            '--type', 'etype_grn',
            '--to_eon_id', 3,
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.noouttest(command)

    def test_165_show_etype_grn_to_eon_id_on_hostname(self):
        command = [
            'show_entitlement',
            '--type', 'etype_grn',
            '--to_eon_id', 3,
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_grn',
                       '  To GRN: grn:/ms/ei/aquilon/unittest',
                       '  On Host: unittest02.one-nyp.ms.com'))
        self.output_equals(out, expected_out, command)

    #
    # 2xx => test all working "on_" options
    #

    def test_200_add_etype_all_to_human_on_cluster(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_cluster', 'utecl1',
        ]
        self.noouttest(command)

    def test_205_search_etype_all_to_human_on_cluster(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_cluster', 'utecl1',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser1',
                       '  On ESX Cluster: utecl1'))
        self.output_equals(out, expected_out, command)

    def test_210_add_etype_all_to_human_on_personality(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_personality', 'compileserver',
        ]
        self.noouttest(command)

    def test_215_search_etype_all_to_human_on_personality(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_personality', 'compileserver',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser1',
                       '  On Personality: compileserver',
                       '  On Organization: ms'))
        self.output_equals(out, expected_out, command)

    def test_220_add_etype_all_to_human_on_personality_on_location(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_personality', 'compileserver',
            '--on_hub', 'ny',
        ]
        self.noouttest(command)

    def test_225_search_etype_all_to_human_on_personality_on_location(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_personality', 'compileserver',
            '--on_hub', 'ny',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser2',
                       '  On Personality: compileserver',
                       '  On Hub: ny'))
        self.output_equals(out, expected_out, command)

    def test_230_add_etype_all_to_human_on_archetype(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_archetype', 'aquilon',
            '--on_host_environment', 'dev',
        ]
        self.noouttest(command)

    def test_235_search_etype_all_to_human_on_archetype(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_archetype', 'aquilon',
            '--on_host_environment', 'dev',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser1',
                       '  On Archetype: aquilon',
                       '  On Host Environment: dev',
                       '  On Organization: ms'))
        self.output_equals(out, expected_out, command)

    def test_240_add_etype_all_to_human_on_archetype_on_location(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_archetype', 'aquilon',
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        self.noouttest(command)

    def test_245_search_etype_all_to_human_on_archetype_on_location(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_archetype', 'aquilon',
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser2',
                       '  On Archetype: aquilon',
                       '  On Host Environment: dev',
                       '  On Hub: ny'))
        self.output_equals(out, expected_out, command)

    def test_250_add_etype_all_to_human_on_grn(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
            '--on_host_environment', 'dev',
        ]
        self.noouttest(command)

    def test_255_search_etype_all_to_human_on_grn(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
            '--on_host_environment', 'dev',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser1',
                       '  On GRN: grn:/ms/ei/aquilon/ut2',
                       '  On Host Environment: dev',
                       '  On Organization: ms'))
        self.output_equals(out, expected_out, command)

    def test_260_add_etype_all_to_human_on_grn_on_location(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        self.noouttest(command)

    def test_265_search_etype_all_to_human_on_grn_on_location(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser2',
                       '  On GRN: grn:/ms/ei/aquilon/ut2',
                       '  On Host Environment: dev',
                       '  On Hub: ny'))
        self.output_equals(out, expected_out, command)

    def test_270_add_etype_all_to_human_on_eon_id(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_eon_id', 3,
            '--on_host_environment', 'dev',
        ]
        self.noouttest(command)

    def test_275_search_etype_all_to_human_on_eon_id(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_eon_id', 3,
            '--on_host_environment', 'dev',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser1',
                       '  On GRN: grn:/ms/ei/aquilon/unittest',
                       '  On Host Environment: dev',
                       '  On Organization: ms'))
        self.output_equals(out, expected_out, command)

    def test_280_add_etype_all_to_human_on_eon_id_on_location(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_eon_id', 3,
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        self.noouttest(command)

    def test_285_search_etype_all_to_human_on_eon_id_on_location(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_eon_id', 3,
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement: etype_all',
                       '  To Human User: testuser2',
                       '  On GRN: grn:/ms/ei/aquilon/unittest',
                       '  On Host Environment: dev',
                       '  On Hub: ny'))
        self.output_equals(out, expected_out, command)

    #
    # 6xx => test all errors related to "to_" options
    #

    def test_600_add_etype_human_to_robot(self):
        command = [
            'add_entitlement',
            '--type', 'etype_human',
            '--to_user', 'testbot1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.badrequesttest(command)

    def test_600_add_etype_grn_to_human(self):
        command = [
            'add_entitlement',
            '--type', 'etype_grn',
            '--to_user', 'testuser1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        self.badrequesttest(command)

    #
    # 65x => test all errors related to "on_" options
    #

    def test_650_add_on_archetype_no_host_environment(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser3',
            '--on_archetype', 'aquilon',
        ]
        err = self.badoptiontest(command)
        self.matchoutput(err,
                         'Option or option group on_archetype can only be '
                         'used together with one of: on_host_environment.',
                         command)

    def test_650_add_on_grn_no_host_environment(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser3',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
        ]
        err = self.badoptiontest(command)
        self.matchoutput(err,
                         'Option or option group on_grn can only be used '
                         'together with one of: on_host_environment.',
                         command)

    def test_650_add_on_eon_id_no_host_environment(self):
        command = [
            'add_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser3',
            '--on_eon_id', 3,
        ]
        err = self.badoptiontest(command)
        self.matchoutput(err,
                         'Option or option group on_eon_id can only be used '
                         'together with one of: on_host_environment.',
                         command)

    #
    # 8xx => test all related to show
    #

    def test_800_show_on_hostname(self):
        command = [
            'show_entitlement',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Archetype: aquilon',
             '  On Host Environment: dev',
             '  On Organization: ms'),
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On Archetype: aquilon',
             '  On Host Environment: dev',
             '  On Hub: ny'),
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Personality: compileserver',
             '  On Organization: ms'),
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On Personality: compileserver',
             '  On Hub: ny'),
            ('Entitlement: etype_all',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_all',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_robot',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_human',
             '  To Human User: testuser1',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self.output_unordered_equals(out, expected_out, command)

    #
    # 9xx => test all related to search
    #

    def test_900_search_on_hostname(self):
        command = [
            'search_entitlement',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_all',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_all',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_robot',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_human',
             '  To Human User: testuser1',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self.output_unordered_equals(out, expected_out, command)

    def test_900_search_to_any_robot_on_hostname(self):
        command = [
            'search_entitlement',
            '--to_any_user_of_type', 'robot',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_robot',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self.output_unordered_equals(out, expected_out, command)

    def test_900_search_to_any_grn_on_hostname(self):
        command = [
            'search_entitlement',
            '--to_any_grn',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        out = self.commandtest(command)
        expected_out = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self.output_unordered_equals(out, expected_out, command)

    def test_900_search_etype_all_on_host_environment(self):
        command = [
            'search_entitlement',
            '--type', 'etype_all',
            '--on_host_environment', 'dev',
        ]
        out = self.commandtest(command)
        expected_out = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Archetype: aquilon',
             '  On Host Environment: dev',
             '  On Organization: ms'),
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On Archetype: aquilon',
             '  On Host Environment: dev',
             '  On Hub: ny'),
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Personality: compileserver',
             '  On Organization: ms'),
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On Personality: compileserver',
             '  On Hub: ny'),
            ('Entitlement: etype_all',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_all',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On GRN: grn:/ms/ei/aquilon/ut2',
             '  On Host Environment: dev',
             '  On Organization: ms'),
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On GRN: grn:/ms/ei/aquilon/ut2',
             '  On Host Environment: dev',
             '  On Hub: ny'),
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host Environment: dev',
             '  On Organization: ms'),
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host Environment: dev',
             '  On Hub: ny'),
        ]]
        self.output_unordered_equals(out, expected_out, command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddEntitlement)
    unittest.TextTestRunner(verbosity=2).run(suite)