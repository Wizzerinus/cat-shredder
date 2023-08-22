from direct.fsm import FSM

from toontown.coghq.cfo import DistributedCashbotBossCraneAI


class DistributedCashbotBossSideCraneAI(DistributedCashbotBossCraneAI.DistributedCashbotBossCraneAI, FSM.FSM):
    def __init__(self, air, boss, index):
        DistributedCashbotBossCraneAI.DistributedCashbotBossCraneAI.__init__(self, air, boss, index)
        FSM.FSM.__init__(self, "DistributedCashbotBossSideCraneAI")

    def getName(self):
        return "SideCrane-%s" % self.index

    def getPointsForStun(self):
        return self.boss.ruleset.POINTS_SIDESTUN
