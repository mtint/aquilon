#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the make aquilon command."""

import os
import sys
import unittest
import re

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestMakeAquilon(TestBrokerCommand):

    def testmakeunittest02(self):
        self.noouttest(["make", "aquilon",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--personality", "compileserver", "--os", "linux/4.0.1-x86_64"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"),
            "unittest02.one-nyp.ms.com.xml")))

    def testverifycatunittest02(self):
        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c5n10');""",
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip0, self.netmask0, self.broadcast0, self.gateway0),
            command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ny.ms.com/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/bootserver/np.test/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/dns/nyinfratest/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/ntp/pa.ny.na/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'personality/compileserver/config' };""",
            command)
        self.matchoutput(out,
            """include { 'archetype/final' };""",
            command)

    def testmakeunittest00(self):
        self.noouttest(["make", "aquilon",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--buildstatus", "blind",
            "--personality", "compileserver", "--os", "linux/4.0.1-x86_64"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"),
            "unittest00.one-nyp.ms.com.xml")))

    def testverifybuildstatus(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: blind", command)

    def testverifybindautoafs(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testverifybindautodns(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/dns/nyinfratest", command)

    def testverifybindautoutsvc(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        count_re = re.compile(r'Client Count: (\d+)')
        inst_count = 0
        for m in count_re.finditer(out):
            inst_count += 1
            self.assert_(int(m.group(1)) > 0,
                    "Service Instance of utsvc has a client count <= 0:\n@@@\n'%s'\n@@@\n" %
                    out)
        self.assert_(inst_count > 0,
                "No utsvc service instances found:\n@@@\n'%s'\n@@@\n" % out)

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c1n3');""",
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip2, self.netmask2, self.broadcast2, self.gateway2),
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth1' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip3, self.netmask3, self.broadcast3, self.gateway3),
            command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ny.ms.com/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/bootserver/np.test/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/dns/nyinfratest/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/ntp/pa.ny.na/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'personality/compileserver/config' };""",
            command)
        self.matchoutput(out,
            """include { 'archetype/final' };""",
            command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeAquilon)
    unittest.TextTestRunner(verbosity=2).run(suite)

