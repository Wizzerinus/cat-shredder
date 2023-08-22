from direct.interval.IntervalGlobal import *
from direct.task.Task import Task
from panda3d.core import *
from panda3d.direct import HideInterval, ShowInterval
from panda3d.otp import *

from otp.avatar import Avatar
from otp.avatar.Avatar import teleportNotify
from toontown.distributed import DelayDelete
from toontown.toon import TTEmote as Emote
from toontown.toonbase import TTLocalizer
from . import AccessoryGlobals
from . import Motion, ToonDNA
from .ToonHead import *
from ..toonbase.globals.TTGlobalsAvatars import *
from ..toonbase.globals.TTGlobalsChat import CheesyEffects
from ..toonbase.globals.TTGlobalsGUI import getToonFont
from ..toonbase.globals.TTGlobalsMovement import *
from ..toonbase.globals.TTGlobalsRender import PieBitmask


def teleportDebug(requestStatus, msg, onlyIfToAv=True):
    if teleportNotify.getDebug():
        teleport = "teleport"
        if "how" in requestStatus and requestStatus["how"][: len(teleport)] == teleport:
            if not onlyIfToAv or "avId" in requestStatus and requestStatus["avId"] > 0:
                teleportNotify.debug(msg)


SLEEP_STRING = TTLocalizer.ToonSleepString
DialogueSoundFiles = {}
LegsAnimDict = {}
TorsoAnimDict = {}
HeadAnimDict = {}
dialogueFiles = ("short", "med", "long", "question", "exclaim", "howl")

AnimList = (
    (3, "neutral", "neutral"),
    (3, "run", "run"),
    (3.5, "walk", "walk"),
    (3.5, "teleport", "teleport"),
    (3.5, "book", "book"),
    (3.5, "jump", "jump"),
    (3.5, "running-jump", "running-jump"),
    (3.5, "jump-squat", "jump-zstart"),
    (3.5, "jump-idle", "jump-zhang"),
    (3.5, "jump-land", "jump-zend"),
    (3.5, "running-jump-squat", "leap_zstart"),
    (3.5, "running-jump-idle", "leap_zhang"),
    (3.5, "running-jump-land", "leap_zend"),
    (3.5, "pushbutton", "press-button"),
    (3.5, "throw", "pie-throw"),
    (3.5, "victory", "victory-dance"),
    (3.5, "sidestep-left", "sidestep-left"),
    (3.5, "conked", "conked"),
    (3.5, "cringe", "cringe"),
    (3.5, "wave", "wave"),
    (3.5, "shrug", "shrug"),
    (3.5, "angry", "angry"),
    (3.5, "tutorial-neutral", "tutorial-neutral"),
    (3.5, "left-point", "left-point"),
    (3.5, "right-point", "right-point"),
    (3.5, "right-point-start", "right-point-start"),
    (3.5, "give-props", "give-props"),
    (3.5, "give-props-start", "give-props-start"),
    (3.5, "right-hand", "right-hand"),
    (3.5, "right-hand-start", "right-hand-start"),
    (3.5, "duck", "duck"),
    (3.5, "sidestep-right", "jump-back-right"),
    (3.5, "periscope", "periscope"),
    (4, "sit", "sit"),
    (4, "sit-start", "intoSit"),
    (4, "swim", "swim"),
    (4, "tug-o-war", "tug-o-war"),
    (4, "sad-walk", "losewalk"),
    (4, "sad-neutral", "sad-neutral"),
    (4, "up", "up"),
    (4, "down", "down"),
    (4, "left", "left"),
    (4, "right", "right"),
    (4, "applause", "applause"),
    (4, "confused", "confused"),
    (4, "bow", "bow"),
    (4, "curtsy", "curtsy"),
    (4, "bored", "bored"),
    (4, "think", "think"),
    (4, "battlecast", "fish"),
    (4, "cast", "cast"),
    (4, "castlong", "castlong"),
    (4, "fish-end", "fishEND"),
    (4, "fish-neutral", "fishneutral"),
    (4, "fish-again", "fishAGAIN"),
    (4, "reel", "reel"),
    (4, "reel-H", "reelH"),
    (4, "reel-neutral", "reelneutral"),
    (4, "pole", "pole"),
    (4, "pole-neutral", "poleneutral"),
    (4, "slip-forward", "slip-forward"),
    (4, "slip-backward", "slip-backward"),
    (4, "catch-neutral", "gameneutral"),
    (4, "catch-run", "gamerun"),
    (4, "catch-eatneutral", "eat_neutral"),
    (4, "catch-eatnrun", "eatnrun"),
    (4, "catch-intro-throw", "gameThrow"),
    (4, "swing", "swing"),
    (4, "pet-start", "petin"),
    (4, "pet-loop", "petloop"),
    (4, "pet-end", "petend"),
    (4, "scientistJealous", "scientistJealous"),
    (4, "scientistEmcee", "scientistEmcee"),
    (4, "scientistWork", "scientistWork"),
    (4, "scientistGame", "scientistGame"),
    (5, "water-gun", "water-gun"),
    (5, "hold-bottle", "hold-bottle"),
    (5, "firehose", "firehose"),
    (5, "spit", "spit"),
    (5, "tickle", "tickle"),
    (5, "smooch", "smooch"),
    (5, "happy-dance", "happy-dance"),
    (5, "sprinkle-dust", "sprinkle-dust"),
    (5, "juggle", "juggle"),
    (5, "climb", "climb"),
    (5, "sound", "shout"),
    (5, "toss", "toss"),
    (5, "hold-magnet", "hold-magnet"),
    (5, "hypnotize", "hypnotize"),
    (5, "struggle", "struggle"),
    (5, "lose", "lose"),
    (5, "melt", "melt"),
    (5.5, "takePhone", "takePhone"),
    (5.5, "phoneNeutral", "phoneNeutral"),
    (5.5, "phoneBack", "phoneBack"),
    (5.5, "bank", "jellybeanJar"),
    (5.5, "callPet", "callPet"),
    (5.5, "feedPet", "feedPet"),
    (5.5, "start-dig", "into_dig"),
    (5.5, "loop-dig", "loop_dig"),
    (5.5, "water", "water"),
    (6, "headdown-putt", "headdown-putt"),
    (6, "into-putt", "into-putt"),
    (6, "loop-putt", "loop-putt"),
    (6, "rotateL-putt", "rotateL-putt"),
    (6, "rotateR-putt", "rotateR-putt"),
    (6, "swing-putt", "swing-putt"),
    (6, "look-putt", "look-putt"),
    (6, "lookloop-putt", "lookloop-putt"),
    (6, "bad-putt", "bad-putt"),
    (6, "badloop-putt", "badloop-putt"),
    (6, "good-putt", "good-putt"),
    (9, "push", "push"),
    (10, "leverReach", "leverReach"),
    (10, "leverPull", "leverPull"),
    (10, "leverNeutral", "leverNeutral"),
)
LegDict = {
    "s": "/models/char/tt_a_chr_dgs_shorts_legs_",
    "m": "/models/char/tt_a_chr_dgm_shorts_legs_",
    "l": "/models/char/tt_a_chr_dgl_shorts_legs_",
}
TorsoDict = {
    "s": "/models/char/dogSS_Naked-torso-",
    "m": "/models/char/dogMM_Naked-torso-",
    "l": "/models/char/dogLL_Naked-torso-",
    "ss": "/models/char/tt_a_chr_dgs_shorts_torso_",
    "ms": "/models/char/tt_a_chr_dgm_shorts_torso_",
    "ls": "/models/char/tt_a_chr_dgl_shorts_torso_",
    "sd": "/models/char/tt_a_chr_dgs_skirt_torso_",
    "md": "/models/char/tt_a_chr_dgm_skirt_torso_",
    "ld": "/models/char/tt_a_chr_dgl_skirt_torso_",
}


def compileGlobalAnimList():
    for phase, anim, filename in AnimList:
        for key in LegDict:
            LegsAnimDict.setdefault(key, {})
            file = f"phase_{phase}{LegDict[key]}{filename}"
            LegsAnimDict[key][anim] = file
        for key in TorsoDict:
            TorsoAnimDict.setdefault(key, {})
            file = f"phase_{phase}{TorsoDict[key]}{filename}"
            TorsoAnimDict[key][anim] = file
        for key in ["dss", "dsl", "dls", "dll"]:
            HeadAnimDict.setdefault(key, {})
            file = f"phase_{phase}{HeadDict[key]}{filename}"
            HeadAnimDict[key][anim] = file


