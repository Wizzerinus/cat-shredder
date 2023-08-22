from direct.fsm import FSM

from toontown.coghq.cfo import DistributedCashbotBossCraneAI


class DistributedCashbotBossHeavyCraneAI(DistributedCashbotBossCraneAI.DistributedCashbotBossCraneAI, FSM.FSM):
    def __init__(self, air, boss, index):
        DistributedCashbotBossCraneAI.DistributedCashbotBossCraneAI.__init__(self, air, boss, index)
        FSM.FSM.__init__(self, "DistributedCashbotBossHeavyCraneAI")

    def getName(self):
        return "HeavyCrane-%s" % self.index

    def getDamageMultiplier(self):
        return self.boss.ruleset.HEAVY_CRANE_DAMAGE_MULTIPLIER
