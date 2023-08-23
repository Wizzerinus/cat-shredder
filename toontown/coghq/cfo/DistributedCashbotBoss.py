import functools

from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
from direct.task.TaskManagerGlobal import *
from panda3d.core import (
    CollisionNode,
    CollisionPlane,
    CollisionPolygon,
    CollisionSphere,
    NodePath,
    Plane,
    Point3,
    TextNode,
    VBase3,
    Vec3,
)
from panda3d.direct import ShowInterval
from panda3d.otp import CFSpeech
from panda3d.physics import ForceNode, LinearEulerIntegrator, LinearVectorForce, PhysicsManager

from toontown.coghq.BossSpeedrunTimer import BossSpeedrunTimedTimer, BossSpeedrunTimer
from toontown.toonbase import TTLocalizer
from direct.task.Task import Task
from . import CraneLeagueGlobals, GeneralCFOGlobals
from direct.fsm import FSM
from toontown.coghq import BossHealthBar, DistributedBossCog
from .CashbotBossScoreboard import CashbotBossScoreboard
from .CraneLeagueHeatDisplay import CraneLeagueHeatDisplay
from toontown.coghq.ActivityLog import ActivityLog
from toontown.elevators import ElevatorConstants, ElevatorUtils
from toontown.toonbase.globals.TTGlobalsRender import *
from toontown.toonbase.globals import TTGlobalsBosses
from toontown.toonbase.globals.TTGlobalsGUI import getCompetitionFont

# This pointer keeps track of the one DistributedCashbotBoss that
# should appear within the avatar's current visibility zones.  If
# there is more than one DistributedCashbotBoss visible to a client at
# any given time, something is wrong.
OneBossCog = None


