#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show dns_domain --dns_domain`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.dns_domain import get_dns_domain


class CommandShowDnsDomainDnsDomain(BrokerCommand):

    required_parameters = ["dns_domain"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, dns_domain, **arguments):
        return get_dns_domain(session, dns_domain)


#if __name__=='__main__':