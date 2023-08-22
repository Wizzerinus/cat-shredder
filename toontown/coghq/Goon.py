import math

from panda3d.core import Point3

from otp.avatar import Avatar
from toontown.toonbase.globals.TTGlobalsAvatars import AvatarTypes, GoonHatColors, GoonModelDict
from toontown.toonbase.globals.TTGlobalsRender import PieBitmask


class Goon(Avatar.Avatar):
    """Goon class:"""

    Goon_initialized = False

    def __init__(self):
        if self.Goon_initialized:
            return

        self.Goon_initialized = True
        Avatar.Avatar.__init__(self)

        self.ignore("nametagAmbientLightChanged")

        self.hFov = 70
        self.attackRadius = 15
        self.strength = 15
        self.velocity = 4
        self.scale = 1.0
        self.avatarType = AvatarTypes.GOON
        self.type = "n"

    def initGoon(self, dnaName):
        self.type = dnaName
        self.generateGoon()
        self.createHead()
        self.find("**/actorGeom").setH(180)

    def generateGoon(self):
        dna = self.type
        filePrefix, animList = GoonModelDict[dna]
        self.loadModel(f"{filePrefix}-zero")

        animDict = {}
        for anim in animList:
            animDict[anim[0]] = filePrefix + anim[1]

        self.loadAnims(animDict)

    def initializeBodyCollisions(self, collIdStr):
        Avatar.Avatar.initializeBodyCollisions(self, collIdStr)

        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | PieBitmask)

    def createHead(self):
        self.headHeight = 3.0

        head = self.find("**/joint35")
        if head.isEmpty():
            head = self.find("**/joint40")
        self.hat = self.find("**/joint8")
        parentNode = head.getParent()
        self.head = parentNode.attachNewNode("headRotate")
        head.reparentTo(self.head)
        self.hat.reparentTo(self.head)

        if self.type == "n":
            self.hat.find("**/security_hat").hide()
        elif self.type == "p":
            self.hat.find("**/hard_hat").hide()

        self.eye = self.find("**/eye")
        self.eye.setColorScale(1, 1, 1, 1)
        self.eye.setColor(1, 1, 0, 1)

        self.radar = None

    def scaleRadar(self):
        if self.radar:
            self.radar.removeNode()

        self.radar = self.eye.attachNewNode("radar")

        model = loader.loadModel("phase_9/models/cogHQ/alphaCone2")
        beam = self.radar.attachNewNode("beam")
        transformNode = model.find("**/transform")
        transformNode.getChildren().reparentTo(beam)

        self.radar.setPos(0, -0.5, 0.4)
        self.radar.setTransparency(1)
        self.radar.setDepthWrite(0)

        self.halfFov = self.hFov / 2.0
        fovRad = self.halfFov * math.pi / 180.0
        self.cosHalfFov = math.cos(fovRad)
        kw = math.tan(fovRad) * self.attackRadius / 10.5

        kl = math.sqrt(self.attackRadius * self.attackRadius + 9.0) / 25.0

        beam.setScale(kw / self.scale, kl / self.scale, kw / self.scale)
        beam.setHpr(0, self.halfFov, 0)

        p = self.radar.getRelativePoint(beam, Point3(0, -6, -1.8))
        self.radar.setSz(-3.5 / p[2])

        self.radar.flattenMedium()

        self.radar.setColor(1, 1, 1, 0.2)

    def colorHat(self):
        colorValues = GoonHatColors.get(self.type)
        if not colorValues:
            return

        try:
            colorValue = max(color for color in colorValues if color[0] <= self.strength)[1]
        except ValueError:
            colorValue = colorValues[0][1]

        if colorValue is None:
            self.hat.clearColorScale()
        else:
            self.hat.setColorScale(colorValue)
