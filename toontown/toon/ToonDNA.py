import random

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from .ClothingGlobals import *

notify = directNotify.newCategory("ToonDNA")
toonSpeciesTypes = ["d", "c", "h", "m", "r", "f", "p", "b", "s"]
toonHeadTypes = [
    "dls",
    "dss",
    "dsl",
    "dll",
    "cls",
    "css",
    "csl",
    "cll",
    "hls",
    "hss",
    "hsl",
    "hll",
    "mls",
    "mss",
    "rls",
    "rss",
    "rsl",
    "rll",
    "fls",
    "fss",
    "fsl",
    "fll",
    "pls",
    "pss",
    "psl",
    "pll",
    "bls",
    "bss",
    "bsl",
    "bll",
    "sls",
    "sss",
    "ssl",
    "sll",
]


def getHeadList(species):
    headList = []
    for head in toonHeadTypes:
        if head[0] == species:
            headList.append(head)

    return headList


def getHeadStartIndex(species):
    for head in toonHeadTypes:
        if head[0] == species:
            return toonHeadTypes.index(head)


def getSpecies(head):
    for species in toonSpeciesTypes:
        if species == head[0]:
            return species


def getSpeciesName(head):
    species = getSpecies(head)
    if species == "d":
        speciesName = "dog"
    elif species == "c":
        speciesName = "cat"
    elif species == "h":
        speciesName = "horse"
    elif species == "m":
        speciesName = "mouse"
    elif species == "r":
        speciesName = "rabbit"
    elif species == "f":
        speciesName = "duck"
    elif species == "p":
        speciesName = "monkey"
    elif species == "b":
        speciesName = "bear"
    elif species == "s":
        speciesName = "pig"
    else:
        raise ValueError(f"Unknown species {species}")
    return speciesName


# 8 species with 4 heads, mice with 2 heads
allToonHeadAnimalIndices = list(range(8 * 4 + 2))
toonTorsoTypes = ["ss", "ms", "ls", "sd", "md", "ld", "s", "m", "l"]
toonLegTypes = ["s", "m", "l"]


def getRandomTop(gender, tailorId=MAKE_A_TOON, generator=None):
    if generator == None:
        generator = random
    collection = TailorCollections[tailorId]
    if gender == "m":
        style = generator.choice(collection[BOY_SHIRTS])
    else:
        style = generator.choice(collection[GIRL_SHIRTS])
    styleList = ShirtStyles[style]
    colors = generator.choice(styleList[2])
    return (styleList[0], colors[0], styleList[1], colors[1])


def getRandomBottom(gender, tailorId=MAKE_A_TOON, generator=None, girlBottomType=None):
    if generator == None:
        generator = random
    collection = TailorCollections[tailorId]
    if gender == "m":
        style = generator.choice(collection[BOY_SHORTS])
    elif girlBottomType is None:
        style = generator.choice(collection[GIRL_BOTTOMS])
    elif girlBottomType == SKIRT:
        skirtCollection = [
            style for style in collection[GIRL_BOTTOMS] if GirlBottoms[BottomStyles[style][0]][1] == SKIRT
        ]
        style = generator.choice(skirtCollection)
    elif girlBottomType == SHORTS:
        shortsCollection = [
            style for style in collection[GIRL_BOTTOMS] if GirlBottoms[BottomStyles[style][0]][1] == SHORTS
        ]
        style = generator.choice(shortsCollection)
    else:
        notify.error("Bad girlBottomType: %s" % girlBottomType)
    styleList = BottomStyles[style]
    color = generator.choice(styleList[1])
    return (styleList[0], color)


def getRandomizedTops(gender, tailorId=MAKE_A_TOON, generator=None):
    if generator == None:
        generator = random
    collection = TailorCollections[tailorId]
    if gender == "m":
        collection = collection[BOY_SHIRTS][:]
    else:
        collection = collection[GIRL_SHIRTS][:]
    tops = []
    generator.shuffle(collection)
    for style in collection:
        colors = ShirtStyles[style][2][:]
        generator.shuffle(colors)
        for color in colors:
            tops.append((ShirtStyles[style][0], color[0], ShirtStyles[style][1], color[1]))

    return tops


def getRandomizedBottoms(gender, tailorId=MAKE_A_TOON, generator=None):
    if generator == None:
        generator = random
    collection = TailorCollections[tailorId]
    if gender == "m":
        collection = collection[BOY_SHORTS][:]
    else:
        collection = collection[GIRL_BOTTOMS][:]
    bottoms = []
    generator.shuffle(collection)
    for style in collection:
        colors = BottomStyles[style][1][:]
        generator.shuffle(colors)
        for color in colors:
            bottoms.append((BottomStyles[style][0], color))

    return bottoms


