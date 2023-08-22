import random

from otp.avatar import DistributedAvatarAI
from toontown.toonbase.globals.TTGlobalsBosses import *
import contextlib

AllBossCogs = []


class DistributedBossCogAI(DistributedAvatarAI.DistributedAvatarAI):
    notify = directNotify.newCategory("DistributedBossCogAI")

    def __init__(self, air, dept):
        DistributedAvatarAI.DistributedAvatarAI.__init__(self, air)

        self.dept = dept

        self.looseToons = []
        self.involvedToons = []
        self.nearToons = []

        self.barrier = None

        self.bossDamage = 0
        self.battleThreeStart = 0
        self.battleThreeDuration = 1800

        self.attackCode = None
        self.attackAvId = 0

        self.hitCount = 0

        AllBossCogs.append(self)

    def delete(self):
        self.ignoreAll()
        if self in AllBossCogs:
            i = AllBossCogs.index(self)
            del AllBossCogs[i]

        return DistributedAvatarAI.DistributedAvatarAI.delete(self)

    def getDNAString(self):
        return self.dept

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        assert self.notify.debug("%s.avatarEnter(%s)" % (self.doId, avId))

        self.addToon(avId)

    def avatarExit(self):
        avId = self.air.getAvatarIdFromSender()
        assert self.notify.debug("%s.avatarExit(%s)" % (self.doId, avId))
        self.removeToon(avId)

    def avatarNearEnter(self):
        avId = self.air.getAvatarIdFromSender()
        assert self.notify.debug("%s.avatarNearEnter(%s)" % (self.doId, avId))

        if avId not in self.nearToons:
            self.nearToons.append(avId)

    def avatarNearExit(self):
        avId = self.air.getAvatarIdFromSender()
        assert self.notify.debug("%s.avatarNearExit(%s)" % (self.doId, avId))

        with contextlib.suppress(ValueError):
            self.nearToons.remove(avId)

    def __handleUnexpectedExit(self, avId):
        assert self.notify.debug("%s.handleUnexpectedExit(%s)" % (self.doId, avId))
        self.removeToon(avId)

    def addToon(self, avId):
        if avId not in self.looseToons and avId not in self.involvedToons:
            self.looseToons.append(avId)

            event = self.air.getAvatarExitEvent(avId)
            self.acceptOnce(event, self.__handleUnexpectedExit, extraArgs=[avId])

    def removeToon(self, avId, died=False):
        assert self.notify.debug("%s.removeToon(%s)" % (self.doId, avId))
        for arr in (self.looseToons, self.involvedToons, self.nearToons):
            with contextlib.suppress(ValueError):
                arr.remove(avId)

        if not died:
            with contextlib.suppress(ValueError):
                self.involvedToons.remove(avId)

        event = self.air.getAvatarExitEvent(avId)
        self.ignore(event)

        if not self.hasToons():
            taskMgr.doMethodLater(10, self.__bossDone, self.uniqueName("BossDone"))

    def __bossDone(self, task):
        self.b_setState("Off")
        messenger.send(self.uniqueName("BossDone"))
        self.ignoreAll()

    def hasToons(self):
        return self.looseToons or self.involvedToons

    def hasToonsAlive(self):
        alive = 0
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                hp = toon.getHp()
                if hp > 0:
                    alive = 1
        return alive

    def getToonIds(self):
        return self.involvedToons

    def damageToon(self, toon, deduction):
        toon.takeDamage(deduction)
        assert self.notify.debug(
            "%s. toon %s hit for %s to %s/%s" % (self.doId, toon.doId, deduction, toon.getHp(), toon.getMaxHp())
        )
        if toon.getHp() <= 0:
            assert self.notify.debug("%s. toon died: %s" % (self.doId, toon.doId))
            self.sendUpdate("toonDied", [toon.doId])

            self.removeToon(toon.doId)

    def healToon(self, toon, increment):
        toon.toonUp(increment)
        assert self.notify.debug("%s. toon %s healed to %s/%s" % (self.doId, toon.doId, toon.getHp(), toon.getMaxHp()))

    def b_setArenaSide(self, arenaSide):
        self.setArenaSide(arenaSide)
        self.d_setArenaSide(arenaSide)

    def setArenaSide(self, arenaSide):
        self.arenaSide = arenaSide

    def d_setArenaSide(self, arenaSide):
        self.sendUpdate("setArenaSide", [arenaSide])

    def b_setState(self, state):
        self.setState(state)
        self.d_setState(state)

    def d_setState(self, state):
        self.sendUpdate("setState", [state])

    def setState(self, state):
        self.demand(state)

    def getState(self):
        return self.state

    def enterOff(self):
        assert self.notify.debug("enterOff()")

    def exitOff(self):
        pass

    def enterWaitForToons(self):
        assert self.notify.debug("%s.enterWaitForToons()" % (self.doId))

        self.barrier = self.beginBarrier("WaitForToons", self.involvedToons, 5, self.__doneWaitForToons)

    def __doneWaitForToons(self, toons):
        assert self.notify.debug("%s.__doneWaitForToons()" % (self.doId))
        self.b_setState("BattleThree")

    def exitWaitForToons(self):
        self.ignoreBarrier(self.barrier)

    def acceptNewToons(self):
        sourceToons = self.looseToons
        self.looseToons = []
        for toonId in sourceToons:
            toon = self.air.doId2do.get(toonId)
            if toon and not toon.ghostMode:
                self.involvedToons.append(toonId)
            else:
                self.looseToons.append(toonId)

    def moveSuits(self, active):
        for suit in active:
            self.reserveSuits.append((suit, 0))

    def getBattleThreeTime(self):
        elapsed = globalClock.getFrameTime() - self.battleThreeStart
        return elapsed / float(self.battleThreeDuration)

    def progressValue(self, fromValue, toValue):
        t0 = float(self.bossDamage) / float(self.bossMaxDamage)

        elapsed = globalClock.getFrameTime() - self.battleThreeStart
        t1 = elapsed / float(self.battleThreeDuration)

        t = max(t0, t1)

        return fromValue + (toValue - fromValue) * min(t, 1)

    def progressRandomValue(self, fromValue, toValue, radius=0.2, noRandom=False):
        if noRandom:
            return self.progressValue(fromValue, toValue)
        t = self.progressValue(0, 1)

        radius = radius * (1.0 - abs(t - 0.5) * 2.0)

        t += radius * random.uniform(-1, 1)
        t = max(min(t, 1.0), 0.0)

        return fromValue + (toValue - fromValue) * t

    def reportToonHealth(self):
        if self.notify.getDebug():
            output = ""
            for toonId in self.involvedToons:
                toon = self.air.doId2do.get(toonId)
                if toon:
                    output += ", %s (%s/%s)" % (toonId, toon.getHp(), toon.getMaxHp())
            self.notify.debug("%s.toons = %s" % (self.doId, output[2:]))

    def getDamageMultiplier(self):
        """Return a multiplier for our damaging attacks."""
        return 1.0

    def zapToon(self, x, y, z, h, p, r, bpx, bpy, attackCode, timestamp):
        avId = self.air.getAvatarIdFromSender()

        if not self.validate(avId, avId in self.involvedToons, "zapToon from unknown avatar"):
            return

        if attackCode == BossCogLawyerAttack and self.dept != "l":
            self.notify.warning("got lawyer attack but not in CJ boss battle")
            return

        toon = simbase.air.doId2do.get(avId)
        if toon:
            self.d_showZapToon(avId, x, y, z, h, p, r, attackCode, timestamp)

            damage = BossCogDamageLevels.get(attackCode)
            if damage is None:
                self.notify.warning("No damage listed for attack code %s" % (attackCode))
                damage = 5

            damage *= self.getDamageMultiplier()
            self.damageToon(toon, damage)

            currState = self.getCurrentOrNextState()
            if attackCode == BossCogElectricFence and currState == "BattleThree" and bpy < 0 and abs(bpx / bpy) > 0.5:
                if bpx < 0:
                    self.b_setAttackCode(BossCogSwatRight)
                else:
                    self.b_setAttackCode(BossCogSwatLeft)

    def d_showZapToon(self, avId, x, y, z, h, p, r, attackCode, timestamp):
        self.sendUpdate("showZapToon", [avId, x, y, z, h, p, r, attackCode, timestamp])

    def b_setAttackCode(self, attackCode, avId=0):
        self.d_setAttackCode(attackCode, avId)
        self.setAttackCode(attackCode, avId)

    def setAttackCode(self, attackCode, avId=0):
        assert self.notify.debug("%s.setAttackCode(%s, %s)" % (self.doId, attackCode, avId))
        self.attackCode = attackCode
        self.attackAvId = avId

        if attackCode in (BossCogDizzy, BossCogDizzyNow):
            delayTime = self.progressValue(20, 5)

            self.hitCount = 0

        elif attackCode == BossCogSlowDirectedAttack:
            delayTime = BossCogAttackTimes.get(attackCode)

            delayTime += self.progressValue(10, 0)

        else:
            delayTime = BossCogAttackTimes.get(attackCode)
            if delayTime is None:
                return

        self.waitForNextAttack(delayTime)

    def d_setAttackCode(self, attackCode, avId=0):
        self.sendUpdate("setAttackCode", [attackCode, avId])

    def waitForNextAttack(self, delayTime):
        currState = self.getCurrentOrNextState()
        if currState == "BattleThree":
            assert self.notify.debug("%s.Waiting %s seconds for next attack." % (self.doId, delayTime))
            taskName = self.uniqueName("NextAttack")
            taskMgr.remove(taskName)
            taskMgr.doMethodLater(delayTime, self.doNextAttack, taskName)
        else:
            assert self.notify.debug("%s.Not doing another attack in state %s." % (self.doId, currState))

    def stopAttacks(self):
        taskName = self.uniqueName("NextAttack")
        taskMgr.remove(taskName)

    def doNextAttack(self, task):
        self.b_setAttackCode(BossCogNoAttack)
