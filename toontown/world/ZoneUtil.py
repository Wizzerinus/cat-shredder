"""
        ZoneUtil

        Get various information from a zone ID.
"""


from toontown.toonbase.globals.TTGlobalsWorld import ZoneIDs, DynamicZonesBegin, DynamicZonesEnd

zoneUtilNotify = directNotify.newCategory("ZoneUtil")


def isCogHQZone(zoneId):
    return (zoneId >= 10000) and (zoneId < 15000)


def isDynamicZone(zoneId):
    return (zoneId >= DynamicZonesBegin) and (zoneId < DynamicZonesEnd)


def genDNAFileName(zoneId):
    if zoneId == ZoneIDs.CashbotHQ:
        return "phase_10/dna/cog_hq_cashbot_sz.dna"

    raise RuntimeError(f"unknown zone ID: {zoneId}")


def getLoaderName(zoneId):
    suffix = zoneId % 1000

    if suffix >= 500:
        suffix -= 500

    if isCogHQZone(zoneId):
        loaderName = "cogHQLoader"
    elif suffix < 100:
        loaderName = "safeZoneLoader"
    else:
        loaderName = "townLoader"

    assert zoneUtilNotify.debug("getLoaderName(zoneId=" + str(zoneId) + ") returning " + loaderName)
    assert loaderName
    return loaderName


def getBranchLoaderName(zoneId):
    """Convert to a branch zone ID before getting loader name."""
    return getLoaderName(getBranchZone(zoneId))


def getSuitWhereName(zoneId):
    where = getWhereName(zoneId, 0)
    assert zoneUtilNotify.debug("getWhereName(zoneId=" + str(zoneId) + ") returning " + where)
    assert where
    return where


def getToonWhereName(zoneId):
    where = getWhereName(zoneId, 1)
    assert zoneUtilNotify.debug("getWhereName(zoneId=" + str(zoneId) + ") returning " + where)
    assert where
    return where


def isPlayground(zoneId):
    whereName = getWhereName(zoneId, False)
    if whereName == "cogHQExterior":
        return True

    return zoneId % 1000 == 0 and zoneId < DynamicZonesBegin


def getWhereName(zoneId, isToon):
    suffix = zoneId % 1000
    suffix = suffix - (suffix % 100)

    where = None
    if isCogHQZone(zoneId):
        if suffix == 0:
            where = "cogHQExterior"
        elif suffix == 100:
            where = "cogHQLobby"
    elif suffix == 0:
        where = "playground"
    elif suffix >= 500:
        where = "toonInterior" if isToon else "suitInterior"
    else:
        where = "street"
    assert where, f"Invalid zone ID: {zoneId}"
    return where


def getBranchZone(zoneId):
    branchId = zoneId - (zoneId % 100)
    if not isCogHQZone(zoneId) and (zoneId % 1000) >= 500:
        branchId -= 500
    assert zoneUtilNotify.debug("getBranchZone(zoneId=" + str(zoneId) + ") returning " + str(branchId))
    return branchId


def getHoodId(zoneId):
    return zoneId - (zoneId % 1000)


def getSafeZoneId(zoneId):
    """returns hoodId of nearest playground; maps HQ zones to their
    closest safezone"""
    return getHoodId(zoneId)


def isInterior(zoneId):
    r = (zoneId % 1000) >= 500
    assert zoneUtilNotify.debug("isInterior(zoneId=" + str(zoneId) + ") returning " + str(r))
    return r