class DistributedCashbotBoss(DistributedBossCog.DistributedBossCog, FSM.FSM):
    notify = directNotify.newCategory("DistributedCashbotBoss")
    notify.debug("Debug mode is active")
    numFakeGoons = 3
    bossHealthBar = None

    BASE_HEAT = 500

    def __init__(self, cr):
        DistributedBossCog.DistributedBossCog.__init__(self, cr)
        FSM.FSM.__init__(self, "DistributedCashbotBoss")
        self.cranes = {}
        self.safes = {}
        self.goons = []
        self.elevatorType = ElevatorConstants.ELEVATOR_CFO

        # hack for quick access while debugging
        base.boss = self

        self.wantCustomCraneSpawns = False
        self.customSpawnPositions = {}
        self.ruleset = CraneLeagueGlobals.CFORuleset()  # Setup a default ruleset as a fallback
        self.scoreboard = None
        self.modifiers = []
        self.heatDisplay = CraneLeagueHeatDisplay()
        self.heatDisplay.hide()
        self.spectators = []
        self.localToonSpectating = False
        self.endVault = None
        self.warningSfx = None

        self.latency = 0.5  # default latency for updating object posHpr

        self.activityLog = ActivityLog()

        self.toonSpawnpointOrder = list(range(8))

    def setToonSpawnpoints(self, order):
        self.toonSpawnpointOrder = order

    def addToActivityLog(self, doId, content):
        doObj = base.cr.doId2do.get(doId)

        try:
            name = doObj.getName()
        except AttributeError:
            name = doId

        msg = "[%s]" % name
        msg += " %s" % content
        self.activityLog.addToLog(msg)

    def debug(self, doId="system", content="null"):
        if self.ruleset.GENERAL_DEBUG:
            self.addToActivityLog(doId, content)

    def goonStatesDebug(self, doId="system", content="null"):
        if self.ruleset.GOON_STATES_DEBUG:
            self.addToActivityLog(doId, content)

    def safeStatesDebug(self, doId="system", content="null"):
        if self.ruleset.SAFE_STATES_DEBUG:
            self.addToActivityLog(doId, content)

    def craneStatesDebug(self, doId="system", content="null"):
        self.notify.debug(f"{doId}: {content}")
        if self.ruleset.CRANE_STATES_DEBUG:
            self.addToActivityLog(doId, content)

    def updateSpectators(self, specs):
        self.spectators = specs
        if not self.localToonSpectating and base.localAvatar.doId in self.spectators:
            self.setLocalToonSpectating()
        elif self.localToonSpectating and base.localAvatar.doId not in self.spectators:
            self.disableLocalToonSpectating()

        for toonId in self.involvedToons:
            t = base.cr.doId2do.get(toonId)
            if t:
                if toonId in self.spectators:
                    t.hide()
                elif toonId in self.getInvolvedToonsNotSpectating():
                    t.show()

    def setLocalToonSpectating(self):
        self.localToonSpectating = True
        self.localToonIsSafe = True

    def disableLocalToonSpectating(self):
        self.localToonSpectating = False
        self.localToonIsSafe = False

    def getInvolvedToonsNotSpectating(self):
        toons = list(self.involvedToons)
        for s in self.spectators:
            if s in toons:
                toons.remove(s)

        return toons

    def announceGenerate(self):
        DistributedBossCog.DistributedBossCog.announceGenerate(self)
        self.bossSpeedrunTimer.cleanup()
        self.bossSpeedrunTimer = (
            BossSpeedrunTimedTimer(time_limit=self.ruleset.TIMER_MODE_TIME_LIMIT)
            if self.ruleset.TIMER_MODE
            else BossSpeedrunTimer()
        )
        self.bossSpeedrunTimer.hide()
        base.cr.forbidCheesyEffects(1)

        # at this point all our attribs have been filled in.
        self.setName(TTLocalizer.CashbotBossName)
        nameInfo = TTLocalizer.BossCogNameWithDept % {
            "name": TTLocalizer.CashbotBossName,
            "dept": "Cashbot",
        }
        self.setDisplayName(nameInfo)

        # Our goal in this battle is to drop stuff on the CFO's head.
        # For this, we need a target.
        target = CollisionSphere(2, 0, 0, 3)
        targetNode = CollisionNode("headTarget")
        targetNode.addSolid(target)
        targetNode.setCollideMask(PieBitmask)
        self.headTarget = self.neck.attachNewNode(targetNode)

        # And he gets a big bubble around his torso, just to keep
        # things from falling through him.  It's a big sphere so
        # things will tend to roll off him instead of landing on him.
        shield = CollisionSphere(0, 0, 0.8, 7)
        shieldNode = CollisionNode("shield")
        shieldNode.addSolid(shield)
        shieldNode.setCollideMask(PieBitmask)
        self.pelvis.attachNewNode(shieldNode)

        # By "heldObject", we mean the safe he's currently wearing as
        # a helmet, if any.  It's called a heldObject because this is
        # the way the cranes refer to the same thing, and we use the
        # same interface to manage this.
        self.heldObject = None
        self.bossDamage = 0

        # The BossCog actually owns the environment geometry.  Not
        # sure if this is a great idea, but it's the way we did it
        # with the sellbot boss, and the comment over there seems to
        # think it's a great idea. :)
        self.loadEnvironment()

        # Set up a physics manager for the cables and the objects
        # falling around in the room.
        self.physicsMgr = PhysicsManager()
        integrator = LinearEulerIntegrator()
        self.physicsMgr.attachLinearIntegrator(integrator)
        fn = ForceNode("gravity")
        self.fnp = self.geom.attachNewNode(fn)
        gravity = LinearVectorForce(0, 0, -32)
        fn.addForce(gravity)
        self.physicsMgr.addLinearForce(gravity)

        # Enable the special CFO chat menu.
        base.localAvatar.chatMgr.chatInputSpeedChat.addCFOMenu()

        # The crane round scoreboard
        self.scoreboard = CashbotBossScoreboard(ruleset=self.ruleset)
        self.scoreboard.hide()

        self.warningSfx = loader.loadSfx("phase_9/audio/sfx/CHQ_GOON_tractor_beam_alarmed.ogg")

        global OneBossCog
        if OneBossCog is not None:
            self.notify.warning("Multiple BossCogs visible.")
        OneBossCog = self

    def getBossMaxDamage(self):
        return self.ruleset.CFO_MAX_HP

    def calculateHeat(self):
        bonusHeat = 0
        # Loop through all modifiers present and calculate the bonus heat
        for modifier in self.modifiers:
            bonusHeat += modifier.getHeat()

        return self.BASE_HEAT + bonusHeat

    def updateRequiredElements(self):
        self.bossSpeedrunTimer.cleanup()
        self.bossSpeedrunTimer = (
            BossSpeedrunTimedTimer(time_limit=self.ruleset.TIMER_MODE_TIME_LIMIT)
            if self.ruleset.TIMER_MODE
            else BossSpeedrunTimer()
        )
        self.bossSpeedrunTimer.hide()
        # If the scoreboard was made then update the ruleset
        if self.scoreboard:
            self.scoreboard.set_ruleset(self.ruleset)

        self.heatDisplay.update(self.calculateHeat(), self.modifiers)

        if self.ruleset.WANT_BACKWALL:
            self.enableBackWall()
        else:
            self.disableBackWall()

    def setRawRuleset(self, attrs):
        self.ruleset = CraneLeagueGlobals.CFORuleset.fromStruct(attrs)
        self.updateRequiredElements()
        self.notify.info(("ruleset updated: " + str(self.ruleset)))

    def getRawRuleset(self):
        return self.ruleset.asStruct()

    def getRuleset(self):
        return self.ruleset

    def setModifiers(self, mods):
        modsToSet = []  # A list of CFORulesetModifierBase subclass instances
        for modStruct in mods:
            modsToSet.append(CraneLeagueGlobals.CFORulesetModifierBase.fromStruct(modStruct))

        self.modifiers = modsToSet
        self.modifiers.sort(key=lambda m: m.MODIFIER_TYPE)

    def disable(self):
        """
        This method is called when the DistributedObject
        is removed from active duty and stored in a cache.
        """
        global OneBossCog
        DistributedBossCog.DistributedBossCog.disable(self)
        base.cr.forbidCheesyEffects(0)
        self.demand("Off")
        self.unloadEnvironment()
        self.fnp.removeNode()
        self.physicsMgr.clearLinearForces()
        self.battleThreeMusic.stop()
        base.localAvatar.chatMgr.chatInputSpeedChat.removeCFOMenu()
        self.scoreboard.cleanup()
        self.heatDisplay.cleanup()
        if OneBossCog == self:
            OneBossCog = None

        del base.boss
        self.bossHealthBar.cleanup()

    def disableBackWall(self):
        if self.endVault is None:
            return

        cn = self.endVault.find("**/wallsCollision").node()
        if cn:
            cn.setIntoCollideMask(WallBitmask | PieBitmask)  # TTCC No Back Wall
        else:
            self.notify.warning("[Crane League] Failed to disable back wall.")

    def enableBackWall(self):
        if self.endVault is None:
            return

        cn = self.endVault.find("**/wallsCollision").node()
        if cn:
            cn.setIntoCollideMask(WallBitmask | PieBitmask | BitMask32.lowerOn(3) << 21)  # TTR Back Wall
        else:
            self.notify.warning("[Crane League] Failed to enable back wall.")

    ##### Environment #####

    def loadEnvironment(self):
        DistributedBossCog.DistributedBossCog.loadEnvironment(self)
        self.midVault = loader.loadModel("phase_10/models/cogHQ/MidVault.bam")
        self.endVault = loader.loadModel("phase_10/models/cogHQ/EndVault.bam")
        self.lightning = loader.loadModel("phase_10/models/cogHQ/CBLightning.bam")
        self.magnet = loader.loadModel("phase_10/models/cogHQ/CBMagnet.bam")
        self.craneArm = loader.loadModel("phase_10/models/cogHQ/CBCraneArm.bam")
        self.controls = loader.loadModel("phase_10/models/cogHQ/CBCraneControls.bam")
        self.stick = loader.loadModel("phase_10/models/cogHQ/CBCraneStick.bam")
        self.safe = loader.loadModel("phase_10/models/cogHQ/CBSafe.bam")
        self.eyes = loader.loadModel("phase_10/models/cogHQ/CashBotBossEyes.bam")
        self.cableTex = self.craneArm.findTexture("MagnetControl")

        # Get the eyes ready for putting outside the helmet.
        self.eyes.setPosHprScale(4.5, 0, -2.5, 90, 90, 0, 0.4, 0.4, 0.4)
        self.eyes.reparentTo(self.neck)
        self.eyes.hide()

        # Position the two rooms relative to each other, and so that
        # the floor is at z == 0
        self.midVault.setPos(0, -222, -70.7)
        self.endVault.setPos(84, -201, -6)
        self.geom = NodePath("geom")
        self.midVault.reparentTo(self.geom)
        self.endVault.reparentTo(self.geom)

        # Clear out unneeded backstage models from the EndVault, if
        # they're in the file.
        self.endVault.findAllMatches("**/MagnetArms").detach()
        self.endVault.findAllMatches("**/Safes").detach()
        self.endVault.findAllMatches("**/MagnetControlsAll").detach()

        # Flag the collisions in the end vault so safes and magnets
        # don't try to go through the wall.
        self.disableBackWall()

        # Get the rolling doors.

        # This is the door to Somewhere Else, through which the boss
        # makes his entrance.
        self.door1 = self.midVault.find("**/SlidingDoor1/")

        # This is the door from the mid vault to the end vault.
        # Everyone proceeds through this door to the final battle
        # scene.
        self.door2 = self.midVault.find("**/SlidingDoor/")

        # This is the door from the end vault back to the mid vault.
        # The boss makes his "escape" through this door.
        self.door3 = self.endVault.find("**/SlidingDoor/")

        # Load the elevator model
        elevatorModel = loader.loadModel("phase_10/models/cogHQ/CFOElevator")

        # Set up an origin for the elevator
        elevatorOrigin = self.midVault.find("**/elevator_origin")
        elevatorOrigin.setScale(1)

        elevatorModel.reparentTo(elevatorOrigin)

        leftDoor = elevatorModel.find("**/left_door")
        leftDoor.setName("left-door")
        rightDoor = elevatorModel.find("**/right_door")
        rightDoor.setName("right-door")
        self.setupElevator(elevatorOrigin)
        ElevatorUtils.closeDoors(leftDoor, rightDoor, ElevatorConstants.ELEVATOR_CFO)

        # Find all the wall polygons and replace them with planes,
        # which are solid, so there will be zero chance of safes or
        # toons slipping through a wall.
        walls = self.endVault.find("**/RollUpFrameCillison")
        walls.detachNode()
        self.evWalls = self.replaceCollisionPolysWithPlanes(walls)
        self.evWalls.reparentTo(self.endVault)

        # Initially, these new planar walls are stashed, so they don't
        # cause us trouble in the intro movie or in battle one.  We
        # will unstash them when we move to battle three.
        self.evWalls.stash()

        # Also replace the floor polygon with a plane, and rename it
        # so we can detect a collision with it.
        floor = self.endVault.find("**/EndVaultFloorCollision")
        floor.detachNode()
        self.evFloor = self.replaceCollisionPolysWithPlanes(floor)
        self.evFloor.reparentTo(self.endVault)
        self.evFloor.setName("floor")

        # Also, put a big plane across the universe a few feet below
        # the floor, to catch things that fall out of the world.
        plane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, -50)))
        planeNode = CollisionNode("dropPlane")
        planeNode.addSolid(plane)
        planeNode.setCollideMask(PieBitmask)
        self.geom.attachNewNode(planeNode)
        self.geom.reparentTo(render)

    def unloadEnvironment(self):
        DistributedBossCog.DistributedBossCog.unloadEnvironment(self)
        self.geom.removeNode()

    def replaceCollisionPolysWithPlanes(self, model):
        newCollisionNode = CollisionNode("collisions")
        newCollideMask = BitMask32(0)
        planes = []
        collList = model.findAllMatches("**/+CollisionNode")
        if not collList:
            collList = [model]
        for cnp in collList:
            cn = cnp.node()
            if not isinstance(cn, CollisionNode):
                self.notify.warning("Not a collision node: %s" % repr(cnp))
                break
            newCollideMask = newCollideMask | cn.getIntoCollideMask()
            for i in range(cn.getNumSolids()):
                solid = cn.getSolid(i)
                if isinstance(solid, CollisionPolygon):
                    # Save the plane defined by this polygon
                    plane = Plane(solid.getPlane())
                    planes.append(plane)
                else:
                    self.notify.warning("Unexpected collision solid: %s" % repr(solid))
                    newCollisionNode.addSolid(plane)

        newCollisionNode.setIntoCollideMask(newCollideMask)

        # Now sort all of the planes and remove the nonunique ones.
        # We can't use traditional dictionary-based tricks, because we
        # want to use Plane.compareTo(), not Plane.__hash__(), to make
        # the comparison.
        threshold = 0.1
        planes.sort(key=functools.cmp_to_key(lambda p1, p2: p1.compareTo(p2, threshold)))
        lastPlane = None
        for plane in planes:
            if lastPlane is None or plane.compareTo(lastPlane, threshold) != 0:
                cp = CollisionPlane(plane)
                newCollisionNode.addSolid(cp)
                lastPlane = plane

        return NodePath(newCollisionNode)

    def grabObject(self, obj):
        # Grab a safe and put it on as a helmet.  This method mirrors
        # a similar method on DistributedCashbotBossCrane.py; it goes
        # through the same API as a crane picking up a safe.

        # This is only called by DistributedCashbotBossObject.enterGrabbed().
        obj.wrtReparentTo(self.neck)
        obj.hideShadows()
        obj.stashCollisions()
        if obj.lerpInterval:
            obj.lerpInterval.finish()
        obj.lerpInterval = Parallel(
            obj.posInterval(GeneralCFOGlobals.CashbotBossToMagnetTime, Point3(-1, 0, 0.2)),
            obj.quatInterval(GeneralCFOGlobals.CashbotBossToMagnetTime, VBase3(0, -90, 90)),
            Sequence(Wait(GeneralCFOGlobals.CashbotBossToMagnetTime), ShowInterval(self.eyes)),
            obj.toMagnetSoundInterval,
        )
        obj.lerpInterval.start()
        self.heldObject = obj

    def dropObject(self, obj):
        # Drop a helmet on the ground.

        # This is only called by DistributedCashbotBossObject.exitGrabbed().
        assert self.heldObject == obj

        if obj.lerpInterval:
            obj.lerpInterval.finish()
            obj.lerpInterval = None

        obj = self.heldObject
        obj.wrtReparentTo(render)
        obj.setHpr(obj.getH(), 0, 0)
        self.eyes.hide()

        # Actually, we shouldn't reveal the shadows until it
        # reaches the ground again.  This will do for now.
        obj.showShadows()
        obj.unstashCollisions()

        self.heldObject = None

    def setBossDamage(self, bossDamage):
        if bossDamage > self.bossDamage:
            delta = bossDamage - self.bossDamage
            self.flashRed()

            # Animate the hit if the CFO should flinch
            if self.ruleset.CFO_FLINCHES_ON_HIT:
                self.doAnimate("hit", now=1)

            self.showHpText(-delta, scale=5)
        self.bossDamage = bossDamage
        self.updateHealthBar()
        if self.bossHealthBar:
            self.bossHealthBar.update(self.ruleset.CFO_MAX_HP - bossDamage, self.ruleset.CFO_MAX_HP)

    def setCraneSpawn(self, want, spawn, toonId):
        self.wantCustomCraneSpawns = want
        self.customSpawnPositions[toonId] = spawn

    def __doPhysics(self, task):
        dt = globalClock.getDt()
        self.physicsMgr.doPhysics(dt)
        return Task.cont

    ##### WaitForToons state #####
    def enterWaitForToons(self):
        DistributedBossCog.DistributedBossCog.enterWaitForToons(self)

        self.detachNode()
        self.geom.hide()

    def exitWaitForToons(self):
        DistributedBossCog.DistributedBossCog.exitWaitForToons(self)
        self.geom.show()

    def enterBattleThree(self):
        if self.bossHealthBar:
            self.bossHealthBar.cleanup()
        self.bossHealthBar = BossHealthBar.BossHealthBar(self.style)

        DistributedBossCog.DistributedBossCog.enterBattleThree(self)

        self.clearChat()
        self.reparentTo(render)

        self.setPosHpr(*GeneralCFOGlobals.CashbotBossBattleThreePosHpr)

        self.happy = 1
        self.raised = 1
        self.forward = 1
        self.doAnimate()

        self.endVault.unstash()
        self.evWalls.unstash()
        self.midVault.stash()

        base.cmod.enable()
        base.localAvatar.setCameraFov(BossBattleCameraFov)

        self.generateHealthBar()
        self.updateHealthBar()

        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9)

        # It is important to make sure this task runs immediately
        # before the collisionLoop of ShowBase.  That will fix up the
        # z value of the safes, etc., before their position is
        # distributed.
        taskMgr.add(self.__doPhysics, self.uniqueName("physics"), priority=25)

        # Display Health Bar
        self.bossHealthBar.initialize(self.ruleset.CFO_MAX_HP - self.bossDamage, self.ruleset.CFO_MAX_HP)

        # Display Boss Timer
        self.bossSpeedrunTimer.reset()
        self.bossSpeedrunTimer.start_updating()
        self.bossSpeedrunTimer.show()

        # Display Modifiers Heat
        self.heatDisplay.update(self.calculateHeat(), self.modifiers)
        self.heatDisplay.show()

        # Make all laff meters blink when in uber mode
        messenger.send("uberThreshold", [self.ruleset.LOW_LAFF_BONUS_THRESHOLD])

        self.localToonIsSafe = 0 if base.localAvatar.doId in self.getInvolvedToonsNotSpectating() else 1

        # Setup the scoreboard
        self.scoreboard.clearToons()
        for index, avId in enumerate(self.getInvolvedToonsNotSpectating()):
            toon = self.cr.doId2do.get(avId)
            if toon:
                x, y, z, h, p, r = CraneLeagueGlobals.TOON_SPAWN_POSITIONS[index]
                toon.setPos(x, y, z)
                toon.setHpr(h, p, r)
            if avId in base.cr.doId2do:
                self.scoreboard.addToon(avId)

    def saySomething(self, chatString):
        intervalName = "CFOTaunt"
        seq = Sequence(name=intervalName)
        seq.append(Func(self.setChatAbsolute, chatString, CFSpeech))
        seq.append(Wait(4.0))
        seq.append(Func(self.clearChat))
        oldSeq = self.activeIntervals.get(intervalName)
        if oldSeq:
            oldSeq.finish()
        seq.start()
        self.storeInterval(seq, intervalName)

    def setAttackCode(self, attackCode, avId=0):
        DistributedBossCog.DistributedBossCog.setAttackCode(self, attackCode, avId)
        if attackCode == TTGlobalsBosses.BossCogAreaAttack:
            self.saySomething(TTLocalizer.CashbotBossAreaAttackTaunt)
            base.playSfx(self.warningSfx)

    def exitBattleThree(self):
        DistributedBossCog.DistributedBossCog.exitBattleThree(self)
        bossDoneEventName = self.uniqueName("DestroyedBoss")
        self.ignore(bossDoneEventName)
        self.stopAnimate()
        self.cleanupAttacks()
        self.setDizzy(0)
        self.removeHealthBar()
        base.localAvatar.setCameraFov(DefaultCameraFov)
        if self.newState != "Victory":
            self.battleThreeMusic.stop()
        taskMgr.remove(self.uniqueName("physics"))

    def toonDied(self, avId):
        self.scoreboard.addScore(
            avId, self.ruleset.POINTS_PENALTY_GO_SAD, CraneLeagueGlobals.PENALTY_GO_SAD_TEXT, ignoreLaff=True
        )
        self.scoreboard.toonDied(avId)
        DistributedBossCog.DistributedBossCog.toonDied(self, avId)

    def localToonDied(self):
        DistributedBossCog.DistributedBossCog.localToonDied(self)
        self.localToonIsSafe = 1

    def killingBlowDealt(self, avId):
        self.scoreboard.addScore(avId, self.ruleset.POINTS_KILLING_BLOW, CraneLeagueGlobals.KILLING_BLOW_TEXT)

    def updateDamageDealt(self, avId, damageDealt):
        self.scoreboard.addScore(avId, damageDealt)
        self.scoreboard.addDamage(avId, damageDealt)

    def updateStunCount(self, avId, craneId):
        crane = base.cr.doId2do.get(craneId)
        if crane:
            self.scoreboard.addScore(avId, crane.getPointsForStun(), CraneLeagueGlobals.STUN_TEXT)
            self.scoreboard.addStun(avId)

    def updateGoonsStomped(self, avId):
        self.scoreboard.addScore(avId, self.ruleset.POINTS_GOON_STOMP, CraneLeagueGlobals.GOON_STOMP_TEXT)
        self.scoreboard.addStomp(avId)

    def updateSafePoints(self, avId, points):
        self.scoreboard.addScore(
            avId, points, CraneLeagueGlobals.PENALTY_SAFEHEAD_TEXT if points < 0 else CraneLeagueGlobals.DESAFE_TEXT
        )

    def updateMaxImpactHits(self, avId):
        self.scoreboard.addScore(avId, self.ruleset.POINTS_IMPACT, CraneLeagueGlobals.IMPACT_TEXT)

    def updateLowImpactHits(self, avId):
        self.scoreboard.addScore(avId, self.ruleset.POINTS_PENALTY_SANDBAG, CraneLeagueGlobals.PENALTY_SANDBAG_TEXT)

    def updateCombo(self, avId, comboLength):
        self.scoreboard.setCombo(avId, comboLength)

    def awardCombo(self, avId, comboLength, amount):
        self.scoreboard.addScore(avId, amount, reason="COMBO x" + str(comboLength) + "!")

    def announceCraneRestart(self):
        restartingOrEnding = "Restarting " if self.ruleset.RESTART_CRANE_ROUND_ON_FAIL else "Ending "
        title = OnscreenText(
            parent=aspect2d,
            text="All toons are sad!",
            style=3,
            fg=(0.8, 0.2, 0.2, 1),
            align=TextNode.ACenter,
            scale=0.15,
            pos=(0, 0.35),
            font=getCompetitionFont(),
        )
        sub = OnscreenText(
            parent=aspect2d,
            text=restartingOrEnding + "crane round in 10 seconds...",
            style=3,
            fg=(0.8, 0.8, 0.8, 1),
            align=TextNode.ACenter,
            scale=0.09,
            pos=(0, 0.2),
            font=getCompetitionFont(),
        )

        Parallel(
            Sequence(
                LerpColorScaleInterval(
                    title, 0.25, colorScale=(1, 1, 1, 1), startColorScale=(1, 1, 1, 0), blendType="easeInOut"
                ),
                Wait(9.75),
                LerpColorScaleInterval(
                    title, 1.25, colorScale=(1, 1, 1, 0), startColorScale=(1, 1, 1, 1), blendType="easeInOut"
                ),
                Func(lambda: title.cleanup()),
            ),
            Sequence(
                LerpColorScaleInterval(
                    sub, 0.25, colorScale=(1, 1, 1, 1), startColorScale=(1, 1, 1, 0), blendType="easeInOut"
                ),
                Wait(9.75),
                LerpColorScaleInterval(
                    sub, 1.25, colorScale=(1, 1, 1, 0), startColorScale=(1, 1, 1, 1), blendType="easeInOut"
                ),
                Func(lambda: sub.cleanup()),
            ),
        ).start()

    def revivedToon(self, avId):
        self.scoreboard.toonRevived(avId)
        if avId == base.localAvatar.doId:
            self.localToonIsSafe = False
            base.localAvatar.stunToon()

    def goonKilledBySafe(self, avId):
        self.scoreboard.addScore(
            avId, amount=self.ruleset.POINTS_GOON_KILLED_BY_SAFE, reason=CraneLeagueGlobals.GOON_KILLED_BY_SAFE_TEXT
        )

    def updateUnstun(self, avId):
        self.scoreboard.addScore(
            avId, amount=self.ruleset.POINTS_PENALTY_UNSTUN, reason=CraneLeagueGlobals.PENALTY_UNSTUN_TEXT
        )

    def timesUp(self):
        restartingOrEnding = "Restarting " if self.ruleset.RESTART_CRANE_ROUND_ON_FAIL else "Ending "

        for avId in self.getInvolvedToonsNotSpectating():
            av = base.cr.doId2do.get(avId)
            if av:
                if avId == base.localAvatar.doId:
                    messenger.send("exitCrane")
                av.stunToon(knockdown=1)

        title = OnscreenText(
            parent=aspect2d,
            text="Times up!",
            style=3,
            fg=(0.8, 0.2, 0.2, 1),
            align=TextNode.ACenter,
            scale=0.15,
            pos=(0, 0.35),
            font=getCompetitionFont(),
        )
        sub = OnscreenText(
            parent=aspect2d,
            text=restartingOrEnding + "crane round in 10 seconds...",
            style=3,
            fg=(0.8, 0.8, 0.8, 1),
            align=TextNode.ACenter,
            scale=0.09,
            pos=(0, 0.2),
            font=getCompetitionFont(),
        )

        Parallel(
            Sequence(
                LerpColorScaleInterval(
                    title, 0.25, colorScale=(1, 1, 1, 1), startColorScale=(1, 1, 1, 0), blendType="easeInOut"
                ),
                Wait(8.75),
                LerpColorScaleInterval(
                    title, 1.25, colorScale=(1, 1, 1, 0), startColorScale=(1, 1, 1, 1), blendType="easeInOut"
                ),
                Func(lambda: title.cleanup()),
            ),
            Sequence(
                LerpColorScaleInterval(
                    sub, 0.25, colorScale=(1, 1, 1, 1), startColorScale=(1, 1, 1, 0), blendType="easeInOut"
                ),
                Wait(8.75),
                LerpColorScaleInterval(
                    sub, 1.25, colorScale=(1, 1, 1, 0), startColorScale=(1, 1, 1, 1), blendType="easeInOut"
                ),
                Func(lambda: sub.cleanup()),
            ),
        ).start()
