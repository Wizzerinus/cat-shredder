from toontown.world.coghq import CogHQBossBattle


class CashbotHQBossBattle(CogHQBossBattle.CogHQBossBattle):
    notify = directNotify.newCategory("CashbotHQBossBattle")

    def __init__(self, loader, parentFSM, doneEvent):
        CogHQBossBattle.CogHQBossBattle.__init__(self, loader, parentFSM, doneEvent)
        self.teleportInPosHpr = (88, -214, 0, 210, 0, 0)

    def load(self):
        CogHQBossBattle.CogHQBossBattle.load(self)

    def unload(self):
        CogHQBossBattle.CogHQBossBattle.unload(self)

    def enter(self, requestStatus):
        from toontown.coghq.cfo import DistributedCashbotBoss

        CogHQBossBattle.CogHQBossBattle.enter(self, requestStatus, DistributedCashbotBoss.OneBossCog)

    def exit(self):
        CogHQBossBattle.CogHQBossBattle.exit(self)

    def exitCrane(self):
        CogHQBossBattle.CogHQBossBattle.exitCrane(self)
        messenger.send("exitCrane")