def loadDialog():
    """
    Load the dialogue audio samples
    """
    if len(DialogueSoundFiles) > 0:
        return
    loadPath = "phase_3.5/audio/dial"
    species = ToonBodyScales
    sfx = loader.loadSfx([f"{loadPath}/AV_{x}_{y}.ogg" for x in species for y in dialogueFiles])
    for num, item in enumerate(species):
        DialogueSoundFiles[item] = sfx[num * len(dialogueFiles) : (num + 1) * len(dialogueFiles)]


def unloadDialog():
    DialogueSoundFiles.clear()


class Toon(Avatar.Avatar, ToonHead):
    notify = directNotify.newCategory("Toon")
    afkTimeout = ConfigVariableInt("afk-timeout", 600).value
    standWalkRunReverse = None

    def __init__(self):
        try:
            self.Toon_initialized
            return
        except:
            self.Toon_initialized = 1

        Avatar.Avatar.__init__(self)
        ToonHead.__init__(self)
        self.forwardSpeed = 0.0
        self.rotateSpeed = 0.0
        self.avatarType = "toon"
        self.motion = Motion.Motion(self)
        self.cheesyEffect = CheesyEffects.NORMAL
        self.setFont(getToonFont())
        self.effectTrack = None
        self.emoteTrack = None
        self.stunTrack = None
        self.rightHands = []
        self.rightHand = None
        self.leftHands = []
        self.leftHand = None
        self.soundTeleport = None
        self.headParts = []
        self.torsoParts = []
        self.hipsParts = []
        self.legsParts = []

        self.hat = 0, 0
        self.glasses = 0, 0
        self.backpack = 0, 0
        self.shoes = 0, 0
        self.__holeActors = None
        self.hatNodes = []
        self.glassesNodes = []
        self.backpackNodes = []
        self.shadowJoint = None

        self.animFSM = ClassicFSM(
            "Toon",
            [
                State("off", self.enterOff, self.exitOff),
                State("neutral", self.enterNeutral, self.exitNeutral),
                State("victory", self.enterVictory, self.exitVictory),
                State("Happy", self.enterHappy, self.exitHappy),
                State("Sad", self.enterSad, self.exitSad),
                State("Catching", self.enterCatching, self.exitCatching),
                State("CatchEating", self.enterCatchEating, self.exitCatchEating),
                State("Sleep", self.enterSleep, self.exitSleep),
                State("walk", self.enterWalk, self.exitWalk),
                State("jumpSquat", self.enterJumpSquat, self.exitJumpSquat),
                State("jump", self.enterJump, self.exitJump),
                State("jumpAirborne", self.enterJumpAirborne, self.exitJumpAirborne),
                State("jumpLand", self.enterJumpLand, self.exitJumpLand),
                State("run", self.enterRun, self.exitRun),
                State("swim", self.enterSwim, self.exitSwim),
                State("swimhold", self.enterSwimHold, self.exitSwimHold),
                State("dive", self.enterDive, self.exitDive),
                State("cringe", self.enterCringe, self.exitCringe),
                State("TeleportOut", self.enterTeleportOut, self.exitTeleportOut),
                State("Died", self.enterDied, self.exitDied),
                State("TeleportedOut", self.enterTeleportedOut, self.exitTeleportedOut),
                State("TeleportIn", self.enterTeleportIn, self.exitTeleportIn),
                State("Emote", self.enterEmote, self.exitEmote),
                State("SitStart", self.enterSitStart, self.exitSitStart),
                State("Sit", self.enterSit, self.exitSit),
                State("Push", self.enterPush, self.exitPush),
                State("Squish", self.enterSquish, self.exitSquish),
                State("FallDown", self.enterFallDown, self.exitFallDown),
                State("Flattened", self.enterFlattened, self.exitFlattened),
            ],
            "off",
            "off",
        )
        self.animFSM.enterInitialState()

    def stopAnimations(self):
        if hasattr(self, "animFSM"):
            if not self.animFSM.isInternalStateInFlux():
                self.animFSM.request("off")
            else:
                self.notify.warning(
                    "animFSM in flux, state=%s, not requesting off" % self.animFSM.getCurrentState().getName()
                )
        else:
            self.notify.warning("animFSM has been deleted")
        if self.effectTrack != None:
            self.effectTrack.finish()
            self.effectTrack = None
        if self.emoteTrack != None:
            self.emoteTrack.finish()
            self.emoteTrack = None
        if self.stunTrack != None:
            self.stunTrack.finish()
            self.stunTrack = None

    def delete(self):
        try:
            self.Toon_deleted
            return
        except:
            self.Toon_deleted = 1

        self.stopAnimations()
        self.rightHands = None
        self.rightHand = None
        self.leftHands = None
        self.leftHand = None
        self.headParts = None
        self.torsoParts = None
        self.hipsParts = None
        self.legsParts = None
        del self.animFSM

        del self.__holeActors
        self.soundTeleport = None
        self.motion.delete()
        self.motion = None
        Avatar.Avatar.delete(self)
        ToonHead.delete(self)

    def updateToonDNA(self, newDNA, fForce=0):
        self.style.gender = newDNA.getGender()
        oldDNA = self.style
        if fForce or newDNA.head != oldDNA.head:
            self.swapToonHead(newDNA.head)
        if fForce or newDNA.torso != oldDNA.torso:
            self.swapToonTorso(newDNA.torso, genClothes=0)
            self.loop("neutral")
        if fForce or newDNA.legs != oldDNA.legs:
            self.swapToonLegs(newDNA.legs)
        self.swapToonColor(newDNA)
        self.__swapToonClothes(newDNA)

    def setDNAString(self, dnaString):
        newDNA = ToonDNA.ToonDNA()
        newDNA.makeFromNetString(dnaString)
        if len(newDNA.torso) < 2:
            self.sendLogSuspiciousEvent("nakedToonDNA %s was requested" % newDNA.torso)
            newDNA.torso = newDNA.torso + "s"
        self.setDNA(newDNA)

    def setDNA(self, dna):
        if self.style:
            self.updateToonDNA(dna)
        else:
            self.style = dna
            self.generateToon()
            self.initializeDropShadow()
            self.initializeNametag3d()

    def parentToonParts(self):
        if self.hasLOD():
            for lodName in self.getLODNames():
                if not self.getPart("torso", lodName).find("**/def_head").isEmpty():
                    self.attach("head", "torso", "def_head", lodName)
                else:
                    self.attach("head", "torso", "joint_head", lodName)
                self.attach("torso", "legs", "joint_hips", lodName)

        else:
            self.attach("head", "torso", "joint_head")
            self.attach("torso", "legs", "joint_hips")

    def unparentToonParts(self):
        if self.hasLOD():
            for lodName in self.getLODNames():
                self.getPart("head", lodName).reparentTo(self.getLOD(lodName))
                self.getPart("torso", lodName).reparentTo(self.getLOD(lodName))
                self.getPart("legs", lodName).reparentTo(self.getLOD(lodName))

        else:
            self.getPart("head").reparentTo(self.getGeomNode())
            self.getPart("torso").reparentTo(self.getGeomNode())
            self.getPart("legs").reparentTo(self.getGeomNode())

    def setLODs(self):
        self.setLODNode()
        levelOneIn = ConfigVariableInt("lod1-in", 20).value
        levelOneOut = ConfigVariableInt("lod1-out", 0).value
        levelTwoIn = ConfigVariableInt("lod2-in", 80).value
        levelTwoOut = ConfigVariableInt("lod2-out", 20).value
        levelThreeIn = ConfigVariableInt("lod3-in", 280).value
        levelThreeOut = ConfigVariableInt("lod3-out", 80).value
        self.addLOD(1000, levelOneIn, levelOneOut)
        self.addLOD(500, levelTwoIn, levelTwoOut)
        self.addLOD(250, levelThreeIn, levelThreeOut)

    def generateToon(self):
        self.setLODs()
        self.generateToonLegs()
        self.generateToonHead()
        self.generateToonTorso()
        self.generateToonColor()
        self.parentToonParts()
        self.rescaleToon()
        self.resetHeight()
        self.setupToonNodes()

    def setupToonNodes(self):
        rightHand = NodePath("rightHand")
        self.rightHand = None
        self.rightHands = []
        leftHand = NodePath("leftHand")
        self.leftHands = []
        self.leftHand = None
        for lodName in self.getLODNames():
            hand = self.getPart("torso", lodName).find("**/joint_Rhold")
            if not self.getPart("torso", lodName).find("**/def_joint_right_hold").isEmpty():
                hand = self.getPart("torso", lodName).find("**/def_joint_right_hold")
            self.rightHands.append(hand)
            rightHand = rightHand.instanceTo(hand)
            if not self.getPart("torso", lodName).find("**/def_joint_left_hold").isEmpty():
                hand = self.getPart("torso", lodName).find("**/def_joint_left_hold")
            self.leftHands.append(hand)
            leftHand = leftHand.instanceTo(hand)
            if self.rightHand == None:
                self.rightHand = rightHand
            if self.leftHand == None:
                self.leftHand = leftHand

        self.headParts = self.findAllMatches("**/__Actor_head")
        self.legsParts = self.findAllMatches("**/__Actor_legs")
        self.hipsParts = self.legsParts.findAllMatches("**/joint_hips")
        self.torsoParts = self.hipsParts.findAllMatches("**/__Actor_torso")
        return

    def initializeBodyCollisions(self, collIdStr):
        Avatar.Avatar.initializeBodyCollisions(self, collIdStr)
        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | PieBitmask)

    def getHoleActors(self):
        if self.__holeActors:
            return self.__holeActors
        holeActor = Actor.Actor("phase_3.5/models/props/portal-mod", {"hole": "phase_3.5/models/props/portal-chan"})
        holeActor2 = Actor.Actor(other=holeActor)
        holeActor3 = Actor.Actor(other=holeActor)
        self.__holeActors = [holeActor, holeActor2, holeActor3]
        for ha in self.__holeActors:
            if hasattr(self, "uniqueName"):
                holeName = self.uniqueName("toon-portal")
            else:
                holeName = "toon-portal"
            ha.setName(holeName)

        return self.__holeActors

    def rescaleToon(self):
        animalStyle = self.style.getAnimal()
        bodyScale = ToonBodyScales[animalStyle]
        self.setAvatarScale(bodyScale)

    def getBodyScale(self):
        animalStyle = self.style.getAnimal()
        bodyScale = ToonBodyScales[animalStyle]
        return bodyScale

    def resetHeight(self):
        if hasattr(self, "style") and self.style:
            animal = self.style.getAnimal()
            bodyScale = ToonBodyScales[animal]
            shoulderHeight = (
                ToonLegHeights[self.style.legs] * bodyScale + ToonTorsoHeights[self.style.torso] * bodyScale
            )
            height = shoulderHeight + ToonHeadHeights[self.style.head]
            self.shoulderHeight = shoulderHeight
            self.setHeight(height)

    def generateToonLegs(self, copy=1):
        legStyle = self.style.legs
        filePrefix = LegDict.get(legStyle)
        if filePrefix is None:
            self.notify.error("unknown leg style: %s" % legStyle)
        self.loadModel("phase_3" + filePrefix + "1000", "legs", "1000", copy)
        self.loadModel("phase_3" + filePrefix + "500", "legs", "500", copy)
        self.loadModel("phase_3" + filePrefix + "250", "legs", "250", copy)
        if not copy:
            self.showPart("legs", "1000")
            self.showPart("legs", "500")
            self.showPart("legs", "250")
        self.loadAnims(LegsAnimDict[legStyle], "legs", "1000")
        self.loadAnims(LegsAnimDict[legStyle], "legs", "500")
        self.loadAnims(LegsAnimDict[legStyle], "legs", "250")
        self.findAllMatches("**/boots_short").stash()
        self.findAllMatches("**/boots_long").stash()
        self.findAllMatches("**/shoes").stash()
        return

    def swapToonLegs(self, legStyle, copy=1):
        self.unparentToonParts()
        self.removePart("legs", "1000")
        self.removePart("legs", "500")
        self.removePart("legs", "250")
        self.style.legs = legStyle
        self.generateToonLegs(copy)
        self.generateToonColor()
        self.parentToonParts()
        self.rescaleToon()
        self.resetHeight()
        self.shadowJoint = None
        self.initializeDropShadow()
        self.initializeNametag3d()

    def generateToonTorso(self, copy=1, genClothes=1):
        torsoStyle = self.style.torso
        filePrefix = TorsoDict.get(torsoStyle)
        if filePrefix is None:
            self.notify.error("unknown torso style: %s" % torsoStyle)
        self.loadModel("phase_3" + filePrefix + "1000", "torso", "1000", copy)
        if len(torsoStyle) == 1:
            self.loadModel("phase_3" + filePrefix + "1000", "torso", "500", copy)
            self.loadModel("phase_3" + filePrefix + "1000", "torso", "250", copy)
        else:
            self.loadModel("phase_3" + filePrefix + "500", "torso", "500", copy)
            self.loadModel("phase_3" + filePrefix + "250", "torso", "250", copy)
        if not copy:
            self.showPart("torso", "1000")
            self.showPart("torso", "500")
            self.showPart("torso", "250")
        self.loadAnims(TorsoAnimDict[torsoStyle], "torso", "1000")
        self.loadAnims(TorsoAnimDict[torsoStyle], "torso", "500")
        self.loadAnims(TorsoAnimDict[torsoStyle], "torso", "250")
        if genClothes == 1 and not len(torsoStyle) == 1:
            self.generateToonClothes()
        return

    def swapToonTorso(self, torsoStyle, copy=1, genClothes=1):
        self.unparentToonParts()
        self.removePart("torso", "1000")
        self.removePart("torso", "500")
        self.removePart("torso", "250")
        self.style.torso = torsoStyle
        self.generateToonTorso(copy, genClothes)
        self.generateToonColor()
        self.parentToonParts()
        self.rescaleToon()
        self.resetHeight()
        self.setupToonNodes()
        self.generateBackpack()

    def generateToonHead(self, copy=1):
        ToonHead.generateToonHead(self, copy, self.style, ("1000", "500", "250"))
        if self.style.getAnimal() == "dog":
            self.loadAnims(HeadAnimDict[self.style.head], "head", "1000")
            self.loadAnims(HeadAnimDict[self.style.head], "head", "500")
            self.loadAnims(HeadAnimDict[self.style.head], "head", "250")

    def swapToonHead(self, headStyle, copy=1):
        self.stopLookAroundNow()
        self.eyelids.request("open")
        self.unparentToonParts()
        self.removePart("head", "1000")
        self.removePart("head", "500")
        self.removePart("head", "250")
        self.style.head = headStyle
        self.generateToonHead(copy)
        self.generateToonColor()
        self.parentToonParts()
        self.rescaleToon()
        self.resetHeight()
        self.eyelids.request("open")
        self.startLookAround()

    def generateToonColor(self):
        ToonHead.generateToonColor(self, self.style)
        armColor = self.style.getArmColor()
        gloveColor = self.style.getGloveColor()
        legColor = self.style.getLegColor()
        for lodName in self.getLODNames():
            torso = self.getPart("torso", lodName)
            if len(self.style.torso) == 1:
                parts = torso.findAllMatches("**/torso*")
                parts.setColor(armColor)
            for pieceName in ("arms", "neck"):
                piece = torso.find("**/" + pieceName)
                piece.setColor(armColor)

            hands = torso.find("**/hands")
            hands.setColor(gloveColor)
            legs = self.getPart("legs", lodName)
            for pieceName in ("legs", "feet"):
                piece = legs.find("**/%s;+s" % pieceName)
                piece.setColor(legColor)

    def swapToonColor(self, dna):
        self.setStyle(dna)
        self.generateToonColor()

    def __swapToonClothes(self, dna):
        self.setStyle(dna)
        self.generateToonClothes(fromNet=1)

    def generateToonClothes(self, fromNet=0):
        swappedTorso = 0
        if self.hasLOD():
            if self.style.getGender() == "f" and fromNet == 0:
                try:
                    bottomPair = ToonDNA.GirlBottoms[self.style.botTex]
                except:
                    bottomPair = ToonDNA.GirlBottoms[0]

                if len(self.style.torso) < 2:
                    self.sendLogSuspiciousEvent("nakedToonDNA %s was requested" % self.style.torso)
                    return 0
                elif self.style.torso[1] == "s" and bottomPair[1] == ToonDNA.SKIRT:
                    self.swapToonTorso(self.style.torso[0] + "d", genClothes=0)
                    swappedTorso = 1
                elif self.style.torso[1] == "d" and bottomPair[1] == ToonDNA.SHORTS:
                    self.swapToonTorso(self.style.torso[0] + "s", genClothes=0)
                    swappedTorso = 1
            try:
                texName = ToonDNA.Shirts[self.style.topTex]
            except:
                texName = ToonDNA.Shirts[0]

            shirtTex = loader.loadTexture(texName, okMissing=True)
            if shirtTex is None:
                self.sendLogSuspiciousEvent("failed to load texture %s" % texName)
                shirtTex = loader.loadTexture(ToonDNA.Shirts[0])
            shirtTex.setMinfilter(Texture.FTLinearMipmapLinear)
            shirtTex.setMagfilter(Texture.FTLinear)
            try:
                shirtColor = ToonDNA.ClothesColors[self.style.topTexColor]
            except:
                shirtColor = ToonDNA.ClothesColors[0]

            try:
                texName = ToonDNA.Sleeves[self.style.sleeveTex]
            except:
                texName = ToonDNA.Sleeves[0]

            sleeveTex = loader.loadTexture(texName, okMissing=True)
            if sleeveTex is None:
                self.sendLogSuspiciousEvent("failed to load texture %s" % texName)
                sleeveTex = loader.loadTexture(ToonDNA.Sleeves[0])
            sleeveTex.setMinfilter(Texture.FTLinearMipmapLinear)
            sleeveTex.setMagfilter(Texture.FTLinear)
            try:
                sleeveColor = ToonDNA.ClothesColors[self.style.sleeveTexColor]
            except:
                sleeveColor = ToonDNA.ClothesColors[0]

            if self.style.getGender() == "m":
                try:
                    texName = ToonDNA.BoyShorts[self.style.botTex]
                except:
                    texName = ToonDNA.BoyShorts[0]

            else:
                try:
                    texName = ToonDNA.GirlBottoms[self.style.botTex][0]
                except:
                    texName = ToonDNA.GirlBottoms[0][0]

            bottomTex = loader.loadTexture(texName, okMissing=True)
            if bottomTex is None:
                self.sendLogSuspiciousEvent("failed to load texture %s" % texName)
                if self.style.getGender() == "m":
                    bottomTex = loader.loadTexture(ToonDNA.BoyShorts[0])
                else:
                    bottomTex = loader.loadTexture(ToonDNA.GirlBottoms[0][0])
            bottomTex.setMinfilter(Texture.FTLinearMipmapLinear)
            bottomTex.setMagfilter(Texture.FTLinear)
            try:
                bottomColor = ToonDNA.ClothesColors[self.style.botTexColor]
            except:
                bottomColor = ToonDNA.ClothesColors[0]

            darkBottomColor = bottomColor * 0.5
            darkBottomColor.setW(1.0)
            for lodName in self.getLODNames():
                thisPart = self.getPart("torso", lodName)
                top = thisPart.find("**/torso-top")
                top.setTexture(shirtTex, 1)
                top.setColor(shirtColor)
                sleeves = thisPart.find("**/sleeves")
                sleeves.setTexture(sleeveTex, 1)
                sleeves.setColor(sleeveColor)
                bottoms = thisPart.findAllMatches("**/torso-bot")
                for bottomNum in range(0, bottoms.getNumPaths()):
                    bottom = bottoms.getPath(bottomNum)
                    bottom.setTexture(bottomTex, 1)
                    bottom.setColor(bottomColor)

                caps = thisPart.findAllMatches("**/torso-bot-cap")
                caps.setColor(darkBottomColor)

        return swappedTorso

    def generateHat(self):
        hat = self.getHat()
        if hat[0] >= len(ToonDNA.HatModels):
            self.sendLogSuspiciousEvent("tried to put a wrong hat idx %d" % hat[0])
            return
        if len(self.hatNodes) > 0:
            for hatNode in self.hatNodes:
                hatNode.removeNode()

            self.hatNodes = []
        self.showEars()
        if hat[0] != 0:
            hatGeom = loader.loadModel(ToonDNA.HatModels[hat[0]], okMissing=True)
            if hatGeom:
                if hat[0] == 54:
                    self.hideEars()
                if hat[1] != 0:
                    texName = ToonDNA.HatTextures[hat[1]]
                    tex = loader.loadTexture(texName, okMissing=True)
                    if tex is None:
                        self.sendLogSuspiciousEvent("failed to load texture %s" % texName)
                    else:
                        tex.setMinfilter(Texture.FTLinearMipmapLinear)
                        tex.setMagfilter(Texture.FTLinear)
                        hatGeom.setTexture(tex, 1)
                transOffset = None
                if AccessoryGlobals.ExtendedHatTransTable.get(hat[0]):
                    transOffset = AccessoryGlobals.ExtendedHatTransTable[hat[0]].get(self.style.head[:2])
                if transOffset is None:
                    transOffset = AccessoryGlobals.HatTransTable.get(self.style.head[:2])
                    if transOffset is None:
                        return
                hatGeom.setPos(transOffset[0][0], transOffset[0][1], transOffset[0][2])
                hatGeom.setHpr(transOffset[1][0], transOffset[1][1], transOffset[1][2])
                hatGeom.setScale(transOffset[2][0], transOffset[2][1], transOffset[2][2])
                headNodes = self.findAllMatches("**/__Actor_head")
                for headNode in headNodes:
                    hatNode = headNode.attachNewNode("hatNode")
                    self.hatNodes.append(hatNode)
                    hatGeom.instanceTo(hatNode)

        return

    def generateGlasses(self):
        glasses = self.getGlasses()
        if glasses[0] >= len(ToonDNA.GlassesModels):
            self.sendLogSuspiciousEvent("tried to put a wrong glasses idx %d" % glasses[0])
            return
        if len(self.glassesNodes) > 0:
            for glassesNode in self.glassesNodes:
                glassesNode.removeNode()

            self.glassesNodes = []
        self.showEyelashes()
        if glasses[0] != 0:
            glassesGeom = loader.loadModel(ToonDNA.GlassesModels[glasses[0]], okMissing=True)
            if glassesGeom:
                if glasses[0] in [15, 16]:
                    self.hideEyelashes()
                if glasses[1] != 0:
                    texName = ToonDNA.GlassesTextures[glasses[1]]
                    tex = loader.loadTexture(texName, okMissing=True)
                    if tex is None:
                        self.sendLogSuspiciousEvent("failed to load texture %s" % texName)
                    else:
                        tex.setMinfilter(Texture.FTLinearMipmapLinear)
                        tex.setMagfilter(Texture.FTLinear)
                        glassesGeom.setTexture(tex, 1)
                transOffset = None
                if AccessoryGlobals.ExtendedGlassesTransTable.get(glasses[0]):
                    transOffset = AccessoryGlobals.ExtendedGlassesTransTable[glasses[0]].get(self.style.head[:2])
                if transOffset is None:
                    transOffset = AccessoryGlobals.GlassesTransTable.get(self.style.head[:2])
                    if transOffset is None:
                        return
                glassesGeom.setPos(transOffset[0][0], transOffset[0][1], transOffset[0][2])
                glassesGeom.setHpr(transOffset[1][0], transOffset[1][1], transOffset[1][2])
                glassesGeom.setScale(transOffset[2][0], transOffset[2][1], transOffset[2][2])
                headNodes = self.findAllMatches("**/__Actor_head")
                for headNode in headNodes:
                    glassesNode = headNode.attachNewNode("glassesNode")
                    self.glassesNodes.append(glassesNode)
                    glassesGeom.instanceTo(glassesNode)

        return

    def generateBackpack(self):
        backpack = self.getBackpack()
        if backpack[0] >= len(ToonDNA.BackpackModels):
            self.sendLogSuspiciousEvent("tried to put a wrong backpack idx %d" % backpack[0])
            return
        if len(self.backpackNodes) > 0:
            for backpackNode in self.backpackNodes:
                backpackNode.removeNode()

            self.backpackNodes = []
        if backpack[0] != 0:
            geom = loader.loadModel(ToonDNA.BackpackModels[backpack[0]], okMissing=True)
            if geom:
                if backpack[1] != 0:
                    texName = ToonDNA.BackpackTextures[backpack[1]]
                    tex = loader.loadTexture(texName, okMissing=True)
                    if tex is None:
                        self.sendLogSuspiciousEvent("failed to load texture %s" % texName)
                    else:
                        tex.setMinfilter(Texture.FTLinearMipmapLinear)
                        tex.setMagfilter(Texture.FTLinear)
                        geom.setTexture(tex, 1)
                transOffset = None
                if AccessoryGlobals.ExtendedBackpackTransTable.get(backpack[0]):
                    transOffset = AccessoryGlobals.ExtendedBackpackTransTable[backpack[0]].get(self.style.torso[:1])
                if transOffset is None:
                    transOffset = AccessoryGlobals.BackpackTransTable.get(self.style.torso[:1])
                    if transOffset is None:
                        return
                geom.setPos(transOffset[0][0], transOffset[0][1], transOffset[0][2])
                geom.setHpr(transOffset[1][0], transOffset[1][1], transOffset[1][2])
                geom.setScale(transOffset[2][0], transOffset[2][1], transOffset[2][2])
                nodes = self.findAllMatches("**/def_joint_attachFlower")
                for node in nodes:
                    theNode = node.attachNewNode("backpackNode")
                    self.backpackNodes.append(theNode)
                    geom.instanceTo(theNode)

        return

    def generateShoes(self):
        shoes = self.getShoes()
        if shoes[0] >= len(ToonDNA.ShoesModels):
            self.sendLogSuspiciousEvent("tried to put a wrong shoes idx %d" % shoes[0])
            return
        self.findAllMatches("**/feet;+s").stash()
        self.findAllMatches("**/boots_short;+s").stash()
        self.findAllMatches("**/boots_long;+s").stash()
        self.findAllMatches("**/shoes;+s").stash()
        geoms = self.findAllMatches("**/%s;+s" % ToonDNA.ShoesModels[shoes[0]])
        for geom in geoms:
            geom.unstash()

        if shoes[0] != 0:
            for geom in geoms:
                texName = ToonDNA.ShoesTextures[shoes[1]]
                if self.style.legs == "l" and shoes[0] == 3:
                    texName = texName[:-4] + "LL.png"
                tex = loader.loadTexture(texName, okMissing=True)
                if tex is None:
                    self.sendLogSuspiciousEvent("failed to load texture %s" % texName)
                else:
                    tex.setMinfilter(Texture.FTLinearMipmapLinear)
                    tex.setMagfilter(Texture.FTLinear)
                    geom.setTexture(tex, 1)

        return

    def generateToonAccessories(self):
        self.generateHat()
        self.generateGlasses()
        self.generateBackpack()
        self.generateShoes()

    def setHat(self, hatIdx, textureIdx):
        self.hat = (hatIdx, textureIdx)
        self.generateHat()

    def getHat(self):
        return self.hat

    def setGlasses(self, glassesIdx, textureIdx):
        self.glasses = (glassesIdx, textureIdx)
        self.generateGlasses()

    def getGlasses(self):
        return self.glasses

    def setBackpack(self, backpackIdx, textureIdx):
        self.backpack = (backpackIdx, textureIdx)
        self.generateBackpack()

    def getBackpack(self):
        return self.backpack

    def setShoes(self, shoesIdx, textureIdx):
        self.shoes = (shoesIdx, textureIdx)
        self.generateShoes()

    def getShoes(self):
        return self.shoes

    def getDialogueArray(self):
        loadDialog()
        animalType = self.style.getType()
        return DialogueSoundFiles[animalType]

    def getShadowJoint(self):
        if self.shadowJoint:
            return self.shadowJoint
        shadowJoint = NodePath("shadowJoint")
        for lodName in self.getLODNames():
            joint = self.getPart("legs", lodName).find("**/joint_shadow")
            shadowJoint = shadowJoint.instanceTo(joint)

        self.shadowJoint = shadowJoint
        return shadowJoint

    def getNametagJoints(self):
        joints = []
        for lodName in self.getLODNames():
            bundle = self.getPartBundle("legs", lodName)
            joint = bundle.findChild("joint_nameTag")
            if joint:
                joints.append(joint)

        return joints

    def getRightHands(self):
        return self.rightHands

    def getLeftHands(self):
        return self.leftHands

    def getHeadParts(self):
        return self.headParts

    def getHipsParts(self):
        return self.hipsParts

    def getTorsoParts(self):
        return self.torsoParts

    def getLegsParts(self):
        return self.legsParts

    def findSomethingToLookAt(self):
        if self.randGen.random() < 0.1 or not hasattr(self, "cr"):
            x = self.randGen.choice((-0.8, -0.5, 0, 0.5, 0.8))
            y = self.randGen.choice((-0.5, 0, 0.5, 0.8))
            self.lerpLookAt(Point3(x, 1.5, y), blink=1)
            return
        nodePathList = []
        for id, obj in list(self.cr.doId2do.items()):
            if hasattr(obj, "getStareAtNodeAndOffset") and obj != self:
                node, offset = obj.getStareAtNodeAndOffset()
                if node.getY(self) > 0.0:
                    nodePathList.append((node, offset))

        if nodePathList:
            nodePathList.sort(key=lambda z: z[0].getDistance(self))
            if len(nodePathList) >= 2:
                if self.randGen.random() < 0.9:
                    chosenNodePath = nodePathList[0]
                else:
                    chosenNodePath = nodePathList[1]
            else:
                chosenNodePath = nodePathList[0]
            self.lerpLookAt(chosenNodePath[0].getPos(self), blink=1)
        else:
            ToonHead.findSomethingToLookAt(self)

    def setSpeed(self, forwardSpeed, rotateSpeed):
        self.forwardSpeed = forwardSpeed
        self.rotateSpeed = rotateSpeed
        action = None
        if self.standWalkRunReverse != None:
            if forwardSpeed >= RunCutOff:
                action = RUN_INDEX
            elif forwardSpeed > WalkCutOff:
                action = WALK_INDEX
            elif forwardSpeed < -WalkCutOff:
                action = REVERSE_INDEX
            elif rotateSpeed != 0.0:
                action = WALK_INDEX
            else:
                action = STAND_INDEX
            anim, rate = self.standWalkRunReverse[action]
            self.motion.enter()
            self.motion.setState(anim, rate)
            if anim != self.playingAnim:
                self.playingAnim = anim
                self.playingRate = rate
                self.stop()
                self.loop(anim)
                self.setPlayRate(rate, anim)
            elif rate != self.playingRate:
                self.playingRate = rate
                self.setPlayRate(rate, anim)
        return action

    def enterOff(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.setActiveShadow(0)
        self.playingAnim = None
        return

    def exitOff(self):
        pass

    def enterNeutral(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        anim = "neutral"
        self.pose(anim, int(self.getNumFrames(anim) * self.randGen.random()))
        self.loop(anim, restart=0)
        self.setPlayRate(animMultiplier, anim)
        self.playingAnim = anim
        self.setActiveShadow(0)

    def exitNeutral(self):
        self.stop()

    def enterVictory(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        anim = "victory"
        frame = int(ts * self.getFrameRate(anim) * animMultiplier)
        self.pose(anim, frame)
        self.loop("victory", restart=0)
        self.setPlayRate(animMultiplier, "victory")
        self.playingAnim = anim
        self.setActiveShadow(0)

    def exitVictory(self):
        self.stop()

    def enterHappy(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.playingAnim = None
        self.playingRate = None
        self.standWalkRunReverse = (("neutral", 1.0), ("walk", 1.0), ("run", 1.0), ("walk", -1.0))
        self.setSpeed(self.forwardSpeed, self.rotateSpeed)
        self.setActiveShadow(1)
        return

    def exitHappy(self):
        self.standWalkRunReverse = None
        self.stop()
        self.motion.exit()
        return

    def enterSad(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.playingAnim = "sad"
        self.playingRate = None
        self.standWalkRunReverse = (("sad-neutral", 1.0), ("sad-walk", 1.2), ("sad-walk", 1.2), ("sad-walk", -1.0))
        self.setSpeed(0, 0)
        Emote.globalEmote.disableBody(self, "toon, enterSad")
        self.setActiveShadow(1)
        if self.isLocal():
            self.controlManager.disableAvatarJump()
        return

    def exitSad(self):
        self.standWalkRunReverse = None
        self.stop()
        self.motion.exit()
        Emote.globalEmote.releaseBody(self, "toon, exitSad")
        if self.isLocal():
            self.controlManager.enableAvatarJump()
        return

    def enterCatching(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.playingAnim = None
        self.playingRate = None
        self.standWalkRunReverse = (("catch-neutral", 1.0), ("catch-run", 1.0), ("catch-run", 1.0), ("catch-run", -1.0))
        self.setSpeed(self.forwardSpeed, self.rotateSpeed)
        self.setActiveShadow(1)
        return

    def exitCatching(self):
        self.standWalkRunReverse = None
        self.stop()
        self.motion.exit()
        return

    def enterCatchEating(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.playingAnim = None
        self.playingRate = None
        self.standWalkRunReverse = (
            ("catch-eatneutral", 1.0),
            ("catch-eatnrun", 1.0),
            ("catch-eatnrun", 1.0),
            ("catch-eatnrun", -1.0),
        )
        self.setSpeed(self.forwardSpeed, self.rotateSpeed)
        self.setActiveShadow(0)
        return

    def exitCatchEating(self):
        self.standWalkRunReverse = None
        self.stop()
        self.motion.exit()
        return

    def enterWalk(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.loop("walk")
        self.setPlayRate(animMultiplier, "walk")
        self.setActiveShadow(1)

    def exitWalk(self):
        self.stop()

    def getJumpDuration(self):
        if self.playingAnim == "neutral":
            return self.getDuration("jump", "legs")
        else:
            return self.getDuration("running-jump", "legs")

    def enterJump(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if self.playingAnim == "neutral":
            anim = "jump"
        else:
            anim = "running-jump"
        self.playingAnim = anim
        self.setPlayRate(animMultiplier, anim)
        self.play(anim)
        self.setActiveShadow(1)

    def exitJump(self):
        self.stop()
        self.playingAnim = "neutral"

    def enterJumpSquat(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if self.playingAnim == "neutral":
            anim = "jump-squat"
        else:
            anim = "running-jump-squat"
        self.playingAnim = anim
        self.setPlayRate(animMultiplier, anim)
        self.play(anim)
        self.setActiveShadow(1)

    def exitJumpSquat(self):
        self.stop()
        self.playingAnim = "neutral"

    def enterJumpAirborne(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if self.playingAnim == "neutral":
            anim = "jump-idle"
        else:
            anim = "running-jump-idle"
        self.playingAnim = anim
        self.setPlayRate(animMultiplier, anim)
        self.loop(anim)
        self.setActiveShadow(1)

    def exitJumpAirborne(self):
        self.stop()
        self.playingAnim = "neutral"

    def enterJumpLand(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if self.playingAnim == "running-jump-idle":
            anim = "running-jump-land"
        else:
            anim = "jump-land"
        self.playingAnim = anim
        self.setPlayRate(animMultiplier, anim)
        self.play(anim)
        self.setActiveShadow(1)

    def exitJumpLand(self):
        self.stop()
        self.playingAnim = "neutral"

    def enterRun(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.loop("run")
        self.setPlayRate(animMultiplier, "run")
        Emote.globalEmote.disableBody(self, "toon, enterRun")
        self.setActiveShadow(1)

    def exitRun(self):
        self.stop()
        Emote.globalEmote.releaseBody(self, "toon, exitRun")

    def enterSwim(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        Emote.globalEmote.disableAll(self, "enterSwim")
        self.playingAnim = "swim"
        self.loop("swim")
        self.setPlayRate(animMultiplier, "swim")
        self.getGeomNode().setP(-89.0)
        self.dropShadow.hide()
        if self.isLocal():
            self.useSwimControls()
        self.nametag3d.setPos(0, -2, 1)
        self.startBobSwimTask()
        self.setActiveShadow(0)

    def enterCringe(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.loop("cringe")
        self.getGeomNode().setPos(0, 0, -2)
        self.setPlayRate(animMultiplier, "swim")

    def exitCringe(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.stop()
        self.getGeomNode().setPos(0, 0, 0)
        self.playingAnim = "neutral"
        self.setPlayRate(animMultiplier, "swim")

    def enterDive(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.loop("swim")
        if hasattr(self.getGeomNode(), "setPos"):
            self.getGeomNode().setPos(0, 0, -2)
            self.setPlayRate(animMultiplier, "swim")
            self.setActiveShadow(0)
            self.dropShadow.hide()
            self.nametag3d.setPos(0, -2, 1)

    def exitDive(self):
        self.stop()
        self.getGeomNode().setPos(0, 0, 0)
        self.playingAnim = "neutral"
        self.dropShadow.show()
        self.nametag3d.setPos(0, 0, self.height + 0.5)

    def enterSwimHold(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.getGeomNode().setPos(0, 0, -2)
        self.nametag3d.setPos(0, -2, 1)
        self.pose("swim", 55)

    def exitSwimHold(self):
        self.stop()
        self.getGeomNode().setPos(0, 0, 0)
        self.playingAnim = "neutral"
        self.dropShadow.show()
        self.nametag3d.setPos(0, 0, self.height + 0.5)

    def exitSwim(self):
        self.stop()
        self.playingAnim = "neutral"
        self.stopBobSwimTask()
        self.getGeomNode().setPosHpr(0, 0, 0, 0, 0, 0)
        self.dropShadow.show()
        if self.isLocal():
            self.useWalkControls()
        self.nametag3d.setPos(0, 0, self.height + 0.5)
        Emote.globalEmote.releaseAll(self, "exitSwim")

    def startBobSwimTask(self):
        taskMgr.remove("swimTask")
        if self.swimBobSeq:
            self.swimBobSeq.finish()
            self.swimBobSeq = None
        self.getGeomNode().setZ(4.0)
        self.nametag3d.setZ(5.0)
        self.swimBobSeq = Sequence(
            self.getGeomNode().posInterval(1, Point3(0, -3, 3), startPos=Point3(0, -3, 4), blendType="easeInOut"),
            self.getGeomNode().posInterval(1, Point3(0, -3, 4), startPos=Point3(0, -3, 3), blendType="easeInOut"),
        )
        self.swimBobSeq.loop()

    def stopBobSwimTask(self):
        if self.swimBobSeq:
            self.swimBobSeq.finish()
            self.swimBobSeq = None
        self.getGeomNode().setPos(0, 0, 0)
        self.nametag3d.setZ(1.0)

    def getSoundTeleport(self):
        if not self.soundTeleport:
            self.soundTeleport = base.loader.loadSfx("phase_3.5/audio/sfx/AV_teleport.ogg")
        return self.soundTeleport

    def getTeleportOutTrack(self, autoFinishTrack=1):
        def showHoles(holes, hands):
            for hole, hand in zip(holes, hands):
                hole.reparentTo(hand)

        def reparentHoles(holes, toon):
            holes[0].reparentTo(toon)
            holes[1].detachNode()
            holes[2].detachNode()
            holes[0].setBin("shadow", 0)
            holes[0].setDepthTest(0)
            holes[0].setDepthWrite(0)

        def cleanupHoles(holes):
            holes[0].detachNode()
            holes[0].clearBin()
            holes[0].clearDepthTest()
            holes[0].clearDepthWrite()

        holes = self.getHoleActors()
        hands = self.getRightHands()
        holeTrack = Track(
            (0.0, Func(showHoles, holes, hands)),
            (0.5, SoundInterval(self.getSoundTeleport(), node=self)),
            (1.708, Func(reparentHoles, holes, self)),
            (3.4, Func(cleanupHoles, holes)),
        )
        if hasattr(self, "uniqueName"):
            trackName = self.uniqueName("teleportOut")
        else:
            trackName = "teleportOut"
        track = Parallel(holeTrack, name=trackName, autoFinish=autoFinishTrack)
        for hole in holes:
            track.append(ActorInterval(hole, "hole", duration=3.4))

        track.append(ActorInterval(self, "teleport", duration=3.4))
        return track

    def enterTeleportOut(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        name = self.name
        if hasattr(self, "doId"):
            name += "-" + str(self.doId)
        self.notify.debug("enterTeleportOut %s" % name)
        if self.ghostMode:
            if callback:
                callback(*extraArgs)
            return
        self.playingAnim = "teleport"
        Emote.globalEmote.disableAll(self, "enterTeleportOut")
        if self.isLocal():
            autoFinishTrack = 0
        else:
            autoFinishTrack = 1
        self.track = self.getTeleportOutTrack(autoFinishTrack)
        self.track.setDoneEvent(self.track.getName())
        self.acceptOnce(self.track.getName(), self.finishTeleportOut, [callback, extraArgs])
        holeClip = PlaneNode("holeClip")
        self.holeClipPath = self.attachNewNode(holeClip)
        self.getGeomNode().setClipPlane(self.holeClipPath)
        self.nametag3d.setClipPlane(self.holeClipPath)
        self.track.start(ts)
        self.setActiveShadow(0)

    def finishTeleportOut(self, callback=None, extraArgs=[]):
        name = self.name
        if hasattr(self, "doId"):
            name += "-" + str(self.doId)
        self.notify.debug("finishTeleportOut %s" % name)
        if self.track != None:
            self.ignore(self.track.getName())
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        if hasattr(self, "animFSM"):
            self.animFSM.request("TeleportedOut")
        if callback:
            callback(*extraArgs)
        return

    def exitTeleportOut(self):
        name = self.name
        if hasattr(self, "doId"):
            name += "-" + str(self.doId)
        self.notify.debug("exitTeleportOut %s" % name)
        if self.track != None:
            self.ignore(self.track.getName())
            self.track.finish()
            self.track = None
        geomNode = self.getGeomNode()
        if geomNode and not geomNode.isEmpty():
            self.getGeomNode().clearClipPlane()
        if self.nametag3d and not self.nametag3d.isEmpty():
            self.nametag3d.clearClipPlane()
        if self.holeClipPath:
            self.holeClipPath.removeNode()
            self.holeClipPath = None
        Emote.globalEmote.releaseAll(self, "exitTeleportOut")
        if self and not self.isEmpty():
            self.show()
        return

    def enterTeleportedOut(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.setActiveShadow(0)

    def exitTeleportedOut(self):
        pass

    def getDiedInterval(self, autoFinishTrack=1):
        sound = loader.loadSfx("phase_5/audio/sfx/ENC_Lose.ogg")
        if hasattr(self, "uniqueName"):
            trackName = self.uniqueName("died")
        else:
            trackName = "died"
        ival = Sequence(
            Func(Emote.globalEmote.disableBody, self),
            Func(self.sadEyes),
            Func(self.blinkEyes),
            Track(
                (0, ActorInterval(self, "lose")),
                (2, SoundInterval(sound, node=self)),
                (5.333, self.scaleInterval(1.5, VBase3(0.01, 0.01, 0.01), blendType="easeInOut")),
            ),
            Func(self.detachNode),
            Func(self.setScale, 1, 1, 1),
            Func(self.normalEyes),
            Func(self.blinkEyes),
            Func(Emote.globalEmote.releaseBody, self),
            name=trackName,
            autoFinish=autoFinishTrack,
        )
        return ival

    def enterDied(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if self.ghostMode:
            if callback:
                callback(*extraArgs)
            return
        self.playingAnim = "lose"
        Emote.globalEmote.disableAll(self, "enterDied")
        if self.isLocal():
            autoFinishTrack = 0
        else:
            autoFinishTrack = 1
        if hasattr(self, "jumpLandAnimFixTask") and self.jumpLandAnimFixTask:
            self.jumpLandAnimFixTask.remove()
            self.jumpLandAnimFixTask = None
        self.track = self.getDiedInterval(autoFinishTrack)
        if callback:
            self.track = Sequence(self.track, Func(callback, *extraArgs), autoFinish=autoFinishTrack)
        self.track.start(ts)
        self.setActiveShadow(0)
        return

    def finishDied(self, callback=None, extraArgs=[]):
        if self.track != None:
            self.ignore(self.track.getName())
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        if hasattr(self, "animFSM"):
            self.animFSM.request("TeleportedOut")
        if callback:
            callback(*extraArgs)
        return

    def exitDied(self):
        if self.track != None:
            self.ignore(self.track.getName())
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        Emote.globalEmote.releaseAll(self, "exitDied")
        self.show()
        return

    def getTeleportInTrack(self):
        hole = self.getHoleActors()[0]
        hole.setBin("shadow", 0)
        hole.setDepthTest(0)
        hole.setDepthWrite(0)
        holeTrack = Sequence()
        holeTrack.append(Func(hole.reparentTo, self))
        pos = Point3(0, -2.4, 0)
        holeTrack.append(Func(hole.setPos, self, pos))
        holeTrack.append(ActorInterval(hole, "hole", startTime=3.4, endTime=3.1))
        holeTrack.append(Wait(0.6))
        holeTrack.append(ActorInterval(hole, "hole", startTime=3.1, endTime=3.4))

        def restoreHole(hole):
            hole.setPos(0, 0, 0)
            hole.detachNode()
            hole.clearBin()
            hole.clearDepthTest()
            hole.clearDepthWrite()

        holeTrack.append(Func(restoreHole, hole))
        toonTrack = Sequence(
            Wait(0.3),
            Func(self.getGeomNode().show),
            Func(self.nametag3d.show),
            ActorInterval(self, "jump", startTime=0.45),
        )
        if hasattr(self, "uniqueName"):
            trackName = self.uniqueName("teleportIn")
        else:
            trackName = "teleportIn"
        return Parallel(holeTrack, toonTrack, name=trackName)

    def enterTeleportIn(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if self.ghostMode:
            if callback:
                callback(*extraArgs)
            return
        self.show()
        self.playingAnim = "teleport"
        Emote.globalEmote.disableAll(self, "enterTeleportIn")
        self.pose("teleport", self.getNumFrames("teleport") - 1)
        self.getGeomNode().hide()
        self.nametag3d.hide()
        self.track = self.getTeleportInTrack()
        if callback:
            self.track.setDoneEvent(self.track.getName())
            self.acceptOnce(self.track.getName(), callback, extraArgs)
        self.track.start(ts)
        self.setActiveShadow(0)

    def exitTeleportIn(self):
        self.playingAnim = None
        if self.track != None:
            self.ignore(self.track.getName())
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        if not self.ghostMode:
            self.getGeomNode().show()
            self.nametag3d.show()
        Emote.globalEmote.releaseAll(self, "exitTeleportIn")
        return

    def enterSitStart(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        Emote.globalEmote.disableBody(self)
        self.playingAnim = "sit-start"
        if self.isLocal():
            self.track = Sequence(ActorInterval(self, "sit-start"), Func(self.b_setAnimState, "Sit", animMultiplier))
        else:
            self.track = Sequence(ActorInterval(self, "sit-start"))
        self.track.start(ts)
        self.setActiveShadow(0)

    def exitSitStart(self):
        self.playingAnim = "neutral"
        if self.track != None:
            self.track.pause()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        Emote.globalEmote.releaseBody(self)
        return

    def enterSit(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        Emote.globalEmote.disableBody(self)
        self.playingAnim = "sit"
        self.loop("sit")
        self.setActiveShadow(0)

    def exitSit(self):
        self.playingAnim = "neutral"
        Emote.globalEmote.releaseBody(self)

    def enterSleep(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.stopLookAround()
        self.stopBlink()
        self.closeEyes()
        self.lerpLookAt(Point3(0, 1, -4))
        self.loop("neutral")
        self.setPlayRate(animMultiplier * 0.4, "neutral")
        self.setChatAbsolute(SLEEP_STRING, CFThought)
        if self == base.localAvatar:
            print("adding timeout task")
            taskMgr.doMethodLater(self.afkTimeout, self.__handleAfkTimeout, self.uniqueName("afkTimeout"))
        self.setActiveShadow(0)

    def __handleAfkTimeout(self, task):
        print("handling timeout")
        self.ignore("wakeup")
        base.cr.playGame.getPlace().fsm.request("final")
        self.b_setAnimState("TeleportOut", 1, self.__handleAfkExitTeleport, [0])
        return Task.done

    def __handleAfkExitTeleport(self, requestStatus):
        self.notify.info("closing shard...")
        base.cr.gameFSM.request("closeShard", ["afkTimeout"])

    def exitSleep(self):
        taskMgr.remove(self.uniqueName("afkTimeout"))
        self.startLookAround()
        self.openEyes()
        self.startBlink()
        doClear = SLEEP_STRING in (self.nametag.getChat(), self.nametag.getStompText())
        if doClear:
            self.clearChat()
        self.lerpLookAt(Point3(0, 1, 0), time=0.25)
        self.stop()

    def enterPush(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        Emote.globalEmote.disableBody(self)
        self.playingAnim = "push"
        self.track = Sequence(ActorInterval(self, "push"))
        self.track.loop()
        self.setActiveShadow(1)

    def exitPush(self):
        self.playingAnim = "neutral"
        if self.track != None:
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        Emote.globalEmote.releaseBody(self)
        return

    def enterEmote(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if len(extraArgs) > 0:
            emoteIndex = extraArgs[0]
        else:
            return
        self.playingAnim = None
        self.playingRate = None
        self.standWalkRunReverse = (("neutral", 1.0), ("walk", 1.0), ("run", 1.0), ("walk", -1.0))
        self.setSpeed(self.forwardSpeed, self.rotateSpeed)
        if self.isLocal() and emoteIndex != Emote.globalEmote.EmoteSleepIndex:
            if self.sleepFlag:
                self.b_setAnimState("Happy", self.animMultiplier)
            self.wakeUp()
        duration = 0
        self.emoteTrack, duration = Emote.globalEmote.doEmote(self, emoteIndex, ts)
        self.setActiveShadow(1)
        return

    def doEmote(self, emoteIndex, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        if not self.isLocal():
            if base.cr.avatarFriendsManager.checkIgnored(self.doId):
                return
        duration = 0
        if self.isLocal():
            self.wakeUp()
            if self.hasTrackAnimToSpeed():
                self.trackAnimToSpeed(None)
        self.emoteTrack, duration = Emote.globalEmote.doEmote(self, emoteIndex, ts)
        return

    def exitEmote(self):
        self.stop()
        if self.emoteTrack != None:
            self.emoteTrack.finish()
            self.emoteTrack = None
        taskMgr.remove(self.taskName("finishEmote"))
        return

    def enterSquish(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        Emote.globalEmote.disableAll(self)
        sound = loader.loadSfx("phase_9/audio/sfx/toon_decompress.ogg")
        lerpTime = 0.1
        node = self.getGeomNode().getChild(0)
        origScale = node.getScale()
        self.track = Sequence(
            LerpScaleInterval(node, lerpTime, VBase3(2, 2, 0.025), blendType="easeInOut"),
            Wait(1.0),
            Parallel(
                Sequence(
                    Wait(0.4),
                    LerpScaleInterval(node, lerpTime, VBase3(1.4, 1.4, 1.4), blendType="easeInOut"),
                    LerpScaleInterval(node, lerpTime / 2.0, VBase3(0.8, 0.8, 0.8), blendType="easeInOut"),
                    LerpScaleInterval(node, lerpTime / 3.0, origScale, blendType="easeInOut"),
                ),
                ActorInterval(self, "jump", startTime=0.2),
                SoundInterval(sound),
            ),
        )
        self.track.start(ts)
        self.setActiveShadow(1)

    def exitSquish(self):
        self.playingAnim = "neutral"
        if self.track != None:
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        Emote.globalEmote.releaseAll(self)
        return

    def enterFallDown(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        self.playingAnim = "fallDown"
        Emote.globalEmote.disableAll(self)
        self.track = Sequence(ActorInterval(self, "slip-backward"), name="fallTrack")
        if callback:
            self.track.setDoneEvent(self.track.getName())
            self.acceptOnce(self.track.getName(), callback, extraArgs)
        self.track.start(ts)

    def exitFallDown(self):
        self.playingAnim = "neutral"
        if self.track != None:
            self.ignore(self.track.getName())
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        Emote.globalEmote.releaseAll(self)
        return

    def stunToon(self, ts=0, callback=None, knockdown=0):
        if not self.isStunned:
            if self.stunTrack:
                self.stunTrack.finish()
                self.stunTrack = None

            def setStunned(stunned):
                self.isStunned = stunned
                if self == base.localAvatar:
                    messenger.send("toonStunned-" + str(self.doId), [self.isStunned])

            node = self.getGeomNode()
            lerpTime = 0.5
            down = self.doToonColorScale(VBase4(1, 1, 1, 0.6), lerpTime)
            up = self.doToonColorScale(VBase4(1, 1, 1, 0.9), lerpTime)
            clear = self.doToonColorScale(self.defaultColorScale, lerpTime)
            track = Sequence(
                Func(setStunned, 1),
                down,
                up,
                down,
                up,
                down,
                up,
                down,
                clear,
                Func(self.restoreDefaultColorScale),
                Func(setStunned, 0),
            )
            if knockdown:
                self.stunTrack = Parallel(ActorInterval(self, animName="slip-backward"), track)
            else:
                self.stunTrack = track
            self.stunTrack.start()
        return

    def getPieces(self, *pieces):
        results = []
        for lodName in self.getLODNames():
            for partName, pieceNames in pieces:
                part = self.getPart(partName, lodName)
                if part:
                    if type(pieceNames) == str:
                        pieceNames = (pieceNames,)
                    for pieceName in pieceNames:
                        npc = part.findAllMatches("**/%s;+s" % pieceName)
                        for i in range(npc.getNumPaths()):
                            results.append(npc[i])

        return results

    def applyCheesyEffect(self, effect, lerpTime=0):
        if self.effectTrack != None:
            self.effectTrack.finish()
            self.effectTrack = None
        if self.cheesyEffect != effect:
            oldEffect = self.cheesyEffect
            self.cheesyEffect = effect
            if oldEffect == CheesyEffects.NORMAL:
                self.effectTrack = self.__doCheesyEffect(effect, lerpTime)
            elif effect == CheesyEffects.NORMAL:
                self.effectTrack = self.__undoCheesyEffect(oldEffect, lerpTime)
            else:
                self.effectTrack = Sequence(
                    self.__undoCheesyEffect(oldEffect, lerpTime / 2.0), self.__doCheesyEffect(effect, lerpTime / 2.0)
                )
            self.effectTrack.start()
        return

    def clearCheesyEffect(self, lerpTime=0):
        self.applyCheesyEffect(CheesyEffects.NORMAL, lerpTime=lerpTime)
        if self.effectTrack != None:
            self.effectTrack.finish()
            self.effectTrack = None
        return

    def doToonColorScale(self, scale, lerpTime, keepDefault=0):
        if keepDefault:
            self.defaultColorScale = scale
        if scale == None:
            scale = VBase4(1, 1, 1, 1)
        node = self.getGeomNode()
        caps = self.getPieces(("torso", "torso-bot-cap"))
        track = Sequence()
        track.append(Func(node.setTransparency, 1))
        if scale[3] != 1:
            for cap in caps:
                track.append(HideInterval(cap))

        track.append(LerpColorScaleInterval(node, lerpTime, scale, blendType="easeInOut"))
        if scale[3] == 1:
            track.append(Func(node.clearTransparency))
            for cap in caps:
                track.append(ShowInterval(cap))

        elif scale[3] == 0:
            track.append(Func(node.clearTransparency))
        return track

    def restoreDefaultColorScale(self):
        node = self.getGeomNode()
        if node:
            if self.defaultColorScale:
                node.setColorScale(self.defaultColorScale)
                if self.defaultColorScale[3] != 1:
                    node.setTransparency(1)
                else:
                    node.clearTransparency()
            else:
                node.clearColorScale()
                node.clearTransparency()

    def __doCheesyEffect(self, effect, lerpTime):
        if effect == CheesyEffects.GHOST:
            alpha = 0
            if base.localAvatar.seeGhosts:
                alpha = 0.2
            return Sequence(
                self.__doToonGhostColorScale(VBase4(1, 1, 1, alpha), lerpTime, keepDefault=1), Func(self.nametag3d.hide)
            )
        return Sequence()

    def __undoCheesyEffect(self, effect, lerpTime):
        if effect == CheesyEffects.GHOST:
            return Sequence(Func(self.nametag3d.show), self.__doToonGhostColorScale(None, lerpTime, keepDefault=1))
        return Sequence()

    def enterFlattened(self, animMultiplier=1, ts=0, callback=None, extraArgs=[]):
        Emote.globalEmote.disableAll(self)
        lerpTime = 0.1
        node = self.getGeomNode().getChild(0)
        self.origScale = node.getScale()
        self.track = Sequence(LerpScaleInterval(node, lerpTime, VBase3(2, 2, 0.025), blendType="easeInOut"))
        self.track.start(ts)
        self.setActiveShadow(1)

    def exitFlattened(self):
        self.playingAnim = "neutral"
        if self.track != None:
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        node = self.getGeomNode().getChild(0)
        node.setScale(self.origScale)
        Emote.globalEmote.releaseAll(self)
        return


compileGlobalAnimList()
