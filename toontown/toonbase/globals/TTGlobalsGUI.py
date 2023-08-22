NametagFontPaths = [
    "phase_3/models/fonts/AnimGothic",
    "phase_3/models/fonts/Aftershock",
    "phase_3/models/fonts/JiggeryPokery",
    "phase_3/models/fonts/Ironwork",
    "phase_3/models/fonts/HastyPudding",
    "phase_3/models/fonts/Comedy",
    "phase_3/models/fonts/Humanist",
    "phase_3/models/fonts/Portago",
    "phase_3/models/fonts/Musicals",
    "phase_3/models/fonts/Scurlock",
    "phase_3/models/fonts/Danger",
    "phase_3/models/fonts/Alie",
    "phase_3/models/fonts/OysterBar",
    "phase_3/models/fonts/RedDogSaloon",
]


class FontPaths:
    Interface = "phase_3/models/fonts/ImpressBT.ttf"
    Toon = "phase_3/models/fonts/ImpressBT.ttf"
    Suit = "phase_3/models/fonts/vtRemingtonPortable.ttf"
    Sign = "phase_3/models/fonts/MickeyFont"
    Minnie = "phase_3/models/fonts/Minnie.ttf"
    BuildingNametag = "phase_3/models/fonts/MickeyFont"
    Competition = "phase_3/models/fonts/hemiheadreg.ttf"


LoadedFonts = {}


def getFont(name, **kw):
    if name not in LoadedFonts:
        LoadedFonts[name] = loader.loadFont(name, **kw)
    return LoadedFonts[name]


def getNametagFont(index):
    return getFont(NametagFontPaths[index])


def getInterfaceFont():
    return getFont(FontPaths.Interface, lineHeight=1)


def getToonFont():
    return getFont(FontPaths.Toon, lineHeight=1)


def getSuitFont():
    return getFont(FontPaths.Suit, pixelsPerUnit=40, spaceAdvance=0.25, lineHeight=1)


def getSignFont():
    return getFont(FontPaths.Sign, lineHeight=1)


def getMinnieFont():
    return getFont(FontPaths.Minnie)


def getBuildingNametagFont():
    return getFont(FontPaths.BuildingNametag)


def getCompetitionFont():
    return getFont(FontPaths.Competition)
