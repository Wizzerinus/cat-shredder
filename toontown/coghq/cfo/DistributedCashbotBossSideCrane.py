from direct.distributed.ClockDelta import *
from direct.fsm import FSM
from panda3d.core import *

from toontown.coghq.cfo import DistributedCashbotBossCrane, DistributedCashbotBossGoon, DistributedCashbotBossSafe


class DistributedCashbotBossSideCrane(DistributedCashbotBossCrane.DistributedCashbotBossCrane, FSM.FSM):
    notify = directNotify.newCategory("DistributedCashbotBossCrane")
    firstMagnetBit = 21
    craneMinY = 8
    craneMaxY = 30
    armMinH = -12.5
    armMaxH = 12.5
    shadowOffset = 1
    emptyFrictionCoef = 0.1
    emptySlideSpeed = 15
    emptyRotateSpeed = 20
    lookAtPoint = Point3(0.3, 0, 0.1)
    lookAtUp = Vec3(0, -1, 0)
    neutralStickHinge = VBase3(0, 90, 0)

    def __init__(self, cr):
        DistributedCashbotBossCrane.DistributedCashbotBossCrane.__init__(self, cr)
        FSM.FSM.__init__(self, "DistributedCashbotBossSideCrane")

    def getName(self):
        return "SideCrane-%s" % self.index

    def grabObject(self, obj):
        if isinstance(obj, DistributedCashbotBossSafe.DistributedCashbotBossSafe):
            return
        DistributedCashbotBossCrane.DistributedCashbotBossCrane.grabObject(self, obj)

    def getPointsForStun(self):
        return self.boss.ruleset.POINTS_SIDESTUN

    # Override base method, always wake up goons
    def considerObjectState(self, obj):
        if isinstance(obj, DistributedCashbotBossGoon.DistributedCashbotBossGoon):
            obj.d_requestWalk()
            obj.setObjectState("W", 0, obj.craneId)  # wake goon up
