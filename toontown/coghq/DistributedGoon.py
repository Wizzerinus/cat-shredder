import random

from direct.distributed import ClockDelta
from direct.distributed.DistributedObject import DistributedObject
from direct.fsm import FSM
from direct.interval.ActorInterval import ActorInterval
from direct.interval.FunctionInterval import Func
from direct.interval.LerpInterval import LerpColorScaleInterval
from direct.interval.MetaInterval import Parallel, Sequence
from direct.interval.SoundInterval import SoundInterval
from direct.task.Task import Task
from panda3d.core import CollisionNode, CollisionSphere, VBase3, Vec4

from toontown.coghq import Goon, GoonDeath
from toontown.toonbase.globals.TTGlobalsMovement import *
from toontown.toonbase.globals.TTGlobalsRender import WallBitmask


class DistributedGoon(DistributedObject, Goon.Goon, FSM.FSM):
    notify = directNotify.newCategory("DistributedGoon")

    DistributedGoon_deleted = False
    DistributedGoon_initialized = False

    def __init__(self, cr):
        if self.DistributedGoon_initialized:
            return

        self.DistributedGoon_initialized = True
        DistributedObject.__init__(self, cr)
        Goon.Goon.__init__(self)
        FSM.FSM.__init__(self, "DistributedGoon")

        self.setCacheable(0)

        self.rayNode = None
        self.checkForWalls = 0
        self.triggerEvent = None

        self.animTrack = None
        self.walkTrack = None
        self.pauseTime = 0
        self.paused = 0
        self.path = None
        self.dir = GOON_FORWARD
        self.animMultiplier = 1.0
        self.isDead = 0
        self.isStunned = 0
        self.collapseSound = loader.loadSfx("phase_9/audio/sfx/CHQ_GOON_hunker_down.ogg")
        self.recoverSound = loader.loadSfx("phase_9/audio/sfx/CHQ_GOON_rattle_shake.ogg")
        self.attackSound = loader.loadSfx("phase_9/audio/sfx/CHQ_GOON_tractor_beam_alarmed.ogg")

    def announceGenerate(self):
        self.initGoon(getattr(self, "goonType", "n"))

        self.scaleRadar()

        self.colorHat()

        self.enterOff()
        taskMgr.doMethodLater(0.1, self.makeCollidable, self.taskName("makeCollidable"))

        self.setGoonScale(self.scale)
        self.animMultiplier = self.velocity / (ANIM_WALK_RATE * self.scale)
        self.setPlayRate(self.animMultiplier, "walk")

    def makeCollidable(self, task):
        """
        Initialize the collision and trigger for this goon. After this
        the goon is collidable, detecting the toon, and responsive to stun.
        """

        self.initCollisions()

        self.initializeBodyCollisions()
        triggerName = self.uniqueName("GoonTrigger")
        self.trigger.setName(triggerName)
        self.triggerEvent = f"enter{triggerName}"

        self.startToonDetect()

    def scaleRadar(self):
        Goon.Goon.scaleRadar(self)

        self.trigger = self.radar.find("**/trigger")

        triggerName = self.uniqueName("GoonTrigger")
        self.trigger.setName(triggerName)

    def initCollisions(self):
        self.cSphere = CollisionSphere(0.0, 0.0, 1.0, 1.0)
        self.cSphereNode = CollisionNode("goonCollSphere")
        self.cSphereNode.addSolid(self.cSphere)
        self.cSphereNodePath = self.head.attachNewNode(self.cSphereNode)
        self.cSphereNodePath.hide()
        self.cSphereBitMask = WallBitmask
        self.cSphereNode.setCollideMask(self.cSphereBitMask)
        self.cSphere.setTangible(1)

        self.sSphere = CollisionSphere(0.0, 0.0, self.headHeight + 0.8, 1.2)
        self.sSphereNode = CollisionNode("toonSphere")
        self.sSphereNode.addSolid(self.sSphere)
        self.sSphereNodePath = self.head.attachNewNode(self.sSphereNode)
        self.sSphereNodePath.hide()
        self.sSphereBitMask = WallBitmask
        self.sSphereNode.setCollideMask(self.sSphereBitMask)
        self.sSphere.setTangible(1)

    def initializeBodyCollisions(self, collIdStr=None):
        self.cSphereNode.setName(self.uniqueName("goonCollSphere"))
        self.sSphereNode.setName(self.uniqueName("toonSphere"))

        self.accept(self.uniqueName("entertoonSphere"), self.handleStun)

    def disableBodyCollisions(self):
        self.ignore(self.uniqueName("entertoonSphere"))

    def deleteCollisions(self):
        if hasattr(self, "sSphereNodePath"):
            self.sSphereNodePath.removeNode()
            del self.sSphereNodePath
            del self.sSphereNode
            del self.sSphere

        if hasattr(self, "cSphereNodePath"):
            self.cSphereNodePath.removeNode()
            del self.cSphereNodePath
            del self.cSphereNode
            del self.cSphere

    def disable(self):
        self.notify.debug(f"DistributedGoon {self.getDoId()}: disabling")
        self.ignoreAll()
        self.stopToonDetect()
        taskMgr.remove(self.taskName("resumeWalk"))
        taskMgr.remove(self.taskName("recoveryDone"))
        self.request("Off")
        self.disableBodyCollisions()
        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None
        if self.walkTrack:
            self.walkTrack.pause()
            self.walkTrack = None

    def delete(self):
        if self.DistributedGoon_deleted:
            return

        self.DistributedGoon_deleted = True
        self.notify.debug(f"DistributedGoon {self.getDoId()}: deleting")

        taskMgr.remove(self.taskName("makeCollidable"))

        self.deleteCollisions()
        self.head.removeNode()
        del self.head
        del self.attackSound
        del self.collapseSound
        del self.recoverSound
        Goon.Goon.cleanup(self)
        Goon.Goon.delete(self)

    def enterOff(self, *args):
        assert self.notify.debug("enterOff()")
        self.hideNametag3d()
        self.hideNametag2d()
        self.hide()
        self.isStunned = 0
        self.isDead = 0

        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None
        if self.walkTrack:
            self.walkTrack.pause()
            self.walkTrack = None

    def exitOff(self):
        self.show()
        self.showNametag3d()
        self.showNametag2d()

    def enterWalk(self, avId=None, ts=0):
        self.notify.debug(f"enterWalk, ts = {ts}")
        self.startToonDetect()
        self.loop("walk", 0)

        self.isStunned = 0

        if self.path:
            if not self.walkTrack:
                self.walkTrack = self.path.makePathTrack(
                    self, self.velocity, self.uniqueName("goonWalk"), turnTime=T_TURN
                )
            self.startWalk(ts)

    def startWalk(self, ts):
        tOffset = ts % self.walkTrack.getDuration()
        self.walkTrack.loop()
        self.walkTrack.pause()
        self.walkTrack.setT(tOffset)
        self.walkTrack.resume()
        self.paused = 0

    def exitWalk(self):
        self.notify.debug("exitWalk")
        self.stopToonDetect()
        if self.walkTrack and not self.paused:
            self.pauseTime = self.walkTrack.pause()
            self.paused = 1
        self.stop()

    def enterBattle(self, avId=None, ts=0):
        self.notify.debug("enterBattle")
        self.stopToonDetect()
        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None

        self.isStunned = 0
        self.animTrack = self.makeAttackTrack()
        self.animTrack.loop()

    def exitBattle(self):
        self.notify.debug("exitBattle")
        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None
        self.head.setHpr(0, 0, 0)

    def enterStunned(self, ts=0):
        self.ignore(self.uniqueName("entertoonSphere"))

        self.isStunned = 1

        self.notify.debug("enterStunned")
        if self.radar:
            self.radar.hide()

        self.animTrack = Parallel(
            Sequence(ActorInterval(self, "collapse"), Func(self.pose, "collapse", 48)),
            SoundInterval(self.collapseSound, node=self),
        )

        self.animTrack.start(ts)

    def exitStunned(self):
        self.notify.debug("exitStunned")
        if self.radar:
            self.radar.show()
        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None

        self.accept(self.uniqueName("entertoonSphere"), self.handleStun)

    def enterRecovery(self, ts=0, pauseTime=0):
        self.notify.debug("enterRecovery")

        self.ignore(self.uniqueName("entertoonSphere"))

        self.isStunned = 1

        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None

        self.animTrack = self.getRecoveryTrack()

        duration = self.animTrack.getDuration()
        self.animTrack.start(ts)

        delay = max(0, duration - ts)
        taskMgr.remove(self.taskName("recoveryDone"))
        taskMgr.doMethodLater(delay, self.recoveryDone, self.taskName("recoveryDone"), extraArgs=(pauseTime,))

    def getRecoveryTrack(self):
        return Parallel(
            Sequence(
                ActorInterval(self, "recovery"),
                Func(self.pose, "recovery", 96),
            ),
            Func(base.playSfx, self.recoverSound, node=self),
        )

    def recoveryDone(self, pauseTime):
        self.request("Walk", None, pauseTime)

    def exitRecovery(self):
        self.notify.debug("exitRecovery")
        taskMgr.remove(self.taskName("recoveryDone"))
        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None

        self.accept(self.uniqueName("entertoonSphere"), self.handleStun)

    def makeAttackTrack(self):
        return Parallel(
            Sequence(
                LerpColorScaleInterval(self.eye, 0.2, Vec4(1, 0, 0, 1)),
                LerpColorScaleInterval(self.eye, 0.2, Vec4(0, 0, 1, 1)),
                LerpColorScaleInterval(self.eye, 0.2, Vec4(1, 0, 0, 1)),
                LerpColorScaleInterval(self.eye, 0.2, Vec4(0, 0, 1, 1)),
                Func(self.eye.clearColorScale),
            ),
            SoundInterval(self.attackSound, node=self, volume=0.4),
        )

    def doDetect(self):
        pass

    def doAttack(self, avId):
        return

    def __startResumeWalkTask(self, ts):
        resumeTime = 1.5

        if ts < resumeTime:
            taskMgr.remove(self.taskName("resumeWalk"))
            taskMgr.doMethodLater(resumeTime - ts, self.request, self.taskName("resumeWalk"), extraArgs=("Walk",))
        else:
            self.request("Walk", ts - resumeTime)

    def __reverseWalk(self, task):
        self.request("Walk")

        return Task.done

    def __startRecoverTask(self, ts):
        stunTime = 4.0

        if ts < stunTime:
            taskMgr.remove(self.taskName("resumeWalk"))
            taskMgr.doMethodLater(stunTime - ts, self.request, self.taskName("resumeWalk"), extraArgs=("Recovery",))
        else:
            self.request("Recovery", ts - stunTime)

    def startToonDetect(self):
        self.radar.show()
        if self.triggerEvent:
            self.accept(self.triggerEvent, self.handleToonDetect)

    def stopToonDetect(self):
        if self.triggerEvent:
            self.ignore(self.triggerEvent)

    def handleToonDetect(self, collEntry=None):
        if base.localAvatar.isStunned:
            return

        if self.state == "Off":
            return

        self.stopToonDetect()

        self.request("Battle", base.localAvatar.doId)

        if self.walkTrack:
            self.pauseTime = self.walkTrack.pause()
            self.paused = 1

        if self.dclass and hasattr(self, "dclass"):
            self.sendUpdate("requestBattle", [self.pauseTime])
        else:
            self.notify.info("Goon deleted and still trying to call handleToonDetect()")

    def handleStun(self, collEntry):
        requestedStunned = False
        toon = base.localAvatar
        if toon:
            toonDistance = self.getPos(toon).length()
            if toonDistance > self.attackRadius:
                self.notify.warning("Stunned a goon, but outside of attack radius")
                return False

            self.request("Stunned")
            requestedStunned = True

        if self.walkTrack:
            self.pauseTime = self.walkTrack.pause()
            self.paused = 1

        self.sendUpdate("requestStunned", [self.pauseTime])
        return requestedStunned

    def setMovie(self, mode, avId, pauseTime, timestamp):
        """
        This is a message from the AI describing a movie for this goon
        """
        if self.isDead:
            return

        ts = ClockDelta.globalClockDelta.localElapsedTime(timestamp)
        self.notify.debug(f"{self.doId}: setMovie({mode},{avId},{pauseTime},{ts})")

        if mode == GOON_MOVIE_BATTLE:
            if self.state != "Battle":
                self.request("Battle", avId, ts)
        elif mode == GOON_MOVIE_STUNNED:
            if self.state != "Stunned":
                toon = base.cr.doId2do.get(avId)
                if toon:
                    toonDistance = self.getPos(toon).length()
                    if toonDistance > self.attackRadius:
                        self.notify.warning("Stunned a goon, but outside of attack radius")
                        return

                    self.request("Stunned", ts)
        elif mode == GOON_MOVIE_RECOVERY:
            if self.state != "Recovery":
                self.request("Recovery", ts, pauseTime)
        elif mode == GOON_MOVIE_SYNC:
            if self.walkTrack:
                self.walkTrack.pause()
                self.paused = 1
            if self.state in ("Off", "Walk"):
                self.request("Walk", avId, pauseTime + ts)
        else:
            if self.walkTrack:
                self.walkTrack.pause()
                self.walkTrack = None
            self.request("Walk", avId, pauseTime + ts)

    def stunToon(self, avId):
        self.notify.debug(f"stunToon({avId})")
        av = base.cr.doId2do.get(avId)
        if av is not None:
            av.stunToon()

    def isLocalToon(self, avId):
        if avId == base.localAvatar.doId:
            return 1
        return 0

    def playCrushMovie(self, crusherId, axis):
        goonPos = self.getPos()
        sx = random.uniform(0.3, 0.8) * self.scale
        sz = random.uniform(0.3, 0.8) * self.scale
        crushTrack = Sequence(
            GoonDeath.createGoonExplosion(self.getParent(), goonPos, VBase3(sx, 1, sz)),
            name=self.uniqueName("crushTrack"),
            autoFinish=1,
        )
        self.dead()
        crushTrack.start()

    def setVelocity(self, velocity):
        self.velocity = velocity
        self.animMultiplier = velocity / (ANIM_WALK_RATE * self.scale)
        self.setPlayRate(self.animMultiplier, "walk")

    def dead(self):
        if not self.isDead and not self.isDisabled():
            self.stopToonDetect()
            self.detachNode()
            self.isDead = 1

    def undead(self):
        if self.isDead:
            self.startToonDetect()
            self.reparentTo(render)
            self.isDead = 0

    def resync(self):
        if not self.isDead:
            self.sendUpdate("requestResync")

    def setHFov(self, hFov):
        if hFov != self.hFov:
            self.hFov = hFov
            if self.isGenerated():
                self.scaleRadar()

    def setAttackRadius(self, attackRadius):
        if attackRadius != self.attackRadius:
            self.attackRadius = attackRadius
            if self.isGenerated():
                self.scaleRadar()

    def setStrength(self, strength):
        if strength != self.strength:
            self.strength = strength
            if self.isGenerated():
                self.colorHat()

    def setGoonScale(self, scale):
        if scale != self.scale:
            self.scale = scale
            if self.isGenerated():
                self.getGeomNode().setScale(self.scale)
                self.scaleRadar()

    def setupGoon(self, velocity, hFov, attackRadius, strength, scale):
        self.setVelocity(velocity)
        self.setHFov(hFov)
        self.setAttackRadius(attackRadius)
        self.setStrength(strength)
        self.setGoonScale(scale)
