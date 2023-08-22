import random

from toontown.toonbase.globals.TTGlobalsWorld import ZoneIDs
from toontown.world import ZoneUtil

PlaygroundCenters = {
    ZoneIDs.CashbotHQ: (133, 512, 32.246, 0, 0, 0),
    ZoneIDs.CashbotHQLobby: (0, 0, 0, 0, 0, 0),
}

HoodNames = {
    ZoneIDs.CashbotHQ: "Cashbot HQ",
}


def getPlaygroundCenterFromId(zoneId):
    options = PlaygroundCenters.get(zoneId, PlaygroundCenters.get(ZoneUtil.getHoodId(zoneId)))
    if isinstance(options, list):
        options = random.choice(options)
    return options or (0, 0, 0, 0, 0, 0)


def getFullnameFromId(zoneId):
    return HoodNames.get(zoneId, "Unknown location")
