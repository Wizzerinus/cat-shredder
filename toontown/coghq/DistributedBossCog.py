import random

from direct.controls.ControlManager import CollisionHandlerRayStart
from direct.distributed.ClockDelta import globalClockDelta
from direct.interval.ActorInterval import ActorInterval
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpFunctionInterval
from direct.interval.MetaInterval import Parallel, ParallelEndTogether, Sequence
from direct.showbase import PythonUtil
from direct.showbase import Transitions
from panda3d.core import *
from panda3d.otp import NametagGlobals

from otp.avatar import DistributedAvatar
from toontown.distributed import DelayDelete
from toontown.elevators import ElevatorConstants, ElevatorUtils
from toontown.toonbase.globals.TTGlobalsBosses import *
from toontown.toonbase.globals.TTGlobalsMovement import *
from toontown.toonbase.globals.TTGlobalsRender import *
from toontown.world import ZoneUtil
from . import BossCog


class DistributedBossCog(DistributedAvatar.DistributedAvatar, BossCog.BossCog):
    notify = directNotify.newCategory("DistributedBossCog")

    allowClickedNameTag = True

    def __init__(self, cr):
        DistributedAvatar.DistributedAvatar.__init__(self, cr)
        BossCog.BossCog.__init__(self)

        self.gotAllToons = 0
        self.toonsA = []
        self.toonsB = []
        self.involvedToons = []
        self.toonRequest = None
        self.arenaSide = 0

        self.toonSphere = None
        self.localToonIsSafe = 0

        self.__toonsStuckToFloor = []
        self.cqueue = None
        self.rays = None
        self.ray1 = None
        self.ray2 = None
        self.ray3 = None
        self.e1 = None
        self.e2 = None
        self.e3 = None

        self.activeIntervals = {}
        self.flashInterval = None

        self.elevatorType = ElevatorConstants.ELEVATOR_VP

    def announceGenerate(self):
        DistributedAvatar.DistributedAvatar.announceGenerate(self)

        nearBubble = CollisionSphere(0, 0, 0, 50)
        nearBubble.setTangible(0)
        nearBubbleNode = CollisionNode("NearBoss")
        nearBubbleNode.setCollideMask(WallBitmask)
        nearBubbleNode.addSolid(nearBubble)
        self.attachNewNode(nearBubbleNode)
        self.accept("enterNearBoss", self.avatarNearEnter)
        self.accept("exitNearBoss", self.avatarNearExit)

        self.collNode.removeSolid(0)
        tube1 = CollisionTube(6.5, -7.5, 2, 6.5, 7.5, 2, 2.5)
        tube2 = CollisionTube(-6.5, -7.5, 2, -6.5, 7.5, 2, 2.5)
        roof = CollisionPolygon(
            Point3(-4.4, 7.1, 5.5), Point3(-4.4, -7.1, 5.5), Point3(4.4, -7.1, 5.5), Point3(4.4, 7.1, 5.5)
        )
        side1 = CollisionPolygon(
            Point3(-4.4, -7.1, 5.5), Point3(-4.4, 7.1, 5.5), Point3(-4.4, 7.1, 0), Point3(-4.4, -7.1, 0)
        )
        side2 = CollisionPolygon(
            Point3(4.4, 7.1, 5.5), Point3(4.4, -7.1, 5.5), Point3(4.4, -7.1, 0), Point3(4.4, 7.1, 0)
        )
        front1 = CollisionPolygon(
            Point3(4.4, -7.1, 5.5), Point3(-4.4, -7.1, 5.5), Point3(-4.4, -7.1, 5.2), Point3(4.4, -7.1, 5.2)
        )
        back1 = CollisionPolygon(
            Point3(-4.4, 7.1, 5.5), Point3(4.4, 7.1, 5.5), Point3(4.4, 7.1, 5.2), Point3(-4.4, 7.1, 5.2)
        )
        self.collNode.addSolid(tube1)
        self.collNode.addSolid(tube2)
        self.collNode.addSolid(roof)
        self.collNode.addSolid(side1)
        self.collNode.addSolid(side2)
        self.collNode.addSolid(front1)
        self.collNode.addSolid(back1)
        self.collNodePath.reparentTo(self.axle)
        self.collNode.setCollideMask(PieBitmask | WallBitmask | CameraBitmask)

        self.collNode.setName("BossZap")
        self.setTag("attackCode", str(BossCogElectricFence))
        self.accept("enterBossZap", self.__touchedBoss)

        bubbleL = CollisionSphere(10, -5, 0, 10)
        bubbleL.setTangible(0)
        bubbleLNode = CollisionNode("BossZap")
        bubbleLNode.setCollideMask(WallBitmask)
        bubbleLNode.addSolid(bubbleL)
        self.bubbleL = self.axle.attachNewNode(bubbleLNode)
        self.bubbleL.setTag("attackCode", str(BossCogSwatLeft))
        self.bubbleL.stash()

        bubbleR = CollisionSphere(-10, -5, 0, 10)
        bubbleR.setTangible(0)
        bubbleRNode = CollisionNode("BossZap")
        bubbleRNode.setCollideMask(WallBitmask)
        bubbleRNode.addSolid(bubbleR)
        self.bubbleR = self.axle.attachNewNode(bubbleRNode)
        self.bubbleR.setTag("attackCode", str(BossCogSwatRight))
        self.bubbleR.stash()

        bubbleF = CollisionSphere(0, -25, 0, 12)
        bubbleF.setTangible(0)
        bubbleFNode = CollisionNode("BossZap")
        bubbleFNode.setCollideMask(WallBitmask)
        bubbleFNode.addSolid(bubbleF)
        self.bubbleF = self.rotateNode.attachNewNode(bubbleFNode)
        self.bubbleF.setTag("attackCode", str(BossCogFrontAttack))
        self.bubbleF.stash()

    def disable(self):
        DistributedAvatar.DistributedAvatar.disable(self)

        self.cr.relatedObjectMgr.abortRequest(self.toonRequest)
        self.toonRequest = None

    def delete(self):
        if hasattr(self, "DistributedBossCog_deleted"):
            raise RuntimeError("bro")
        self.DistributedBossCog_deleted = True
        self.ignoreAll()
        DistributedAvatar.DistributedAvatar.delete(self)
        BossCog.BossCog.delete(self)

    def setDNAString(self, dnaString):
        BossCog.BossCog.setDNAString(self, dnaString)

    def getDNAString(self):
        return self.dna.makeNetString()

    def setDNA(self, dna):
        BossCog.BossCog.setDNA(self, dna)

    def setToonIds(self, involvedToons, toonsA, toonsB):
        self.involvedToons = involvedToons
        self.toonsA = toonsA
        self.toonsB = toonsB

        self.cr.relatedObjectMgr.abortRequest(self.toonRequest)
        self.gotAllToons = 0
        self.toonRequest = self.cr.relatedObjectMgr.requestObjects(
            self.involvedToons, allCallback=self.__gotAllToons, eachCallback=self.gotToon
        )

    def getDialogueArray(self, *args):
        return BossCog.BossCog.getDialogueArray(self, *args)

    def storeInterval(self, interval, name):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if hasattr(ival, "delayDelete") or hasattr(ival, "delayDeletes"):
                self.clearInterval(name, finish=1)
        self.activeIntervals[name] = interval

    def cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()
            DelayDelete.cleanupDelayDeletes(interval)
        self.activeIntervals = {}

    def clearInterval(self, name, finish=1):
        """Clean up the specified Interval"""
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if name in self.activeIntervals:
                DelayDelete.cleanupDelayDeletes(ival)
                del self.activeIntervals[name]
        else:
            self.notify.debug("interval: %s already cleared" % name)

    def finishInterval(self, name):
        """Force the specified Interval to jump to the end"""
        if name in self.activeIntervals:
            interval = self.activeIntervals[name]
            interval.finish()

    def d_avatarEnter(self):
        assert self.notify.debug("d_avatarEnter()")
        self.sendUpdate("avatarEnter", [])

    def d_avatarExit(self):
        assert self.notify.debug("d_avatarExit()")
        self.sendUpdate("avatarExit", [])

    def avatarNearEnter(self, entry):
        self.sendUpdate("avatarNearEnter", [])

    def avatarNearExit(self, entry):
        self.sendUpdate("avatarNearExit", [])

    def hasLocalToon(self):
        doId = base.localAvatar.doId
        return (doId in self.toonsA) or (doId in self.toonsB)

    def setArenaSide(self, arenaSide):
        self.arenaSide = arenaSide

    def setState(self, state):
        self.request(state)

    def gotToon(self, toon):
        stateName = self.state
        assert self.notify.debug("gotToon(%s) in state %s" % (toon.doId, stateName))

    def __gotAllToons(self, toons):
        assert self.notify.debug("gotAllToons()")
        self.gotAllToons = 1
        messenger.send("gotAllToons")

    def controlToons(self):
        assert self.notify.debug("controlToons")
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.stopLookAround()
                toon.stopSmooth()

        if self.hasLocalToon():
            self.toMovieMode()

    def enableLocalToonSimpleCollisions(self):
        if not self.toonSphere:
            sphere = CollisionSphere(0, 0, 1, 1)
            sphere.setRespectEffectiveNormal(0)
            sphereNode = CollisionNode("SimpleCollisions")
            sphereNode.setFromCollideMask(WallBitmask | FloorBitmask)
            sphereNode.setIntoCollideMask(BitMask32.allOff())
            sphereNode.addSolid(sphere)
            self.toonSphere = NodePath(sphereNode)
            self.toonSphereHandler = CollisionHandlerPusher()
            self.toonSphereHandler.addCollider(self.toonSphere, base.localAvatar)
        self.toonSphere.reparentTo(base.localAvatar)
        base.cTrav.addCollider(self.toonSphere, self.toonSphereHandler)

    def disableLocalToonSimpleCollisions(self):
        if self.toonSphere:
            base.cTrav.removeCollider(self.toonSphere)
            self.toonSphere.detachNode()

    def toOuchMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, "fsm"):
                place.setState("ouch")

    def toCraneMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, "fsm"):
                place.setState("crane")

    def toMovieMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, "fsm"):
                place.setState("movie")

    def toWalkMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, "fsm"):
                place.setState("walk")

    def toFinalBattleMode(self):
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, "fsm"):
                place.setState("finalBattle")

    def releaseToons(self, finalBattle=0):
        assert self.notify.debug("releaseToons %d" % finalBattle)
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.startLookAround()
                toon.startSmooth()
                toon.wrtReparentTo(render)

                if toon is base.localAvatar:
                    if finalBattle:
                        self.toFinalBattleMode()
                    else:
                        self.toWalkMode()

    def stickToonsToFloor(self):
        self.unstickToons()

        rayNode = CollisionNode("stickToonsToFloor")
        rayNode.addSolid(CollisionRay(0.0, 0.0, CollisionHandlerRayStart, 0.0, 0.0, -1.0))
        rayNode.setFromCollideMask(FloorBitmask)
        rayNode.setIntoCollideMask(BitMask32.allOff())
        ray = NodePath(rayNode)

        lifter = CollisionHandlerFloor()
        lifter.setOffset(FloorOffset)
        lifter.setReach(10.0)

        for toonId in self.involvedToons:
            toon = base.cr.doId2do.get(toonId)
            if toon:
                toonRay = ray.instanceTo(toon)
                lifter.addCollider(toonRay, toon)
                base.cTrav.addCollider(toonRay, lifter)
                self.__toonsStuckToFloor.append(toonRay)

    def unstickToons(self):
        for toonRay in self.__toonsStuckToFloor:
            base.cTrav.removeCollider(toonRay)
            toonRay.removeNode()
        self.__toonsStuckToFloor = []

    def stickBossToFloor(self):
        self.unstickBoss()

        self.ray1 = CollisionRay(0.0, 10.0, 20.0, 0.0, 0.0, -1.0)
        self.ray2 = CollisionRay(0.0, 0.0, 20.0, 0.0, 0.0, -1.0)
        self.ray3 = CollisionRay(0.0, -10.0, 20.0, 0.0, 0.0, -1.0)

        rayNode = CollisionNode("stickBossToFloor")
        rayNode.addSolid(self.ray1)
        rayNode.addSolid(self.ray2)
        rayNode.addSolid(self.ray3)
        rayNode.setFromCollideMask(FloorBitmask)
        rayNode.setIntoCollideMask(BitMask32.allOff())
        self.rays = self.attachNewNode(rayNode)

        self.cqueue = CollisionHandlerQueue()
        base.cTrav.addCollider(self.rays, self.cqueue)

    def rollBoss(self, t, fromPos, deltaPos):
        self.setPos(fromPos + deltaPos * t)

        if not self.cqueue:
            return

        self.cqueue.sortEntries()
        numEntries = self.cqueue.getNumEntries()
        if numEntries != 0:
            for i in range(self.cqueue.getNumEntries() - 1, -1, -1):
                entry = self.cqueue.getEntry(i)
                solid = entry.getFrom()
                if solid == self.ray1:
                    self.e1 = entry
                elif solid == self.ray2:
                    self.e2 = entry
                elif solid == self.ray3:
                    self.e3 = entry
                else:
                    self.notify.warning("Unexpected ray in __liftBoss")
                    return

            self.cqueue.clearEntries()

        if not (self.e1 and self.e2 and self.e3):
            self.notify.debug("Some points missed in __liftBoss")
            return

        p1 = self.e1.getSurfacePoint(self)
        p2 = self.e2.getSurfacePoint(self)
        p3 = self.e3.getSurfacePoint(self)

        p2a = (p1 + p3) / 2

        center = p2a if p2a[2] > p2[2] else p2
        self.setZ(self, center[2])

        if p1[2] > p2[2] + 0.01 or p3[2] > p2[2] + 0.01:
            mat = Mat4(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            if abs(p3[2] - center[2]) < abs(p1[2] - center[2]):
                lookAt(mat, Vec3(p1 - center), CSDefault)
            else:
                lookAt(mat, Vec3(center - p3), CSDefault)
            self.rotateNode.setMat(mat)

        else:
            self.rotateNode.clearTransform()

    def unstickBoss(self):
        if self.rays:
            base.cTrav.removeCollider(self.rays)
            self.rays.removeNode()

        self.rays = None
        self.ray1 = None
        self.ray2 = None
        self.ray3 = None
        self.e1 = None
        self.e2 = None
        self.e3 = None
        self.rotateNode.clearTransform()

        self.cqueue = None

    def rollBossToPoint(self, fromPos, fromHpr, toPos, toHpr, reverse):
        vector = Vec3(toPos - fromPos)
        distance = vector.length()

        if toHpr is None:
            mat = Mat3(0, 0, 0, 0, 0, 0, 0, 0, 0)
            headsUp(mat, vector, CSDefault)
            scale = VBase3(0, 0, 0)
            shear = VBase3(0, 0, 0)
            toHpr = VBase3(0, 0, 0)
            decomposeMatrix(mat, scale, shear, toHpr, CSDefault)

        if fromHpr:
            newH = PythonUtil.fitDestAngle2Src(fromHpr[0], toHpr[0])
            toHpr = VBase3(newH, 0, 0)

        else:
            fromHpr = toHpr

        turnTime = abs(toHpr[0] - fromHpr[0]) / BossCogTurnSpeed
        leftRate = BossCogTreadSpeed if toHpr[0] < fromHpr[0] else -BossCogTreadSpeed
        rollTreadRate = -BossCogTreadSpeed if reverse else BossCogTreadSpeed

        rollTime = distance / BossCogRollSpeed
        deltaPos = toPos - fromPos
        track = Sequence(
            Func(self.setPos, fromPos),
            Func(self.headsUp, toPos),
            Parallel(
                self.hprInterval(turnTime, toHpr, fromHpr),
                self.rollLeftTreads(turnTime, leftRate),
                self.rollRightTreads(turnTime, -leftRate),
            ),
            Parallel(
                LerpFunctionInterval(self.rollBoss, duration=rollTime, extraArgs=[fromPos, deltaPos]),
                self.rollLeftTreads(rollTime, rollTreadRate),
                self.rollRightTreads(rollTime, rollTreadRate),
            ),
        )

        return track, toHpr

    def setupElevator(self, elevatorModel):
        self.elevatorModel = elevatorModel

        self.leftDoor = self.elevatorModel.find("**/left-door")
        if self.leftDoor.isEmpty():
            self.leftDoor = self.elevatorModel.find("**/left_door")
        self.rightDoor = self.elevatorModel.find("**/right-door")
        if self.rightDoor.isEmpty():
            self.rightDoor = self.elevatorModel.find("**/right_door")

        self.openSfx = base.loader.loadSfx("phase_9/audio/sfx/CHQ_FACT_door_open_sliding.ogg")
        self.finalOpenSfx = base.loader.loadSfx("phase_9/audio/sfx/CHQ_FACT_door_open_final.ogg")
        self.closeSfx = base.loader.loadSfx("phase_9/audio/sfx/CHQ_FACT_door_open_sliding.ogg")
        self.finalCloseSfx = base.loader.loadSfx("phase_9/audio/sfx/CHQ_FACT_door_open_final.ogg")
        self.openDoors = ElevatorUtils.getOpenInterval(
            self, self.leftDoor, self.rightDoor, self.openSfx, self.finalOpenSfx, self.elevatorType
        )
        self.closeDoors = ElevatorUtils.getCloseInterval(
            self, self.leftDoor, self.rightDoor, self.closeSfx, self.finalCloseSfx, self.elevatorType
        )

        self.closeDoors.start()
        self.closeDoors.finish()

    def placeToonInElevator(self, toon):
        self.putToonInCogSuit(toon)

        toonIndex = self.involvedToons.index(toon.doId)
        toon.reparentTo(self.elevatorModel)
        toon.setPos(*ElevatorConstants.BigElevatorPoints[toonIndex])
        toon.setHpr(180, 0, 0)
        toon.suit.loop("neutral")

    def toonDied(self, avId):
        assert self.notify.debug("toonDied(%s)" % (avId))

        if avId == base.localAvatar.doId:
            self.localToonDied()

    def localToonToSafeZone(self):
        assert self.notify.debug("localToonToSafeZone()")

        target_sz = ZoneUtil.getSafeZoneId(base.localAvatar.defaultZone)

        place = self.cr.playGame.getPlace()
        place.fsm.request(
            "teleportOut",
            [
                {
                    "loader": ZoneUtil.getLoaderName(target_sz),
                    "where": ZoneUtil.getWhereName(target_sz, 1),
                    "how": "teleportIn",
                    "hoodId": target_sz,
                    "zoneId": target_sz,
                    "shardId": None,
                    "avId": -1,
                }
            ],
        )

    def localToonDied(self):
        assert self.notify.debug("localToonToSafeZone()")

        target_sz = ZoneUtil.getSafeZoneId(base.localAvatar.defaultZone)

        place = self.cr.playGame.getPlace()
        place.fsm.request(
            "died",
            [
                {
                    "loader": ZoneUtil.getLoaderName(target_sz),
                    "where": ZoneUtil.getWhereName(target_sz, 1),
                    "how": "teleportIn",
                    "hoodId": target_sz,
                    "zoneId": target_sz,
                    "shardId": None,
                    "avId": -1,
                }
            ],
        )

    def __touchedBoss(self, entry):
        assert self.notify.debug("__touchedBoss()")

        self.notify.debug("%s" % entry)
        self.notify.debug("fromPos = %s" % entry.getFromNodePath().getPos(render))
        self.notify.debug("intoPos = %s" % entry.getIntoNodePath().getPos(render))
        attackCodeStr = entry.getIntoNodePath().getNetTag("attackCode")
        if attackCodeStr == "":
            self.notify.warning("Node %s has no attackCode tag." % (repr(entry.getIntoNodePath())))
            return
        attackCode = int(attackCodeStr)
        if attackCode == BossCogLawyerAttack and self.dna.dept != "l":
            self.notify.warning("got lawyer attack but not in CJ boss battle")
            return

        self.zapLocalToon(attackCode)

    def zapLocalToon(self, attackCode, origin=None):
        if self.localToonIsSafe or base.localAvatar.ghostMode or base.localAvatar.isStunned:
            return
        messenger.send("interrupt-pie")

        place = self.cr.playGame.getPlace()
        currentState = None
        if place:
            currentState = place.fsm.getCurrentState().getName()
        if currentState not in ("walk", "finalBattle", "crane"):
            return

        toon = base.localAvatar

        fling = 1
        shake = 0
        if attackCode == BossCogAreaAttack:
            fling = 0
            shake = 1

        if fling:
            if origin is None:
                origin = self

            camera.wrtReparentTo(render)
            toon.headsUp(origin)
            camera.wrtReparentTo(toon)

        bossRelativePos = toon.getPos(self.getGeomNode())
        bp2d = Vec2(bossRelativePos[0], bossRelativePos[1])
        bp2d.normalize()

        pos = toon.getPos()
        hpr = toon.getHpr()
        timestamp = globalClockDelta.getFrameNetworkTime()

        self.sendUpdate(
            "zapToon", [pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2], bp2d[0], bp2d[1], attackCode, timestamp]
        )

        self.doZapToon(toon, fling=fling, shake=shake)

    def showZapToon(self, toonId, x, y, z, h, p, r, attackCode, timestamp):
        if toonId == base.localAvatar.doId:
            return

        ts = globalClockDelta.localElapsedTime(timestamp)
        pos = Point3(x, y, z)
        hpr = VBase3(h, p, r)
        fling = 1

        toon = self.cr.doId2do.get(toonId)
        if toon:
            if attackCode == BossCogAreaAttack:
                pos = None
                hpr = None
                fling = 0

            else:
                ts -= toon.smoother.getDelay()

            self.doZapToon(toon, pos=pos, hpr=hpr, ts=ts, fling=fling)

    def doZapToon(self, toon, pos=None, hpr=None, ts=0, fling=1, shake=1):
        zapName = toon.uniqueName("zap")
        self.clearInterval(zapName)

        zapTrack = Sequence(name=zapName)

        if toon == base.localAvatar:
            self.toOuchMode()
            messenger.send("interrupt-pie")

            self.enableLocalToonSimpleCollisions()
        else:
            zapTrack.append(Func(toon.stopSmooth))

        def getSlideToPos(toon=toon):
            return render.getRelativePoint(toon, Point3(0, -5, 0))

        if pos is not None and hpr is not None:
            zapTrack.append(Func(toon.setPosHpr, pos, hpr)),

        toonTrack = Parallel()

        if shake and toon == base.localAvatar:
            toonTrack.append(
                Sequence(
                    Func(camera.setZ, camera, 1),
                    Wait(0.15),
                    Func(camera.setZ, camera, -2),
                    Wait(0.15),
                    Func(camera.setZ, camera, 1),
                )
            )

        if fling:
            toonTrack += [ActorInterval(toon, "slip-backward"), toon.posInterval(0.5, getSlideToPos, fluid=1)]
        else:
            toonTrack += [ActorInterval(toon, "slip-forward")]

        zapTrack.append(toonTrack)

        if toon == base.localAvatar:
            zapTrack.append(Func(self.disableLocalToonSimpleCollisions))
            currentState = self.state
            if currentState == "BattleThree" or hasattr(self, "chairs"):
                zapTrack.append(Func(self.toFinalBattleMode))
            else:
                zapTrack.append(Func(self.toWalkMode))
        else:
            zapTrack.append(Func(toon.startSmooth))

        if ts > 0:
            startTime = ts
        else:
            zapTrack = Sequence(Wait(-ts), zapTrack)
            startTime = 0

        zapTrack.append(Func(self.clearInterval, zapName))

        zapTrack.delayDelete = DelayDelete.DelayDelete(toon, "BossCog.doZapToon")
        zapTrack.start(startTime)
        self.storeInterval(zapTrack, zapName)

    def setAttackCode(self, attackCode, avId=0):
        assert self.notify.debug("setAttackCode(%s, %s) time=%f" % (attackCode, avId, globalClock.getFrameTime()))
        self.attackCode = attackCode
        self.attackAvId = avId

        if attackCode == BossCogDizzy:
            self.setDizzy(1)
            self.cleanupAttacks()
            self.doAnimate(None, raised=0, happy=1)

        elif attackCode == BossCogDizzyNow:
            self.setDizzy(1)
            self.cleanupAttacks()
            self.doAnimate("hit", happy=1, now=1)

        elif attackCode == BossCogSwatLeft:
            self.setDizzy(0)
            self.doAnimate("ltSwing", now=1)

        elif attackCode == BossCogSwatRight:
            self.setDizzy(0)
            self.doAnimate("rtSwing", now=1)

        elif attackCode == BossCogAreaAttack:
            self.setDizzy(0)
            self.doAnimate("areaAttack", now=1)

        elif attackCode in (BossCogFrontAttack, BossCogRecoverDizzyAttack):
            self.setDizzy(0)
            self.doAnimate("frontAttack", now=1)

        elif attackCode in (BossCogDirectedAttack, BossCogSlowDirectedAttack):
            self.setDizzy(0)
            self.doDirectedAttack(avId, attackCode)

        elif attackCode == BossCogNoAttack:
            self.setDizzy(0)
            self.doAnimate(None, raised=1)

    def cleanupAttacks(self):
        pass

    def cleanupFlash(self):
        if self.flashInterval:
            self.flashInterval.finish()
            self.flashInterval = None

    def flashRed(self):
        self.cleanupFlash()

        self.setColorScale(1, 1, 1, 1)
        i = Sequence(
            self.colorScaleInterval(0.1, colorScale=VBase4(1, 0, 0, 1)),
            self.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)),
        )
        self.flashInterval = i
        i.start()

    def flashGreen(self):
        self.cleanupFlash()

        if not self.isEmpty():
            self.setColorScale(1, 1, 1, 1)
            i = Sequence(
                self.colorScaleInterval(0.1, colorScale=VBase4(0, 1, 0, 1)),
                self.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)),
            )
            self.flashInterval = i
            i.start()

    def getGearFrisbee(self):
        return loader.loadModel("phase_9/models/char/gearProp")

    def doDirectedAttack(self, avId, attackCode):
        toon = base.cr.doId2do.get(avId)
        if toon:
            gearRoot = self.rotateNode.attachNewNode("gearRoot")
            gearRoot.setZ(10)
            gearRoot.setTag("attackCode", str(attackCode))
            gearModel = self.getGearFrisbee()
            gearModel.setScale(0.2)

            gearRoot.headsUp(toon)
            toToonH = PythonUtil.fitDestAngle2Src(0, gearRoot.getH() + 180)

            gearRoot.lookAt(toon)

            neutral = "Fb_neutral"
            if not self.twoFaced:
                neutral = "Ff_neutral"

            gearTrack = Parallel()
            for i in range(4):
                node = gearRoot.attachNewNode(str(i))
                node.hide()
                node.setPos(0, 5.85, 4.0)
                gearModel.instanceTo(node)
                x = random.uniform(-5, 5)
                z = random.uniform(-3, 3)
                h = random.uniform(-720, 720)
                gearTrack.append(
                    Sequence(
                        Wait(i * 0.15),
                        Func(node.show),
                        Parallel(
                            node.posInterval(1, Point3(x, 50, z), fluid=1),
                            node.hprInterval(1, VBase3(h, 0, 0), fluid=1),
                        ),
                        Func(node.detachNode),
                    )
                )

            if not self.raised:
                neutral1Anim = self.getAnim("down2Up")
                self.raised = 1
            else:
                neutral1Anim = ActorInterval(self, neutral, startFrame=48)

            throwAnim = self.getAnim("throw")
            neutral2Anim = ActorInterval(self, neutral)

            extraAnim = Sequence()
            if attackCode == BossCogSlowDirectedAttack:
                extraAnim = ActorInterval(self, neutral)

            seq = Sequence(
                ParallelEndTogether(self.pelvis.hprInterval(1, VBase3(toToonH, 0, 0)), neutral1Anim),
                extraAnim,
                Parallel(
                    Sequence(
                        Wait(0.19), gearTrack, Func(gearRoot.detachNode), self.pelvis.hprInterval(0.2, VBase3(0, 0, 0))
                    ),
                    Sequence(throwAnim, neutral2Anim),
                ),
            )

            self.doAnimate(seq, now=1, raised=1)

    def announceAreaAttack(self):
        if not getattr(base.localAvatar.controlManager.currentControls, "isAirborne", 0):
            self.zapLocalToon(BossCogAreaAttack)

    def loadEnvironment(self):
        self.elevatorMusic = base.loader.loadMusic("phase_7/audio/bgm/tt_elevator.ogg")
        self.stingMusic = base.loader.loadMusic("phase_7/audio/bgm/encntr_suit_winning_indoor.ogg")
        self.epilogueMusic = base.loader.loadMusic("phase_9/audio/bgm/encntr_hall_of_fame.ogg")

    def unloadEnvironment(self):
        pass

    def enterOff(self):
        assert self.notify.debug("enterOff()")
        self.cleanupIntervals()
        self.hide()
        self.clearChat()
        self.toWalkMode()

    def exitOff(self):
        self.show()

    def enterWaitForToons(self):
        assert self.notify.debug("enterWaitForToons()")

        self.cleanupIntervals()
        self.hide()

        if self.gotAllToons:
            self.__doneWaitForToons()
        else:
            self.accept("gotAllToons", self.__doneWaitForToons)

        self.transitions = Transitions.Transitions(loader)
        self.transitions.IrisModelName = "phase_3/models/misc/iris"
        self.transitions.FadeModelName = "phase_3/models/misc/fade"
        self.transitions.fadeScreen(alpha=1)

        NametagGlobals.setMasterArrowsOn(0)

    def __doneWaitForToons(self):
        self.doneBarrier("WaitForToons")

    def exitWaitForToons(self):
        self.show()

        self.transitions.noFade()
        del self.transitions
        NametagGlobals.setMasterArrowsOn(1)

    def enterElevator(self):
        assert self.notify.debug("enterElevator()")

        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.stopLookAround()
                toon.stopSmooth()
                self.placeToonInElevator(toon)

        self.toMovieMode()

        camera.reparentTo(self.elevatorModel)
        camera.setPosHpr(0, 30, 8, 180, 0, 0)

        base.playMusic(self.elevatorMusic, looping=1, volume=1.0)

        ival = Sequence(
            ElevatorUtils.getRideElevatorInterval(self.elevatorType),
            ElevatorUtils.getRideElevatorInterval(self.elevatorType),
            self.openDoors,
            Func(camera.wrtReparentTo, render),
            Func(self.__doneElevator),
        )

        intervalName = "ElevatorMovie"
        ival.start()
        self.storeInterval(ival, intervalName)

    def __doneElevator(self):
        self.doneBarrier("Elevator")

    def exitElevator(self):
        intervalName = "ElevatorMovie"
        self.clearInterval(intervalName)
        self.elevatorMusic.stop()

        ElevatorUtils.closeDoors(self.leftDoor, self.rightDoor, self.elevatorType)

    def enterIntroduction(self):
        assert self.notify.debug("enterIntroduction()")

        self.controlToons()

        ElevatorUtils.openDoors(self.leftDoor, self.rightDoor, self.elevatorType)

        NametagGlobals.setMasterArrowsOn(0)

        intervalName = "IntroductionMovie"
        delayDeletes = []

        seq = Sequence(self.makeIntroductionMovie(delayDeletes), Func(self.__beginBattleOne), name=intervalName)
        seq.delayDeletes = delayDeletes
        seq.start()
        self.storeInterval(seq, intervalName)

    def __beginBattleOne(self):
        intervalName = "IntroductionMovie"
        self.clearInterval(intervalName)

        self.doneBarrier("Introduction")

    def exitIntroduction(self):
        self.notify.debug("DistributedBossCog.exitIntroduction:")
        intervalName = "IntroductionMovie"
        self.clearInterval(intervalName)
        self.unstickToons()
        self.releaseToons()

        NametagGlobals.setMasterArrowsOn(1)

        ElevatorUtils.closeDoors(self.leftDoor, self.rightDoor, self.elevatorType)

    def enterBattleThree(self):
        assert self.notify.debug("enterBattleThree()")
        self.cleanupIntervals()
        self.releaseToons(finalBattle=1)
        NametagGlobals.setMasterArrowsOn(0)
        NametagGlobals.setMasterNametagsActive(1)

    def exitBattleThree(self):
        assert self.notify.debug("exitBattleThree()")
        self.cleanupIntervals()