allColorsList = [
    VBase4(1.0, 1.0, 1.0, 1.0),
    VBase4(0.96875, 0.691406, 0.699219, 1.0),
    VBase4(0.933594, 0.265625, 0.28125, 1.0),
    VBase4(0.863281, 0.40625, 0.417969, 1.0),
    VBase4(0.710938, 0.234375, 0.4375, 1.0),
    VBase4(0.570312, 0.449219, 0.164062, 1.0),
    VBase4(0.640625, 0.355469, 0.269531, 1.0),
    VBase4(0.996094, 0.695312, 0.511719, 1.0),
    VBase4(0.832031, 0.5, 0.296875, 1.0),
    VBase4(0.992188, 0.480469, 0.167969, 1.0),
    VBase4(0.996094, 0.898438, 0.320312, 1.0),
    VBase4(0.996094, 0.957031, 0.597656, 1.0),
    VBase4(0.855469, 0.933594, 0.492188, 1.0),
    VBase4(0.550781, 0.824219, 0.324219, 1.0),
    VBase4(0.242188, 0.742188, 0.515625, 1.0),
    VBase4(0.304688, 0.96875, 0.402344, 1.0),
    VBase4(0.433594, 0.90625, 0.835938, 1.0),
    VBase4(0.347656, 0.820312, 0.953125, 1.0),
    VBase4(0.191406, 0.5625, 0.773438, 1.0),
    VBase4(0.558594, 0.589844, 0.875, 1.0),
    VBase4(0.285156, 0.328125, 0.726562, 1.0),
    VBase4(0.460938, 0.378906, 0.824219, 1.0),
    VBase4(0.546875, 0.28125, 0.75, 1.0),
    VBase4(0.726562, 0.472656, 0.859375, 1.0),
    VBase4(0.898438, 0.617188, 0.90625, 1.0),
    VBase4(0.7, 0.7, 0.8, 1.0),
    VBase4(0.3, 0.3, 0.35, 1.0),
]
defaultBoyColorList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
defaultGirlColorList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
allColorsListApproximations = [
    VBase4(round(x[0], 3), round(x[1], 3), round(x[2], 3), round(x[3], 3)) for x in allColorsList
]
allowedColors = set([allColorsListApproximations[x] for x in set(defaultBoyColorList + defaultGirlColorList + [26])])


