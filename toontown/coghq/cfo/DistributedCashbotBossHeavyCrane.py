from direct.distributed.ClockDelta import *
from direct.fsm import FSM
from panda3d.core import *

from toontown.coghq.cfo import DistributedCashbotBossCrane


class DistributedCashbotBossHeavyCrane(DistributedCashbotBossCrane.DistributedCashbotBossCrane, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedCashbotBossHeavyCrane")
    craneMinY = 8
    craneMaxY = 28
    armMinH = -25
    armMaxH = 25
    emptyFrictionCoef = 0.1
    emptySlideSpeed = 5
    emptyRotateSpeed = 15
    lookAtPoint = Point3(0.3, 0, 0.1)
    lookAtUp = Vec3(0, -1, 0)
    neutralStickHinge = VBase3(0, 90, 0)

    def __init__(self, cr):
        DistributedCashbotBossCrane.DistributedCashbotBossCrane.__init__(self, cr)
        FSM.FSM.__init__(self, "DistributedCashbotBossHeavyCrane")

    def getName(self):
        return "HeavyCrane-%s" % self.index
