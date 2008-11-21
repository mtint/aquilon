# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del service`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.service import get_service
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.svc.service_map import ServiceMap
from aquilon.server.templates.service import (PlenaryService,
        PlenaryServiceInstance, PlenaryServiceInstanceClientDefault)


class CommandDelService(BrokerCommand):

    required_parameters = ["service"]

    @add_transaction
    @az_check
    def render(self, session, service, instance, **arguments):
        # This should fail nicely if the service is required for an archetype.
        dbservice = get_service(session, service)
        if not instance:
            if dbservice.instances:
                raise ArgumentError("Cannot remove service with instances defined.")
            plenary_info = PlenaryService(dbservice)
            plenary_info.remove(self.config.get("broker", "plenarydir"))
            session.delete(dbservice)
            return
        dbsi = session.query(ServiceInstance).filter_by(
                name=instance, service=dbservice).first()

        if dbsi:
            if dbsi.client_count > 0:
                raise ArgumentError("instance has clients and cannot be deleted.")

            plenary_info = PlenaryServiceInstance(dbservice, dbsi)
            plenary_info.remove(self.config.get("broker", "plenarydir"))

            plenary_info = PlenaryServiceInstanceClientDefault(dbservice, dbsi)
            plenary_info.remove

            # Check the service map and remove any mappings
            for dbmap in session.query(ServiceMap).filter_by(service_instance=dbsi).all():
                session.delete(dbmap)

            session.delete(dbsi)
            session.flush()
            session.refresh(dbservice)
            
        # FIXME: Cascade to relevant objects...
        return