class ToonDNA:
    def __init__(self, str=None, type=None, dna=None, r=None, b=None, g=None):
        if str != None:
            self.makeFromNetString(str)
        elif type != None:
            if type == "t":
                if dna == None:
                    self.newToonRandom(r, g, b)
                else:
                    self.newToonFromProperties(*dna.asTuple())
        else:
            self.type = "u"
        self.cache = ()
        return

    def clone(self):
        d = ToonDNA()
        d.makeFromNetString(self.makeNetString())
        return d

    def makeNetString(self):
        dg = PyDatagram()
        dg.addFixedString(self.type, 1)
        if self.type == "t":
            headIndex = toonHeadTypes.index(self.head)
            torsoIndex = toonTorsoTypes.index(self.torso)
            legsIndex = toonLegTypes.index(self.legs)
            dg.addUint8(headIndex)
            dg.addUint8(torsoIndex)
            dg.addUint8(legsIndex)
            if self.gender == "m":
                dg.addUint8(1)
            else:
                dg.addUint8(0)
            dg.addUint8(self.topTex)
            dg.addUint8(self.topTexColor)
            dg.addUint8(self.sleeveTex)
            dg.addUint8(self.sleeveTexColor)
            dg.addUint8(self.botTex)
            dg.addUint8(self.botTexColor)
            dg.addUint8(self.armColor)
            dg.addUint8(self.gloveColor)
            dg.addUint8(self.legColor)
            dg.addUint8(self.headColor)
        elif self.type == "u":
            notify.error("undefined avatar")
        else:
            notify.error("unknown avatar type: ", self.type)
        return dg.getMessage()

    @staticmethod
    def isValidNetString(string):
        dg = PyDatagram(string)
        dgi = PyDatagramIterator(dg)
        if dgi.getRemainingSize() != 15:
            return False
        type = dgi.getFixedString(1)
        if type not in ("t",):
            return False
        headIndex = dgi.getUint8()
        torsoIndex = dgi.getUint8()
        legsIndex = dgi.getUint8()
        if headIndex >= len(toonHeadTypes):
            return False
        if torsoIndex >= len(toonTorsoTypes):
            return False
        if legsIndex >= len(toonLegTypes):
            return False
        gender = dgi.getUint8()
        if gender == 1:
            gender = "m"
        else:
            gender = "f"
        topTex = dgi.getUint8()
        topTexColor = dgi.getUint8()
        sleeveTex = dgi.getUint8()
        sleeveTexColor = dgi.getUint8()
        botTex = dgi.getUint8()
        botTexColor = dgi.getUint8()
        armColor = dgi.getUint8()
        gloveColor = dgi.getUint8()
        legColor = dgi.getUint8()
        headColor = dgi.getUint8()
        if topTex >= len(Shirts):
            return False
        if topTexColor >= len(ClothesColors):
            return False
        if sleeveTex >= len(Sleeves):
            return False
        if sleeveTexColor >= len(ClothesColors):
            return False
        if botTex >= (len(BoyShorts) if gender == "m" else len(GirlBottoms)):
            return False
        if botTexColor >= len(ClothesColors):
            return False
        if armColor >= len(allColorsList):
            return False
        if gloveColor != 0:
            return False
        if legColor >= len(allColorsList):
            return False
        if headColor >= len(allColorsList):
            return False
        return True

    def makeFromNetString(self, string):
        dg = PyDatagram(string)
        dgi = PyDatagramIterator(dg)
        self.type = dgi.getFixedString(1)
        if self.type == "t":
            headIndex = dgi.getUint8()
            torsoIndex = dgi.getUint8()
            legsIndex = dgi.getUint8()
            self.head = toonHeadTypes[headIndex]
            self.torso = toonTorsoTypes[torsoIndex]
            self.legs = toonLegTypes[legsIndex]
            gender = dgi.getUint8()
            if gender == 1:
                self.gender = "m"
            else:
                self.gender = "f"
            self.topTex = dgi.getUint8()
            self.topTexColor = dgi.getUint8()
            self.sleeveTex = dgi.getUint8()
            self.sleeveTexColor = dgi.getUint8()
            self.botTex = dgi.getUint8()
            self.botTexColor = dgi.getUint8()
            self.armColor = dgi.getUint8()
            self.gloveColor = dgi.getUint8()
            self.legColor = dgi.getUint8()
            self.headColor = dgi.getUint8()
        else:
            notify.error("unknown avatar type: ", self.type)
        return None

    def defaultColor(self):
        return 25

    def __defaultColors(self):
        color = self.defaultColor()
        self.armColor = color
        self.gloveColor = 0
        self.legColor = color
        self.headColor = color

    def newToon(self, dna, color=None):
        if len(dna) == 4:
            self.type = "t"
            self.head = dna[0]
            self.torso = dna[1]
            self.legs = dna[2]
            self.gender = dna[3]
            self.topTex = 0
            self.topTexColor = 0
            self.sleeveTex = 0
            self.sleeveTexColor = 0
            self.botTex = 0
            self.botTexColor = 0
            if color == None:
                color = self.defaultColor()
            self.armColor = color
            self.legColor = color
            self.headColor = color
            self.gloveColor = 0
        else:
            notify.error("tuple must be in format ('%s', '%s', '%s', '%s')")
        return

    def newToonFromProperties(
        self,
        head,
        torso,
        legs,
        gender,
        armColor,
        gloveColor,
        legColor,
        headColor,
        topTexture,
        topTextureColor,
        sleeveTexture,
        sleeveTextureColor,
        bottomTexture,
        bottomTextureColor,
    ):
        self.type = "t"
        self.head = head
        self.torso = torso
        self.legs = legs
        self.gender = gender
        self.armColor = armColor
        self.gloveColor = gloveColor
        self.legColor = legColor
        self.headColor = headColor
        self.topTex = topTexture
        self.topTexColor = topTextureColor
        self.sleeveTex = sleeveTexture
        self.sleeveTexColor = sleeveTextureColor
        self.botTex = bottomTexture
        self.botTexColor = bottomTextureColor

    def updateToonProperties(
        self,
        head=None,
        torso=None,
        legs=None,
        gender=None,
        armColor=None,
        gloveColor=None,
        legColor=None,
        headColor=None,
        topTexture=None,
        topTextureColor=None,
        sleeveTexture=None,
        sleeveTextureColor=None,
        bottomTexture=None,
        bottomTextureColor=None,
        shirt=None,
        bottom=None,
    ):
        if head:
            self.head = head
        if torso:
            self.torso = torso
        if legs:
            self.legs = legs
        if gender:
            self.gender = gender
        if armColor:
            self.armColor = armColor
        if gloveColor:
            self.gloveColor = gloveColor
        if legColor:
            self.legColor = legColor
        if headColor:
            self.headColor = headColor
        if topTexture:
            self.topTex = topTexture
        if topTextureColor:
            self.topTexColor = topTextureColor
        if sleeveTexture:
            self.sleeveTex = sleeveTexture
        if sleeveTextureColor:
            self.sleeveTexColor = sleeveTextureColor
        if bottomTexture:
            self.botTex = bottomTexture
        if bottomTextureColor:
            self.botTexColor = bottomTextureColor
        if shirt:
            str, colorIndex = shirt
            defn = ShirtStyles[str]
            self.topTex = defn[0]
            self.topTexColor = defn[2][colorIndex][0]
            self.sleeveTex = defn[1]
            self.sleeveTexColor = defn[2][colorIndex][1]
        if bottom:
            str, colorIndex = bottom
            defn = BottomStyles[str]
            self.botTex = defn[0]
            self.botTexColor = defn[1][colorIndex]

    def newToonRandom(self, seed=None, gender="m", npc=0, stage=None):
        if seed:
            generator = random.Random()
            generator.seed(seed)
        else:
            generator = random
        self.type = "t"
        self.legs = generator.choice(toonLegTypes + ["m", "l", "l", "l"])
        self.gender = gender
        if not npc:
            if stage == MAKE_A_TOON:
                animalIndicesToUse = allToonHeadAnimalIndices
                animal = generator.choice(animalIndicesToUse)
                self.head = toonHeadTypes[animal]
            else:
                self.head = generator.choice(toonHeadTypes)
        else:
            self.head = generator.choice(toonHeadTypes[:22])
        top, topColor, sleeve, sleeveColor = getRandomTop(gender, generator=generator)
        bottom, bottomColor = getRandomBottom(gender, generator=generator)
        if gender == "m":
            self.torso = generator.choice(toonTorsoTypes[:3])
            self.topTex = top
            self.topTexColor = topColor
            self.sleeveTex = sleeve
            self.sleeveTexColor = sleeveColor
            self.botTex = bottom
            self.botTexColor = bottomColor
            color = generator.choice(defaultBoyColorList)
            self.armColor = color
            self.legColor = color
            self.headColor = color
        else:
            self.torso = generator.choice(toonTorsoTypes[:6])
            self.topTex = top
            self.topTexColor = topColor
            self.sleeveTex = sleeve
            self.sleeveTexColor = sleeveColor
            if self.torso[1] == "d":
                bottom, bottomColor = getRandomBottom(gender, generator=generator, girlBottomType=SKIRT)
            else:
                bottom, bottomColor = getRandomBottom(gender, generator=generator, girlBottomType=SHORTS)
            self.botTex = bottom
            self.botTexColor = bottomColor
            color = generator.choice(defaultGirlColorList)
            self.armColor = color
            self.legColor = color
            self.headColor = color
        self.gloveColor = 0

    def asTuple(self):
        return (
            self.head,
            self.torso,
            self.legs,
            self.gender,
            self.armColor,
            self.gloveColor,
            self.legColor,
            self.headColor,
            self.topTex,
            self.topTexColor,
            self.sleeveTex,
            self.sleeveTexColor,
            self.botTex,
            self.botTexColor,
        )

    def getType(self):
        if self.type == "t":
            type = self.getAnimal()
        else:
            notify.error("Invalid DNA type: ", self.type)
        return type

    def getAnimal(self):
        if self.head[0] == "d":
            return "dog"
        elif self.head[0] == "c":
            return "cat"
        elif self.head[0] == "m":
            return "mouse"
        elif self.head[0] == "h":
            return "horse"
        elif self.head[0] == "r":
            return "rabbit"
        elif self.head[0] == "f":
            return "duck"
        elif self.head[0] == "p":
            return "monkey"
        elif self.head[0] == "b":
            return "bear"
        elif self.head[0] == "s":
            return "pig"
        else:
            notify.error("unknown headStyle: ", self.head[0])

    def getGender(self):
        return self.gender

    def getArmColor(self):
        try:
            return allColorsList[self.armColor]
        except:
            return allColorsList[0]

    def getLegColor(self):
        try:
            return allColorsList[self.legColor]
        except:
            return allColorsList[0]

    def getHeadColor(self):
        try:
            return allColorsList[self.headColor]
        except:
            return allColorsList[0]

    def getGloveColor(self):
        try:
            return allColorsList[self.gloveColor]
        except:
            return allColorsList[0]
