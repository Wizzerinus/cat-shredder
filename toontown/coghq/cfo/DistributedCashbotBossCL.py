from direct.directnotify import DirectNotifyGlobal

from toontown.coghq.cfo import DistributedCashbotBoss


class DistributedCashbotBossCL(DistributedCashbotBoss.DistributedCashbotBoss):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedCashbotBossCLAI")

    def __init__(self, air):
        DistributedCashbotBoss.DistributedCashbotBoss.__init__(self, air)
