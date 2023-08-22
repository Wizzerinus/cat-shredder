from toontown.world import DistributedDoorAI


class DistributedCogHQDoorAI(DistributedDoorAI.DistributedDoorAI):
    notify = directNotify.newCategory("DistributedCogHQDoorAI")

    def __init__(
        self,
        air,
        blockNumber,
        doorType,
        destinationZone,
        doorIndex=0,
        swing=3,
    ):
        assert self.notify.debug("__init__: dest:%s, doorIndex:%d)" % (destinationZone, doorIndex))
        DistributedDoorAI.DistributedDoorAI.__init__(self, air, blockNumber, doorType, doorIndex, swing)
        self.destinationZone = destinationZone

    def getDestinationZone(self):
        return self.destinationZone
