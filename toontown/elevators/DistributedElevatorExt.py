from panda3d.otp import Nametag, NametagGroup

from toontown.toonbase import TTLocalizer
from . import DistributedElevator
from .ElevatorUtils import *
from toontown.toonbase.globals.TTGlobalsGUI import getBuildingNametagFont


class DistributedElevatorExt(DistributedElevator.DistributedElevator):
    def __init__(self, cr):
        DistributedElevator.DistributedElevator.__init__(self, cr)
        self.nametag = None
        self.currentFloor = -1

    def setupElevator(self):
        """
        Called when the building doId is set at construction time,
        this method sets up the elevator for business.
        """
        if self.isSetup:
            self.elevatorSphereNodePath.removeNode()

        self.leftDoor = self.bldg.leftDoor
        self.rightDoor = self.bldg.rightDoor
        DistributedElevator.DistributedElevator.setupElevator(self)
        self.setupNametag()

    def disable(self):
        self.clearNametag()
        DistributedElevator.DistributedElevator.disable(self)

    def setupNametag(self):
        if self.nametag is None:
            self.nametag = NametagGroup()
            self.nametag.setFont(getBuildingNametagFont())
            self.nametag.setContents(Nametag.CName)
            self.nametag.setColorCode(NametagGroup.CCSuitBuilding)
            self.nametag.setActive(0)
            self.nametag.setAvatar(self.getElevatorModel())

            name = self.cr.playGame.dnaStore.getTitleFromBlockNumber(self.bldg.block)
            if not name:
                name = TTLocalizer.CogsInc
            else:
                name += TTLocalizer.CogsIncExt

            self.nametag.setName(name)
            self.nametag.manage(base.marginManager)

    def clearNametag(self):
        if self.nametag is not None:
            self.nametag.unmanage(base.marginManager)
            self.nametag.setAvatar(NodePath())
            self.nametag = None

    def getBldgDoorOrigin(self):
        return self.bldg.getSuitDoorOrigin()

    def gotBldg(self, buildingList):
        self.bldgRequest = None
        self.bldg = buildingList[0]
        if not self.bldg:
            self.notify.error("setBldgDoId: elevator %d cannot find bldg %d!" % (self.doId, self.bldgDoId))
            return
        if self.getBldgDoorOrigin():
            self.bossLevel = self.bldg.getBossLevel()
            self.setupElevator()
        else:
            self.notify.warning(
                "setBldgDoId: elevator %d cannot find suitDoorOrigin for bldg %d!" % (self.doId, self.bldgDoId)
            )
        return

    def setFloor(self, floorNumber):
        if self.currentFloor >= 0 and self.bldg.floorIndicator[floorNumber]:
            self.bldg.floorIndicator[self.currentFloor].setColor(LIGHT_OFF_COLOR)

        if floorNumber >= 0 and self.bldg.floorIndicator[floorNumber]:
            self.bldg.floorIndicator[floorNumber].setColor(LIGHT_ON_COLOR)

        self.currentFloor = floorNumber

    def handleEnterSphere(self, collEntry):
        self.notify.debug("Entering Elevator Sphere....")

        if (
            hasattr(base.localAvatar, "boardingParty")
            and base.localAvatar.boardingParty
            and base.localAvatar.boardingParty.getGroupLeader(base.localAvatar.doId)
            and base.localAvatar.boardingParty.getGroupLeader(base.localAvatar.doId) != base.localAvatar.doId
        ):
            base.localAvatar.elevatorNotifier.showMeWithoutStopping(TTLocalizer.ElevatorGroupMember)
        else:
            self.cr.playGame.getPlace().detectedElevatorCollision(self)

    def handleEnterElevator(self):
        if (
            hasattr(base.localAvatar, "boardingParty")
            and base.localAvatar.boardingParty
            and base.localAvatar.boardingParty.getGroupLeader(base.localAvatar.doId)
        ):
            if base.localAvatar.boardingParty.getGroupLeader(base.localAvatar.doId) == base.localAvatar.doId:
                base.localAvatar.boardingParty.handleEnterElevator(self)

        elif base.localAvatar.hp > 0:
            self.sendUpdate("requestBoard", [])
        else:
            self.notify.warning("Tried to board elevator with hp: %d" % base.localAvatar.hp)

    def enterWaitEmpty(self, ts):
        self.elevatorSphereNodePath.unstash()
        self.forceDoorsOpen()
        self.accept(self.uniqueName("enterelevatorSphere"), self.handleEnterSphere)
        self.accept(self.uniqueName("enterElevatorOK"), self.handleEnterElevator)
        DistributedElevator.DistributedElevator.enterWaitEmpty(self, ts)

    def exitWaitEmpty(self):
        self.elevatorSphereNodePath.stash()
        self.ignore(self.uniqueName("enterelevatorSphere"))
        self.ignore(self.uniqueName("enterElevatorOK"))
        DistributedElevator.DistributedElevator.exitWaitEmpty(self)

    def enterWaitCountdown(self, ts):
        DistributedElevator.DistributedElevator.enterWaitCountdown(self, ts)
        self.forceDoorsOpen()
        self.accept(self.uniqueName("enterElevatorOK"), self.handleEnterElevator)
        self.startCountdownClock(self.countdownTime, ts)

    def exitWaitCountdown(self):
        self.ignore(self.uniqueName("enterElevatorOK"))
        DistributedElevator.DistributedElevator.exitWaitCountdown(self)

    def getZoneId(self):
        return self.bldg.interiorZoneId

    def getElevatorModel(self):
        return self.bldg.getSuitElevatorNodePath()
