from direct.distributed import DistributedNodeAI


class DistributedAvatarAI(DistributedNodeAI.DistributedNodeAI):
    _name = ""
    locationName = ""
    activity = None

    def __init__(self, air):
        DistributedNodeAI.DistributedNodeAI.__init__(self, air)
        self.hp = 0
        self.maxHp = 0

    def b_setName(self, name):
        self.setName(name)
        self.d_setName(name)

    def d_setName(self, name):
        self.sendUpdate("setName", [name])

    def setName(self, name):
        self._name = name

    def getName(self):
        return self._name

    def b_setMaxHp(self, maxHp):
        self.d_setMaxHp(maxHp)
        self.setMaxHp(maxHp)

    def d_setMaxHp(self, maxHp):
        self.sendUpdate("setMaxHp", [maxHp])

    def setMaxHp(self, maxHp):
        self.maxHp = maxHp

    def getMaxHp(self):
        return self.maxHp

    def b_setHp(self, hp):
        self.d_setHp(hp)
        self.setHp(hp)

    def d_setHp(self, hp):
        self.sendUpdate("setHp", [hp])

    def setHp(self, hp):
        self.hp = hp

    def getHp(self):
        return self.hp

    def toonUp(self, num):
        if self.hp >= self.maxHp:
            return
        self.hp = min(self.hp + num, self.maxHp)
        self.b_setHp(self.hp)

    def checkAvOnShard(self, avId):
        senderId = self.air.getAvatarIdFromSender()
        onShard = False
        if simbase.air.doId2do.get(avId):
            onShard = True
        self.sendUpdateToAvatarId(senderId, "confirmAvOnShard", [avId, onShard])
