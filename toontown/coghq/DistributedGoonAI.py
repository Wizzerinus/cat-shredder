import random

from direct.distributed import ClockDelta
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from toontown.toonbase.globals.TTGlobalsMovement import *


class DistributedGoonAI(DistributedObjectAI):
    """
    A simple, dumb robot.
    The robot should be flexible and reusable, for uses in CogHQ basements
    and factories, and perhaps other parts of the game.  Let the goon's
    movement, discovery, and attack methods be modular, so different behavior
    types can be easily plugged in.
    """

    UPDATE_TIMESTAMP_INTERVAL = 180.0

    STUN_TIME = 4

    notify = directNotify.newCategory("DistributedGoonAI")

    def __init__(self, air):
        self.hFov = 70
        self.attackRadius = 15
        self.strength = 15
        self.velocity = 4
        self.scale = 1.0

        DistributedObjectAI.__init__(self, air)
        self.curInd = 0
        self.dir = GOON_FORWARD
        self.width = 1
        self.crushed = 0

        self.pathStartTime = None
        self.walkTrackTime = 0.0
        self.totalPathTime = 1.0

    def delete(self):
        taskMgr.remove(self.taskName("sync"))
        taskMgr.remove(self.taskName("resumeWalk"))
        taskMgr.remove(self.taskName("recovery"))
        taskMgr.remove(self.taskName("deleteGoon"))

    def startGoon(self):
        ts = 100 * random.random()
        self.sendMovie(GOON_MOVIE_WALK, pauseTime=ts)

    def requestBattle(self, pauseTime):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug(f"requestBattle, avId = {avId}")

        self.sendMovie(GOON_MOVIE_BATTLE, avId, pauseTime)

        taskMgr.remove(self.taskName("resumeWalk"))
        taskMgr.doMethodLater(
            5, self.sendMovie, self.taskName("resumeWalk"), extraArgs=(GOON_MOVIE_WALK, avId, pauseTime)
        )

    def requestStunned(self, pauseTime):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug(f"requestStunned({avId})")

        self.sendMovie(GOON_MOVIE_STUNNED, avId, pauseTime)

        taskMgr.remove(self.taskName("recovery"))
        taskMgr.doMethodLater(
            self.STUN_TIME, self.sendMovie, self.taskName("recovery"), extraArgs=(GOON_MOVIE_RECOVERY, avId, pauseTime)
        )

    def requestResync(self, task=None):
        """
        resync(self)

        Broadcasts a walk message to all clients who care.
        This is mainly useful while developing, in case you
        have paused the AI or your client and you are now out of sync.
        We should resync every 5 minutes, so the timestamp doesn't go
        stale.

        The magic word "~resyncGoons" calls this function on every goon
        in the current zone
        """
        self.notify.debug("resyncGoon")
        self.sendMovie(GOON_MOVIE_SYNC)

        return

    def sendMovie(self, type, avId=0, pauseTime=0.0):
        if type == GOON_MOVIE_WALK:
            self.pathStartTime = globalClock.getFrameTime()
            self.walkTrackTime = pauseTime

            self.notify.debug(
                f"GOON_MOVIE_WALK doId = {self.doId}, pathStartTime = {self.pathStartTime}, "
                f"walkTrackTime = {self.walkTrackTime}"
            )

        if type == GOON_MOVIE_WALK or type == GOON_MOVIE_SYNC:
            curT = globalClock.getFrameTime()
            elapsedT = curT - self.pathStartTime

            pathT = self.walkTrackTime + elapsedT

            self.sendUpdate("setMovie", [type, avId, pathT, ClockDelta.globalClockDelta.localToNetworkTime(curT)])

            taskMgr.remove(self.taskName("sync"))
            taskMgr.doMethodLater(
                self.UPDATE_TIMESTAMP_INTERVAL, self.requestResync, self.taskName("sync"), extraArgs=None
            )
        else:
            self.sendUpdate("setMovie", [type, avId, pauseTime, ClockDelta.globalClockDelta.getFrameNetworkTime()])

    def setVelocity(self, velocity):
        self.velocity = velocity

    def setHFov(self, hFov):
        self.hFov = hFov

    def setAttackRadius(self, attackRadius):
        self.attackRadius = attackRadius

    def setStrength(self, strength):
        self.strength = strength

    def setGoonScale(self, scale):
        self.scale = scale

    def b_setupGoon(self, velocity, hFov, attackRadius, strength, scale, stunTime=None):
        if stunTime is not None:
            self.STUN_TIME = stunTime

        self.setupGoon(velocity, hFov, attackRadius, strength, scale)
        self.d_setupGoon(velocity, hFov, attackRadius, strength, scale)

    def setupGoon(self, velocity, hFov, attackRadius, strength, scale):
        self.setVelocity(velocity)
        self.setHFov(hFov)
        self.setAttackRadius(attackRadius)
        self.setStrength(strength)
        self.setGoonScale(scale)

    def d_setupGoon(self, velocity, hFov, attackRadius, strength, scale):
        self.sendUpdate("setupGoon", [velocity, hFov, attackRadius, strength, scale])
