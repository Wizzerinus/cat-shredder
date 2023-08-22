from direct.distributed.DistributedNodeAI import DistributedNodeAI


class DistributedAvatarUD(DistributedNodeAI):
    def __init__(self, air):
        DistributedNodeAI.__init__(self, air)
        self.hp = 0
        self.maxHp = 0

    def b_setName(self, name):
        self.setName(name)
        self.d_setName(name)

    def d_setName(self, name):
        self.sendUpdate("setName", [name])

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name
