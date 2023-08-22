from direct.interval.IntervalGlobal import *
from direct.task.Task import Task
from pandac.PandaModules import *

from toontown.effects import DustCloud
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals.TTGlobalsGUI import getSignFont
from toontown.toonbase.globals.TTGlobalsRender import WallBitmask

TRACK_TYPE_TELEPORT = 1
TRACK_TYPE_RUN = 2
TRACK_TYPE_POOF = 3


class BoardingGroupShow:
    notify = directNotify.newCategory("BoardingGroupShow")

    thresholdRunDistance = 25.0

    def __init__(self, toon):
        self.toon = toon
        self.avId = self.toon.doId
        self.dustCloudIval = None
        if __debug__:
            base.bgs = self

    def cleanup(self):
        if base.localAvatar.doId == self.avId:
            self.__stopTimer()
            self.clock.removeNode()

    def startTimer(self):
        self.clockNode = TextNode("elevatorClock")
        self.clockNode.setFont(getSignFont())
        self.clockNode.setAlign(TextNode.ACenter)
        self.clockNode.setTextColor(0.5, 0.5, 0.5, 1)
        self.clockNode.setText(str(int(self.countdownDuration)))
        self.clock = aspect2d.attachNewNode(self.clockNode)

        self.clock.setPos(0, 0, -0.6)
        self.clock.setScale(0.15, 0.15, 0.15)

        self.__countdown(self.countdownDuration, self.__boardingElevatorTimerExpired)

    def __countdown(self, duration, callback):
        """
        Spawn the timer task for duration seconds.
        Calls callback when the timer is up
        """
        self.countdownTask = Task(self.__timerTask)
        self.countdownTask.duration = duration
        self.countdownTask.callback = callback

        taskMgr.remove(self.uniqueName(self.avId))
        return taskMgr.add(self.countdownTask, self.uniqueName(self.avId))

    def __timerTask(self, task):
        """
        This is the task for the countdown.
        """
        countdownTime = int(task.duration - task.time)
        timeStr = self.timeWarningText + str(countdownTime)

        if self.clockNode.getText() != timeStr:
            self.clockNode.setText(timeStr)

        if task.time >= task.duration:
            if task.callback:
                task.callback()
            return Task.done

        return Task.cont

    def __boardingElevatorTimerExpired(self):
        """
        This is where the control goes as soon as the countdown finishes.
        """
        self.notify.debug("__boardingElevatorTimerExpired")
        self.clock.removeNode()

    def __stopTimer(self):
        """
        Get rid of any countdowns
        """
        if self.countdownTask:
            self.countdownTask.callback = None
            taskMgr.remove(self.countdownTask)

    def uniqueName(self, avId):
        """
        Here we're making our own uniqueName method, each avId's sequence should be unique.
        """
        return "boardingElevatorTimerTask-" + str(avId)

    def getBoardingTrack(self, elevatorModel, offset, offsetWrtRender, wantToonRotation):
        """
        Return an interval of the toon teleporting/running to the front of the elevator.
        This method is called from the elevator.
        Note: The offset is to where the toon will teleport/run to. This offset has to be
        calculated wrt the parent of the toon.
        Eg: For the CogKart the offset should be computed wrt to the cogKart because the
            toon is parented to the cogKart.
            For the other elevators the offset should be computer wrt to render because the
            toon is parented to render.
        """
        self.timeWarningText = TTLocalizer.BoardingTimeWarning
        self.countdownDuration = 6
        trackType = TRACK_TYPE_TELEPORT
        boardingTrack = Sequence()
        if self.toon:
            if self.avId == base.localAvatar.doId:
                boardingTrack.append(Func(self.startTimer))

            isInThresholdDist = self.__isInThresholdDist(elevatorModel, offset, self.thresholdRunDistance)
            isRunPathClear = self.__isRunPathClear(elevatorModel, offsetWrtRender)

            if isInThresholdDist and isRunPathClear:
                boardingTrack.append(self.__getRunTrack(elevatorModel, offset, wantToonRotation))
                trackType = TRACK_TYPE_RUN
            else:
                boardingTrack.append(self.__getTeleportTrack(elevatorModel, offset, wantToonRotation))

        boardingTrack.append(Func(self.cleanup))

        return (boardingTrack, trackType)

    def __getOffsetPos(self, elevatorModel, offset):
        """
        Get the offset position to where the toon might have to
        teleport to or run to.
        Note: This is the pos reletive to the elevator.
        """
        dest = elevatorModel.getPos(self.toon.getParent())
        dest += Vec3(*offset)
        return dest

    def __getTeleportTrack(self, elevatorModel, offset, wantToonRotation):
        """
        We get the teleport track when the toon is outside the
        threshold distance away from the elevator.
        The Teleport Track is an interval of the toon teleporting to the
        elevator seat's offset position. After it reaches the offset position
        the boarding the elevator animation takes over.
        """
        teleportTrack = Sequence()
        if self.toon:
            if wantToonRotation:
                teleportTrack.append(Func(self.toon.headsUp, elevatorModel, offset))
            teleportTrack.append(Func(self.toon.setAnimState, "TeleportOut"))
            teleportTrack.append(Wait(3.5))
            teleportTrack.append(Func(self.toon.setPos, Point3(offset)))
            teleportTrack.append(Func(self.toon.setAnimState, "TeleportIn"))
            teleportTrack.append(Wait(1))
        return teleportTrack

    def __getPoofTeleportTrack(self, elevatorModel, offset, wantToonRotation):
        """
        We get the poof teleport track when the toon is outside the
        threshold distance away from the elevator.
        The Poof Teleport Track is an interval of the toon poofing out
        and poofing into the elevator seat's offset position.
        After it reaches the offset position
        the boarding the elevator animation takes over.
        """
        teleportTrack = Sequence()

        if wantToonRotation:
            teleportTrack.append(Func(self.toon.headsUp, elevatorModel, offset))

        def getDustCloudPos():
            toonPos = self.toon.getPos(render)
            return Point3(toonPos.getX(), toonPos.getY(), toonPos.getZ() + 3)

        def cleanupDustCloudIval():
            if self.dustCloudIval:
                self.dustCloudIval.finish()
                self.dustCloudIval = None

        def getDustCloudIval():
            cleanupDustCloudIval()

            dustCloud = DustCloud.DustCloud(fBillboard=0, wantSound=1)
            dustCloud.setBillboardAxis(2.0)
            dustCloud.setZ(3)
            dustCloud.setScale(0.4)
            dustCloud.createTrack()

            self.dustCloudIval = Sequence(
                Func(dustCloud.reparentTo, render),
                Func(dustCloud.setPos, getDustCloudPos()),
                dustCloud.track,
                Func(dustCloud.detachNode),
                Func(dustCloud.destroy),
                name="dustCloadIval",
            )
            self.dustCloudIval.start()

        if self.toon:
            teleportTrack.append(Func(self.toon.setAnimState, "neutral"))
            teleportTrack.append(Wait(0.5))
            teleportTrack.append(Func(getDustCloudIval))
            teleportTrack.append(Wait(0.25))
            teleportTrack.append(Func(self.toon.hide))
            teleportTrack.append(Wait(1.5))
            teleportTrack.append(Func(self.toon.setPos, Point3(offset)))
            teleportTrack.append(Func(getDustCloudIval))
            teleportTrack.append(Wait(0.25))
            teleportTrack.append(Func(self.toon.show))
            teleportTrack.append(Wait(0.5))
            teleportTrack.append(Func(cleanupDustCloudIval))
        return teleportTrack

    def __getRunTrack(self, elevatorModel, offset, wantToonRotation):
        """
        We get the run track when the toon is within the threshold distance
        away from the elevator.
        The Run Track is an interval of the toon running to the
        elevator seat's offset position. After it reaches the offset position
        the boarding the elevator animation takes over.
        """
        runTrack = Sequence()
        if self.toon:
            if wantToonRotation:
                runTrack.append(Func(self.toon.headsUp, elevatorModel, offset))

            runTrack.append(Func(self.toon.setAnimState, "run"))
            runTrack.append(LerpPosInterval(self.toon, 1, Point3(offset)))

        return runTrack

    def __isInThresholdDist(self, elevatorModel, offset, thresholdDist):
        """
        Checks to see if the toon is within the threshold distance
        from the elevator.
        """
        diff = Point3(offset) - self.toon.getPos()

        return diff.length() <= thresholdDist

    def __isRunPathClear(self, elevatorModel, offsetWrtRender):
        pathClear = True
        source = self.toon.getPos(render)
        dest = offsetWrtRender

        collSegment = CollisionSegment(source[0], source[1], source[2], dest[0], dest[1], dest[2])
        fromObject = render.attachNewNode(CollisionNode("runCollSegment"))
        fromObject.node().addSolid(collSegment)
        fromObject.node().setFromCollideMask(WallBitmask)
        fromObject.node().setIntoCollideMask(BitMask32.allOff())

        queue = CollisionHandlerQueue()
        base.cTrav.addCollider(fromObject, queue)
        base.cTrav.traverse(render)
        queue.sortEntries()
        if queue.getNumEntries():
            for entryNum in range(queue.getNumEntries()):
                entry = queue.getEntry(entryNum)
                hitObject = entry.getIntoNodePath()
                if hitObject.getNetTag("pieCode") != "3":
                    pathClear = False

        base.cTrav.removeCollider(fromObject)
        fromObject.removeNode()
        return pathClear

    def getGoButtonShow(self, elevatorName):
        """
        Return an interval of the toon teleporting out with the time.
        This method is called from DistributedBoardingParty.
        """
        self.elevatorName = elevatorName
        self.timeWarningText = TTLocalizer.BoardingGoShow % self.elevatorName
        self.countdownDuration = 4
        goButtonShow = Sequence()
        if self.toon:
            if self.avId == base.localAvatar.doId:
                goButtonShow.append(Func(self.startTimer))
            goButtonShow.append(self.__getTeleportOutTrack())
            goButtonShow.append(Wait(3))
        goButtonShow.append(Func(self.cleanup))
        return goButtonShow

    def __getTeleportOutTrack(self):
        """
        Return an interval of the toon teleporting out.
        """
        teleportOutTrack = Sequence()
        if self.toon:
            teleportOutTrack.append(Func(self.toon.b_setAnimState, "TeleportOut"))
        return teleportOutTrack

    def getGoButtonPreShow(self):
        """
        Return an interval showing time left for the pre show.
        """
        self.timeWarningText = TTLocalizer.BoardingGoPreShow
        self.countdownDuration = 4
        goButtonPreShow = Sequence()
        if self.toon and self.avId == base.localAvatar.doId:
            goButtonPreShow.append(Func(self.startTimer))
            goButtonPreShow.append(Wait(3))
        goButtonPreShow.append(Func(self.cleanup))
        return goButtonPreShow
