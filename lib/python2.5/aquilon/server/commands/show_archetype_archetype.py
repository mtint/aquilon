# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show archetype --archetype`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.archetype import get_archetype


class CommandShowArchetypeArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, archetype, **arguments):
        return get_archetype(session, archetype)


