import random

from direct.controls.GhostWalker import GhostWalker
from direct.controls.GravityWalker import GravityWalker
from direct.controls.ObserverWalker import ObserverWalker
from direct.controls.SwimWalker import SwimWalker
from direct.controls.TwoDWalker import TwoDWalker
from direct.distributed import DistributedSmoothNode
from direct.showbase.InputStateGlobal import inputState
from direct.task import Task
from panda3d.core import CollisionTraverser, ConfigVariableInt, Point3
from panda3d.otp import Nametag, WhisperPopup

from otp.avatar import DistributedAvatar
from toontown.toon.camera.CameraModule import CameraModule
from toontown.toonbase.globals.TTGlobalsCore import ThinkPosHotkey
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont
from toontown.toonbase.globals.TTGlobalsMovement import *
from toontown.toonbase.globals.TTGlobalsRender import *


class LocalAvatar(DistributedAvatar.DistributedAvatar, DistributedSmoothNode.DistributedSmoothNode):
    """
    This is the local version of a distributed avatar.
    """

    notify = directNotify.newCategory("LocalAvatar")

    sleepTimeout = ConfigVariableInt("sleep-timeout", 120).value
    swimTimeout = ConfigVariableInt("afk-timeout", 600).value

    def __init__(self, cr, chatMgr, talkAssistant=None, passMessagesThrough=False):
        """
        cr is a ClientRepository
        """
        try:
            self.LocalAvatar_initialized
            return
        except:
            pass

        self.debugSteps = 0
        self.nudgeInProgress = False

        self.LocalAvatar_initialized = 1
        DistributedAvatar.DistributedAvatar.__init__(self, cr)
        DistributedSmoothNode.DistributedSmoothNode.__init__(self, cr)

        self.cTrav = CollisionTraverser("base.cTrav")
        base.pushCTrav(self.cTrav)
        self.cTrav.setRespectPrevTransform(1)

        self.avatarControlsEnabled = 0
        self.controlManager = base.controlManager
        self.initializeCollisions()
        self.cmod = CameraModule(self)
        self.animMultiplier = 1.0

        self.runTimeout = 2.5

        self.customMessages = []

        self.chatMgr = chatMgr
        base.talkAssistant = talkAssistant

        self.garbleChat = 1

        self.teleportAllowed = 1

        self.lockedDown = 0

        self.isPageUp = 0
        self.isPageDown = 0

        self.soundRun = None
        self.soundWalk = None

        self.sleepFlag = 0

        self.movingFlag = 0
        self.swimmingFlag = 0

        self.lastNeedH = None

        self.sleepCallback = None
        self.accept("wakeup", self.wakeUp)

        self.jumpLandAnimFixTask = None

        self.nametag2dNormalContents = Nametag.CSpeech
        self.showNametag2d()

        self.setPickable(0)

    def useSwimControls(self):
        self.controlManager.use("swim", self)

    def useGhostControls(self):
        self.controlManager.use("ghost", self)

    def useWalkControls(self):
        self.controlManager.use("walk", self)

    def useTwoDControls(self):
        self.controlManager.use("twoD", self)

    def isLockedDown(self):
        return self.lockedDown

    def lock(self):
        if self.lockedDown == 1:
            self.notify.debug("lock() - already locked!")
        self.lockedDown = 1

    def unlock(self):
        if self.lockedDown == 0:
            self.notify.debug("unlock() - already unlocked!")
        self.lockedDown = 0

    def isInWater(self):
        return self.getZ(render) <= 0.0

    def isTeleportAllowed(self):
        """
        Returns true if the local avatar is currently allowed to
        teleport away somewhere, false otherwise.
        """
        return self.teleportAllowed

    def setTeleportAllowed(self, flag):
        """
        Sets the flag that indicates whether the toon is allowed to
        teleport away, even if we are in walk mode.  Usually this is
        1, but it may be set to 0 in unusual cases
        """
        self.teleportAllowed = flag
        self.refreshOnscreenButtons()

    def sendFriendsListEvent(self):
        self.wakeUp()
        messenger.send("openFriendsList")

    def delete(self):
        try:
            self.LocalAvatar_deleted
            return
        except:
            self.LocalAvatar_deleted = 1
        self.ignoreAll()
        self.stopJumpLandTask()
        taskMgr.remove("shadowReach")

        base.popCTrav()

        self.disableAvatarControls()
        self.stopTrackAnimToSpeed()
        self.cmod.destroy()
        self.deleteCollisions()
        self.controlManager.delete()
        self.physControls = None
        del self.controlManager
        base.controlManager = None
        self.positionExaminer.delete()
        del self.positionExaminer
        taskMgr.remove(self.uniqueName("walkReturnTask"))
        self.chatMgr.delete()
        del self.chatMgr
        del self.soundRun
        del self.soundWalk
        if hasattr(self, "soundWhisper"):
            del self.soundWhisper
        DistributedAvatar.DistributedAvatar.delete(self)

    def shadowReach(self, state):
        if base.localAvatar.shadowPlacer:
            base.localAvatar.shadowPlacer.lifter.setReach(base.localAvatar.getAirborneHeight() + 4.0)
        return Task.cont

    def wantLegacyLifter(self):
        return False

    def setupControls(
        self,
        avatarRadius=1.4,
        floorOffset=FloorOffset,
        reach=4.0,
        wallBitmask=WallBitmask,
        floorBitmask=FloorBitmask,
        ghostBitmask=GhostBitmask,
    ):
        """
        Set up the local avatar for collisions
        """
        walkControls = GravityWalker(legacyLifter=self.wantLegacyLifter())
        walkControls.setWallBitMask(wallBitmask)
        walkControls.setFloorBitMask(floorBitmask)
        walkControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        self.controlManager.add(walkControls, "walk")
        self.physControls = walkControls

        twoDControls = TwoDWalker()
        twoDControls.setWallBitMask(wallBitmask)
        twoDControls.setFloorBitMask(floorBitmask)
        twoDControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        self.controlManager.add(twoDControls, "twoD")

        swimControls = SwimWalker()
        swimControls.setWallBitMask(wallBitmask)
        swimControls.setFloorBitMask(floorBitmask)
        swimControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        self.controlManager.add(swimControls, "swim")

        ghostControls = GhostWalker()
        ghostControls.setWallBitMask(ghostBitmask)
        ghostControls.setFloorBitMask(floorBitmask)
        ghostControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        self.controlManager.add(ghostControls, "ghost")

        observerControls = ObserverWalker()
        observerControls.setWallBitMask(ghostBitmask)
        observerControls.setFloorBitMask(floorBitmask)
        observerControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        self.controlManager.add(observerControls, "observer")

        self.controlManager.use("walk", self)
        self.controlManager.disable()

    def initializeCollisions(self):
        """
        Set up the local avatar for collisions
        """
        self.setupControls()

    def deleteCollisions(self):
        self.controlManager.deleteCollisions()
        self.ignore("entero157")
        del self.cTrav

    def collisionsOff(self):
        self.controlManager.collisionsOff()

    def collisionsOn(self):
        self.controlManager.collisionsOn()

    def stopJumpLandTask(self):
        if self.jumpLandAnimFixTask:
            self.jumpLandAnimFixTask.remove()
            self.jumpLandAnimFixTask = None

    def jumpStart(self):
        if not self.sleepFlag and self.hp > 0:
            self.b_setAnimState("jumpAirborne", 1.0)
            self.stopJumpLandTask()

    def returnToWalk(self, task):
        if self.sleepFlag:
            state = "Sleep"
        elif self.hp > 0:
            state = "Happy"
        else:
            state = "Sad"
        self.b_setAnimState(state, 1.0)
        return Task.done

    def jumpLandAnimFix(self, jumpTime):
        if self.playingAnim != "run" and self.playingAnim != "walk":
            return taskMgr.doMethodLater(jumpTime, self.returnToWalk, self.uniqueName("walkReturnTask"))

    def jumpHardLand(self):
        if self.allowHardLand():
            self.b_setAnimState("jumpLand", 1.0)
            self.stopJumpLandTask()
            self.jumpLandAnimFixTask = self.jumpLandAnimFix(1.0)

        if self.d_broadcastPosHpr:
            self.d_broadcastPosHpr()

    def jumpLand(self):
        self.jumpLandAnimFixTask = self.jumpLandAnimFix(0.01)

        if self.d_broadcastPosHpr:
            self.d_broadcastPosHpr()

    def setupAnimationEvents(self):
        assert self.notify.debugStateCall(self)
        self.accept("jumpStart", self.jumpStart, [])
        self.accept("jumpHardLand", self.jumpHardLand, [])
        self.accept("jumpLand", self.jumpLand, [])

    def ignoreAnimationEvents(self):
        assert self.notify.debugStateCall(self)
        self.ignore("jumpStart")
        self.ignore("jumpHardLand")
        self.ignore("jumpLand")

    def allowHardLand(self):
        return (not self.sleepFlag) and (self.hp > 0)

    def enableAvatarControls(self):
        """
        Activate the tab, page up, arrow keys, etc.
        """
        assert self.notify.debugStateCall(self)
        if self.avatarControlsEnabled:
            return
        self.avatarControlsEnabled = 1
        self.setupAnimationEvents()
        self.controlManager.enable()

    def disableAvatarControls(self):
        """
        Ignore the tab, page up, arrow keys, etc.
        """
        assert self.notify.debugStateCall(self)
        if not self.avatarControlsEnabled:
            return
        self.avatarControlsEnabled = 0
        self.ignoreAnimationEvents()
        self.controlManager.setWASDTurn(1)
        self.controlManager.disable()

    def setWalkSpeedNormal(self):
        self.controlManager.setSpeeds(ToonRunSpeed, ToonJumpForce, ToonReverseSpeed, ToonRotateSpeed)

    def setWalkSpeedSlow(self):
        self.controlManager.setSpeeds(
            ToonForwardSpeedSlow, ToonJumpForceSlow, ToonReverseSpeedSlow, ToonRotateSpeedSlow
        )

    def getClampedAvatarHeight(self):
        return max(self.getHeight(), 3.0)

    def getGeom(self):
        return render

    def setCameraFov(self, fov):
        """Sets the camera to a particular fov and remembers this
        fov, so that things like page up and page down that
        temporarily change fov will restore it properly."""

        self.fov = fov
        base.camLens.setFov(self.fov)

    def resetCameraFov(self):
        self.cmod.lerpFov(self.fov, 0.4)

    def lerpCameraFov(self, *args):
        self.cmod.lerpFov(*args)

    def gotoNode(self, node, eyeHeight=3):
        """gotoNode(self, NodePath node)

        Puts the avatar at a suitable point nearby, and facing, the
        indicated NodePath, whatever it might be.  This will normally
        be another avatar, as in Goto Friend.
        """
        possiblePoints = (
            Point3(3, 6, 0),
            Point3(-3, 6, 0),
            Point3(6, 6, 0),
            Point3(-6, 6, 0),
            Point3(3, 9, 0),
            Point3(-3, 9, 0),
            Point3(6, 9, 0),
            Point3(-6, 9, 0),
            Point3(9, 9, 0),
            Point3(-9, 9, 0),
            Point3(6, 0, 0),
            Point3(-6, 0, 0),
            Point3(6, 3, 0),
            Point3(-6, 3, 0),
            Point3(9, 9, 0),
            Point3(-9, 9, 0),
            Point3(0, 12, 0),
            Point3(3, 12, 0),
            Point3(-3, 12, 0),
            Point3(6, 12, 0),
            Point3(-6, 12, 0),
            Point3(9, 12, 0),
            Point3(-9, 12, 0),
            Point3(0, -6, 0),
            Point3(-3, -6, 0),
            Point3(0, -9, 0),
            Point3(-6, -9, 0),
        )

        for point in possiblePoints:
            pos = self.positionExaminer.consider(node, point, eyeHeight)
            if pos:
                self.setPos(node, pos)
                self.lookAt(node)

                self.setHpr(self.getH() + random.choice((-10, 10)), 0, 0)
                return

        self.setPos(node, 0, 0, 0)

    def setCustomMessages(self, customMessages):
        self.customMessages = customMessages
        messenger.send("customMessagesChanged")

    def displayWhisper(self, fromId, chatString, whisperType):
        """displayWhisper(self, int fromId, string chatString, int whisperType)

        Displays the whisper message in whatever capacity makes sense.
        This function overrides a similar function in DistributedAvatar.
        """
        sender = None
        sfx = self.soundWhisper

        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            if sender == None:
                return
            chatString = sender.getName() + ": " + chatString

        whisper = WhisperPopup(chatString, getInterfaceFont(), whisperType)
        if sender != None:
            whisper.setClickable(sender.getName(), fromId)

        whisper.manage(base.marginManager)
        base.playSfx(sfx)

    def setAnimMultiplier(self, value):
        """setAnimMultiplier(self, float)
        Setter for anim playback speed multiplier
        """
        self.animMultiplier = value

    def getAnimMultiplier(self):
        """
        Getter for anim playback speed multiplier
        """
        return self.animMultiplier

    def enableRun(self):
        moveForward = base.MOVE_FORWARD
        moveBackwards = base.MOVE_BACKWARDS
        self.accept(moveForward, self.startRunWatch)
        self.accept(moveBackwards, self.stopRunWatch)
        self.accept(f"control-{moveForward}", self.startRunWatch)
        self.accept(f"control-{moveForward}-up", self.stopRunWatch)
        self.accept(f"alt-{moveForward}", self.startRunWatch)
        self.accept(f"alt-{moveForward}-up", self.stopRunWatch)
        self.accept(f"shift-{moveForward}", self.startRunWatch)
        self.accept(f"shift-{moveForward}-up", self.stopRunWatch)

    def disableRun(self):
        moveForward = base.MOVE_FORWARD
        self.ignore(f"{moveForward}")
        self.ignore(f"{moveForward}-up")
        self.ignore(f"control-{moveForward}-up")
        self.ignore(f"control-{moveForward}-up")
        self.ignore(f"alt-{moveForward}")
        self.ignore(f"alt-{moveForward}-up")
        self.ignore(f"shift-{moveForward}")
        self.ignore(f"shift-{moveForward}-up")

    def startRunWatch(self):
        def setRun(ignored):
            messenger.send("running-on")

        taskMgr.doMethodLater(self.runTimeout, setRun, self.uniqueName("runWatch"))
        return Task.cont

    def stopRunWatch(self):
        taskMgr.remove(self.uniqueName("runWatch"))
        messenger.send("running-off")
        return Task.cont

    def runSound(self):
        self.soundWalk.stop()
        base.playSfx(self.soundRun, looping=1)

    def walkSound(self):
        self.soundRun.stop()
        base.playSfx(self.soundWalk, looping=1)

    def stopSound(self):
        self.soundRun.stop()
        self.soundWalk.stop()

    def wakeUp(self):
        if self.sleepCallback != None:
            taskMgr.remove(self.uniqueName("sleepwatch"))
            self.startSleepWatch(self.sleepCallback)
        self.lastMoved = globalClock.getFrameTime()
        if self.sleepFlag:
            self.sleepFlag = 0

    def gotoSleep(self):
        if not self.sleepFlag:
            self.b_setAnimState("Sleep", self.animMultiplier)
            self.sleepFlag = 1

    def forceGotoSleep(self):
        if self.hp > 0:
            self.sleepFlag = 0
            self.gotoSleep()

    def startSleepWatch(self, callback):
        self.sleepCallback = callback
        taskMgr.doMethodLater(self.sleepTimeout, callback, self.uniqueName("sleepwatch"))

    def stopSleepWatch(self):
        taskMgr.remove(self.uniqueName("sleepwatch"))
        self.sleepCallback = None

    def startSleepSwimTest(self):
        """
        Spawn a task to check for sleep, this is normally handled by trackAnimToSpeed for some reason
        Sleepwatch appears to be a simple timeout for the sticker book

        """
        taskName = self.taskName("sleepSwimTest")

        taskMgr.remove(taskName)
        task = Task.Task(self.sleepSwimTest)

        self.lastMoved = globalClock.getFrameTime()
        self.lastState = None
        self.lastAction = None

        self.sleepSwimTest(task)
        taskMgr.add(self.sleepSwimTest, taskName, 35)

    def stopSleepSwimTest(self):
        taskName = self.taskName("sleepSwimTest")
        taskMgr.remove(taskName)
        self.stopSound()

    def sleepSwimTest(self, task):
        now = globalClock.getFrameTime()
        speed, rotSpeed, slideSpeed = self.controlManager.getSpeeds()
        if speed != 0.0 or rotSpeed != 0.0 or inputState.isSet("jump"):
            if not self.swimmingFlag:
                self.swimmingFlag = 1
        else:
            if self.swimmingFlag:
                self.swimmingFlag = 0
        if self.swimmingFlag or self.hp <= 0:
            self.wakeUp()
        else:
            if not self.sleepFlag:
                now = globalClock.getFrameTime()
                if now - self.lastMoved > self.swimTimeout:
                    self.swimTimeoutAction()
                    return Task.done

        return Task.cont

    def swimTimeoutAction(self):
        pass

    def trackAnimToSpeed(self, task):
        speed, rotSpeed, slideSpeed = self.controlManager.getSpeeds()

        if speed != 0.0 or rotSpeed != 0.0 or slideSpeed != 0.0 or inputState.isSet("jump"):
            if not self.movingFlag:
                self.movingFlag = 1

                self.stopLookAround()
        else:
            if self.movingFlag:
                self.movingFlag = 0

                self.startLookAround()

        if self.movingFlag or self.hp <= 0:
            self.wakeUp()
        else:
            if not self.sleepFlag:
                now = globalClock.getFrameTime()
                if now - self.lastMoved > self.sleepTimeout:
                    self.gotoSleep()

        state = None
        if self.sleepFlag:
            state = "Sleep"
        elif self.hp > 0:
            state = "Happy"
        else:
            state = "Sad"

        if state != self.lastState:
            self.lastState = state
            self.b_setAnimState(state, self.animMultiplier)
            if state == "Sad":
                self.setWalkSpeedSlow()
            else:
                self.setWalkSpeedNormal()

        action = self.setSpeed(speed, rotSpeed)
        if action != self.lastAction:
            self.lastAction = action
            if self.emoteTrack:
                self.emoteTrack.finish()
                self.emoteTrack = None
            if action == WALK_INDEX or action == REVERSE_INDEX:
                self.walkSound()
            elif action == RUN_INDEX or action == STRAFE_LEFT_INDEX or action == STRAFE_RIGHT_INDEX:
                self.runSound()
            else:
                self.stopSound()

        return Task.cont

    def hasTrackAnimToSpeed(self):
        taskName = self.taskName("trackAnimToSpeed")
        return taskMgr.hasTaskNamed(taskName)

    def startTrackAnimToSpeed(self):
        """
        Spawn a task to match avatar animation with movement speed

            if speed < 0 -> play walk cycle backwards
            if speed = 0
               if rotSpeed = 0 -> neutral cycle
               else -> walk cycle
            if speed > 0 and speed < runCutOff -> walk cycle
            if speed >= runCutOff -> run cycle
        """
        taskName = self.taskName("trackAnimToSpeed")

        taskMgr.remove(taskName)
        task = Task.Task(self.trackAnimToSpeed)

        self.lastMoved = globalClock.getFrameTime()
        self.lastState = None
        self.lastAction = None

        self.trackAnimToSpeed(task)
        taskMgr.add(self.trackAnimToSpeed, taskName, 35)

    def stopTrackAnimToSpeed(self):
        taskName = self.taskName("trackAnimToSpeed")
        taskMgr.remove(taskName)
        self.stopSound()

    def startChat(self):
        self.chatMgr.start()
        self.accept(ThinkPosHotkey, self.thinkPos)

    def stopChat(self):
        self.chatMgr.stop()
        self.ignore(ThinkPosHotkey)

    def d_broadcastPositionNow(self):
        """
        Forces a broadcast of the toon's current position.  Normally
        this is called immediately before calling
        setParent(OTPGlobals.SPRender), to ensure the remote
        clients don't observe this toon momentarily in the wrong place
        when he appears.
        """
        self.d_clearSmoothing()
        self.d_broadcastPosHpr()

    def d_setParent(self, parentToken):
        DistributedSmoothNode.DistributedSmoothNode.d_setParent(self, parentToken)

    def canChat(self):
        """
        Overrided by derived class
        """
        assert False
