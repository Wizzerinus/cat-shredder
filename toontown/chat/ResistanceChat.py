import random

from direct.interval.IntervalGlobal import *
from panda3d.core import *

from toontown.toonbase import TTLocalizer
from toontown.toonbase.PropPool import createParticleEffect

TTL = TTLocalizer
EFFECT_RADIUS = 30
RESISTANCE_TOONUP = 0
resistanceMenu = [RESISTANCE_TOONUP]
resistanceDict = {
    RESISTANCE_TOONUP: {
        "menuName": TTL.ResistanceToonupMenu,
        "itemText": TTL.ResistanceToonupItem,
        "chatText": TTL.ResistanceToonupChat,
        "values": [10, 20, 40, 80, -1],
        "items": [0, 1, 2, 3, 4],
    },
}


def encodeId(menuIndex, itemIndex):
    textId = menuIndex * 100
    textId += resistanceDict[menuIndex]["items"][itemIndex]
    return textId


def decodeId(textId):
    menuIndex = int(textId / 100)
    itemIndex = textId % 100
    return (menuIndex, itemIndex)


def validateId(textId):
    if textId < 0:
        return 0
    menuIndex, itemIndex = decodeId(textId)
    if menuIndex not in resistanceDict:
        return 0
    if itemIndex >= len(resistanceDict[menuIndex]["values"]):
        return 0
    return 1


def getItems(menuIndex):
    return resistanceDict[menuIndex]["items"]


def getMenuName(textId):
    menuIndex, itemIndex = decodeId(textId)
    return resistanceDict[menuIndex]["menuName"]


def getItemText(textId):
    menuIndex, itemIndex = decodeId(textId)
    value = resistanceDict[menuIndex]["values"][itemIndex]
    text = resistanceDict[menuIndex]["itemText"]
    if menuIndex is RESISTANCE_TOONUP:
        if value == -1:
            value = TTL.ResistanceToonupItemMax
    elif menuIndex is RESISTANCE_RESTOCK:
        value = resistanceDict[menuIndex]["extra"][itemIndex]
    return text % str(value)


def getChatText(textId):
    menuIndex, itemIndex = decodeId(textId)
    return resistanceDict[menuIndex]["chatText"]


def getItemValue(textId):
    menuIndex, itemIndex = decodeId(textId)
    return resistanceDict[menuIndex]["values"][itemIndex]


def getRandomId():
    menuIndex = random.choice(resistanceMenu)
    itemIndex = random.choice(getItems(menuIndex))
    return encodeId(menuIndex, itemIndex)


def doEffect(textId, speakingToon, nearbyToons):
    menuIndex, itemIndex = decodeId(textId)
    if menuIndex == RESISTANCE_TOONUP:
        effect = createParticleEffect("resistanceEffectSparkle")
        fadeColor = VBase4(1, 0.5, 1, 1)
    else:
        return
    recolorToons = Parallel()
    for toonId in nearbyToons:
        toon = base.cr.doId2do.get(toonId)
        if toon and not toon.ghostMode:
            i = Sequence(
                toon.doToonColorScale(fadeColor, 0.3),
                toon.doToonColorScale(toon.defaultColorScale, 0.3),
                Func(toon.restoreDefaultColorScale),
            )
            recolorToons.append(i)

    i = Parallel(
        ParticleInterval(effect, speakingToon, worldRelative=0, duration=3, cleanup=True),
        Sequence(Wait(0.2), recolorToons),
        autoFinish=1,
    )
    i.start()
