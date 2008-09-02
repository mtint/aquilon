#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Switch Ports model the ports of switches and are they physical connections
    to other machines' physical interfaces via the foreign key to interface """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Table, Column, Integer, DateTime, Sequence, ForeignKey
from sqlalchemy.orm import relation, deferred
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.db_factory     import Base
from aquilon.aqdb.net.network    import Network
from aquilon.aqdb.hw.tor_switch  import TorSwitch
from aquilon.aqdb.hw.interface   import Interface


class SwitchPort(Base):
    """ Tor switches are types of machines (for now at least). What they
        have, besides their own interfaces and a network they provide, are
        ports, which connect to physical interfaces """
    #TODO: figure out all the association mapping stuff
    __tablename__ = 'switch_port'

    #TODO: code level constraint on machine_type == tor_switch
    switch_id   = Column(Integer,
                       ForeignKey(TorSwitch.id, ondelete = 'CASCADE',
                                  name = 'swport_hwent_fk'), primary_key = True)

    interface_id     = Column(Integer, ForeignKey('interface.id', ondelete = 'CASCADE',
                                     name = 'switch_int_fk'), primary_key=True)

    slot         = Column(Integer, default=None)
    port_number  = Column(Integer, nullable=False)



    # network_id as an attr of the port on the switch, makes switch port
    # a more flexible linkage of switches, networks, and interfaces,
    # even though TOR (or single vlan or layer2 only switch ports all have the
    # same network id. vlan could go here (or on network itself)...
    #To implement properly, this must be tiggered to update as soon as the
    # network property is set on a tor switch.
    #TODO: handle ondelete behavior for network with 'set null' behavior
    network_id   = Column(Integer, ForeignKey(Network.c.id,
                                              name = 'switch_port_network_fk'))

    link_creation_date = deferred( Column('creation_date', DateTime,
                                          default = datetime.now,
                                          nullable = False))

    switch = relation(TorSwitch, uselist = False, backref = 'switchport',
                         passive_deletes = True)

    interface  = relation(Interface, uselist = False, backref = 'switchport',
                         passive_deletes = True)

switch_port = SwitchPort.__table__
switch_port.primary_key.name = 'switch_port_pk'

table = switch_port

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

