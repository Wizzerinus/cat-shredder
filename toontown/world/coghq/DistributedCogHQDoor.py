from direct.interval.IntervalGlobal import *
from panda3d.core import VBase3

from toontown.toonbase import TTLocalizer
from toontown.world import DistributedDoor, ZoneUtil


class DistributedCogHQDoor(DistributedDoor.DistributedDoor):
    def __init__(self, cr):
        """constructor for the DistributedDoor"""
        DistributedDoor.DistributedDoor.__init__(self, cr)
        self.openSfx = base.loader.loadSfx("phase_9/audio/sfx/CHQ_door_open.ogg")
        self.closeSfx = base.loader.loadSfx("phase_9/audio/sfx/CHQ_door_close.ogg")

    def wantsNametag(self):
        """return true if this door needs an arrow pointing to it."""
        return 0

    def getRequestStatus(self):
        zoneId = self.otherZoneId
        return {
            "loader": ZoneUtil.getBranchLoaderName(zoneId),
            "where": ZoneUtil.getToonWhereName(zoneId),
            "how": "doorIn",
            "hoodId": ZoneUtil.getHoodId(zoneId),
            "zoneId": zoneId,
            "shardId": None,
            "avId": -1,
            "allowRedirect": 0,
            "doorDoId": self.otherDoId,
        }

    def enterClosing(self, ts):
        doorFrameHoleRight = self.findDoorNode("doorFrameHoleRight")
        if doorFrameHoleRight.isEmpty():
            self.notify.warning("enterClosing(): did not find doorFrameHoleRight")
            return

        rightDoor = self.findDoorNode("rightDoor")
        if rightDoor.isEmpty():
            self.notify.warning("enterClosing(): did not find rightDoor")
            return

        otherNP = self.getDoorNodePath()
        trackName = "doorClose-%d" % (self.doId)
        h = 100 if self.rightSwing else -100
        self.finishDoorTrack()
        self.doorTrack = Parallel(
            Sequence(
                LerpHprInterval(
                    nodePath=rightDoor,
                    duration=1.0,
                    hpr=VBase3(0, 0, 0),
                    startHpr=VBase3(h, 0, 0),
                    other=otherNP,
                    blendType="easeInOut",
                ),
                Func(doorFrameHoleRight.hide),
                Func(self.hideIfHasFlat, rightDoor),
            ),
            Sequence(
                Wait(0.5),
                SoundInterval(self.closeSfx, node=rightDoor),
            ),
            name=trackName,
        )
        self.doorTrack.start(ts)
        if hasattr(self, "done"):
            request = self.getRequestStatus()
            messenger.send("doorDoneEvent", [request])

    def exitDoorEnterClosing(self, ts):
        doorFrameHoleLeft = self.findDoorNode("doorFrameHoleLeft")
        if doorFrameHoleLeft.isEmpty():
            self.notify.warning("enterOpening(): did not find flatDoors")
            return

        if ZoneUtil.isInterior(self.zoneId):
            doorFrameHoleLeft.setColor(1.0, 1.0, 1.0, 1.0)
        h = -100 if self.leftSwing else 100
        leftDoor = self.findDoorNode("leftDoor")
        if not leftDoor.isEmpty():
            otherNP = self.getDoorNodePath()
            trackName = "doorExitTrack-%d" % (self.doId)
            self.doorExitTrack = Parallel(
                Sequence(
                    LerpHprInterval(
                        nodePath=leftDoor,
                        duration=1.0,
                        hpr=VBase3(0, 0, 0),
                        startHpr=VBase3(h, 0, 0),
                        other=otherNP,
                        blendType="easeInOut",
                    ),
                    Func(doorFrameHoleLeft.hide),
                    Func(self.hideIfHasFlat, leftDoor),
                ),
                Sequence(
                    Wait(0.5),
                    SoundInterval(self.closeSfx, node=leftDoor),
                ),
                name=trackName,
            )
            self.doorExitTrack.start(ts)

    def setZoneIdAndBlock(self, zoneId, block):
        assert self.notify.debug(
            "setZoneIdAndBlock(zoneId=" + str(zoneId) + ", block=" + str(block) + ") for doId=" + str(self.doId)
        )
        self.zoneId = zoneId
        self.block = block

    def enterDoor(self):
        messenger.send("DistributedDoor_doorTrigger")
        self.sendUpdate("requestEnter")

    def doorTrigger(self, args=None):
        if base.localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            base.localAvatar.boardingParty.showMe(rejectText)
            return
        DistributedDoor.DistributedDoor.doorTrigger(self, args)
