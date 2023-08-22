from . import DistributedBossElevatorAI
from .ElevatorConstants import *


class DistributedCFOElevatorAI(DistributedBossElevatorAI.DistributedBossElevatorAI):
    def __init__(self, air, bldg, zone):
        """__init__(air)"""
        DistributedBossElevatorAI.DistributedBossElevatorAI.__init__(self, air, bldg, zone)
        self.type = ELEVATOR_CFO
        self.countdownTime = ElevatorData[self.type]["countdown"]
