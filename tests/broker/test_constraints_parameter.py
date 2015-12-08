#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand


class TestParameterConstraints(TestBrokerCommand):

    def test_100_archetype_validation(self):
        cmd = ["del_parameter_definition", "--archetype", "aquilon",
               "--path=espinfo/function"]
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "Parameter with path espinfo/function used by following and cannot be deleted", cmd)

    # This test should eventually be here, but parameter tests need to be
    # re-organized first
    #def test_110_feature_validation(self):
    #    cmd = ["del_parameter_definition", "--feature", "myfeature", "--type=host",
    #           "--path=teststring"]
    #    out = self.badrequesttest(cmd)
    #    self.matchoutput(out, "Parameter with path teststring used by following and cannot be deleted", cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParameterConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
