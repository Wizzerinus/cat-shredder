from toontown.boarding import DistributedBoardingPartyAI
from toontown.coghq.DistributedLobbyManagerAI import DistributedLobbyManagerAI
from toontown.elevators import DistributedCFOElevatorAI
from toontown.elevators import DoorTypes
from toontown.toonbase.globals.TTGlobalsWorld import ZoneIDs
from toontown.world import HoodDataAI
from toontown.world.coghq import DistributedCogHQDoorAI


class CashbotHQDataAI(HoodDataAI.HoodDataAI):
    notify = directNotify.newCategory("CashbotHqDataAI")
    hoodId = ZoneIDs.CashbotHQ

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)

        self.lobbyMgr = DistributedLobbyManagerAI(self.air, None)
        self.lobbyMgr.generateWithRequired(ZoneIDs.CashbotHQLobby)
        self.addDistObj(self.lobbyMgr)

        self.lobbyElevator = DistributedCFOElevatorAI.DistributedCFOElevatorAI(
            self.air, self.lobbyMgr, ZoneIDs.CashbotHQLobby
        )
        self.lobbyElevator.generateWithRequired(ZoneIDs.CashbotHQLobby)
        self.addDistObj(self.lobbyElevator)

        self.boardingParty = DistributedBoardingPartyAI.DistributedBoardingPartyAI(
            self.air, [self.lobbyElevator.doId], 8
        )
        self.boardingParty.generateWithRequired(ZoneIDs.CashbotHQLobby)

        extDoor0 = DistributedCogHQDoorAI.DistributedCogHQDoorAI(
            self.air, 0, DoorTypes.EXT_COGHQ, ZoneIDs.CashbotHQLobby, doorIndex=0
        )
        extDoorList = [extDoor0]

        intDoor0 = DistributedCogHQDoorAI.DistributedCogHQDoorAI(
            self.air, 0, DoorTypes.INT_COGHQ, ZoneIDs.CashbotHQ, doorIndex=0
        )
        intDoor0.setOtherDoor(extDoor0)
        intDoor0.zoneId = ZoneIDs.CashbotHQLobby

        for extDoor in extDoorList:
            extDoor.setOtherDoor(intDoor0)
            extDoor.zoneId = ZoneIDs.CashbotHQ
            extDoor.generateWithRequired(ZoneIDs.CashbotHQ)
            extDoor.sendUpdate("setDoorIndex", [extDoor.getDoorIndex()])
            self.addDistObj(extDoor)

        intDoor0.generateWithRequired(ZoneIDs.CashbotHQLobby)
        intDoor0.sendUpdate("setDoorIndex", [intDoor0.getDoorIndex()])
        self.addDistObj(intDoor0)
