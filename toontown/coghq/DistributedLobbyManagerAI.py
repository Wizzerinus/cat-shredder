from direct.distributed import DistributedObjectAI


class DistributedLobbyManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = directNotify.newCategory("LobbyManagerAI")

    def __init__(self, air, bossConstructor):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.air = air
        self.bossConstructor = bossConstructor

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.notify.debug("generate")

    def delete(self):
        self.notify.debug("delete")
        self.ignoreAll()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def requestSoloBoss(self):
        toonId = self.air.getAvatarIdFromSender()
        zoneId = self.createBossOffice([toonId])
        self.sendUpdateToAvatarId(toonId, "setBossZoneId", [zoneId])

    def createBossOffice(self, avIdList):
        bossZone = self.air.allocateZone()
        self.notify.info("createBossOffice: %s" % bossZone)
        bossCog = self.bossConstructor(self.air)
        for avId in avIdList:
            if avId:
                bossCog.addToon(avId)

        bossCog.acceptNewToons()
        bossCog.generateWithRequired(bossZone)
        self.acceptOnce(bossCog.uniqueName("BossDone"), self.destroyBossOffice, extraArgs=[bossCog])
        bossCog.b_setState("WaitForToons")
        return bossZone

    def destroyBossOffice(self, bossCog):
        bossZone = bossCog.zoneId
        self.notify.info("destroyBossOffice: %s" % bossZone)
        bossCog.requestDelete()
        self.air.deallocateZone(bossZone)
