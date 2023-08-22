from enum import IntEnum


class ZoneIDs(IntEnum):
    CashbotHQ = 12000
    CashbotHQLobby = 12100


ValidStartingLocations = {ZoneIDs.CashbotHQ, ZoneIDs.CashbotHQLobby}


class DoorReject(IntEnum):
    pass


DoorRejectNames = {}


DynamicZonesBegin = 61001
DynamicZonesEnd = 999999
