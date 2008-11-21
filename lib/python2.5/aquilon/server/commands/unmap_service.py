# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq unmap service`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.svc.service_map import ServiceMap
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.service_instance import get_service_instance


class CommandUnmapService(BrokerCommand):

    required_parameters = ["service", "instance"]

    @add_transaction
    @az_check
    def render(self, session, service, instance, **arguments):
        dbservice = get_service(session, service)
        dblocation = get_location(session, **arguments)
        dbinstance = get_service_instance(session, dbservice, instance)
        dbmap = session.query(ServiceMap).filter_by(location=dblocation,
                service_instance=dbinstance).first()
        if dbmap:
            session.delete(dbmap)
        session.flush()
        session.refresh(dbservice)
        session.refresh(dbinstance)
        return


