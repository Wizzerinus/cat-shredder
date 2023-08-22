from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.fsm import StateData
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from direct.showbase import PythonUtil
from pandac.PandaModules import *

from toontown.toonbase import TTLocalizer


class Elevator(StateData.StateData):
    def __init__(self, elevatorState, doneEvent, distElevator):
        StateData.StateData.__init__(self, doneEvent)

        self.fsm = ClassicFSM.ClassicFSM(
            "Elevator",
            [
                State.State("start", self.enterStart, self.exitStart, ["requestBoard"]),
                State.State("requestBoard", self.enterRequestBoard, self.exitRequestBoard, ["boarding"]),
                State.State("boarding", self.enterBoarding, self.exitBoarding, ["boarded"]),
                State.State(
                    "boarded", self.enterBoarded, self.exitBoarded, ["requestExit", "elevatorClosing", "final"]
                ),
                State.State("requestExit", self.enterRequestExit, self.exitRequestExit, ["exiting", "elevatorClosing"]),
                State.State("elevatorClosing", self.enterElevatorClosing, self.exitElevatorClosing, ["final"]),
                State.State("exiting", self.enterExiting, self.exitExiting, ["final"]),
                State.State("final", self.enterFinal, self.exitFinal, ["start"]),
            ],
            "start",
            "final",
        )

        self.dfaDoneEvent = "elevatorDfaDoneEvent"
        self.elevatorState = elevatorState
        self.distElevator = distElevator
        if distElevator:
            distElevator.elevatorFSM = self
        self.reverseBoardingCamera = False
        self.skipDFABoard = 0

    def load(self):
        self.elevatorState.addChild(self.fsm)
        self.buttonModels = loader.loadModel("phase_3.5/models/gui/inventory_gui")
        self.upButton = self.buttonModels.find("**/InventoryButtonUp")
        self.downButton = self.buttonModels.find("**/InventoryButtonDown")
        self.rolloverButton = self.buttonModels.find("**/InventoryButtonRollover")

    def unload(self):
        self.elevatorState.removeChild(self.fsm)
        if self.distElevator:
            self.distElevator.elevatorFSM = None
        del self.distElevator
        del self.fsm
        del self.elevatorState
        self.buttonModels.removeNode()
        del self.buttonModels
        del self.upButton
        del self.downButton
        del self.rolloverButton

    def enter(self):
        self.fsm.enterInitialState()
        if self.distElevator:
            self.fsm.request("requestBoard")

    def exit(self):
        self.ignoreAll()

    def signalDone(self, doneStatus):
        messenger.send(self.doneEvent, [doneStatus])

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def enterRequestBoard(self):
        messenger.send(self.distElevator.uniqueName("enterElevatorOK"))

    def exitRequestBoard(self):
        pass

    def enterBoarding(self, nodePath):
        camera.wrtReparentTo(nodePath)
        if self.reverseBoardingCamera:
            heading = PythonUtil.fitDestAngle2Src(camera.getH(nodePath), 180)
            self.cameraBoardTrack = LerpPosHprInterval(camera, 1.5, Point3(0, 18, 8), Point3(heading, -10, 0))
        else:
            self.cameraBoardTrack = LerpPosHprInterval(camera, 1.5, Point3(0, -16, 5.5), Point3(0, 0, 0))

        self.cameraBoardTrack.start()

    def exitBoarding(self):
        self.ignore("boardedElevator")

    def enterBoarded(self):
        self.enableExitButton()

    def exitBoarded(self):
        self.cameraBoardTrack.finish()
        self.disableExitButton()

    def enableExitButton(self):
        self.exitButton = DirectButton(
            relief=None,
            text=TTLocalizer.ElevatorHopOff,
            text_fg=(0.9, 0.9, 0.9, 1),
            text_pos=(0, -0.23),
            text_scale=0.8,
            image=(self.upButton, self.downButton, self.rolloverButton),
            image_color=(0.5, 0.5, 0.5, 1),
            image_scale=(20, 1, 11),
            pos=(0, 0, 0.8),
            scale=0.15,
            command=lambda self=self: self.fsm.request("requestExit"),
        )

        if (
            hasattr(base.localAvatar, "boardingParty")
            and base.localAvatar.boardingParty
            and base.localAvatar.boardingParty.getGroupLeader(base.localAvatar.doId)
            and base.localAvatar.boardingParty.getGroupLeader(base.localAvatar.doId) != base.localAvatar.doId
        ):
            self.exitButton["command"] = None
            self.exitButton.hide()

    def disableExitButton(self):
        self.exitButton.destroy()

    def enterRequestExit(self):
        messenger.send("elevatorExitButton")

    def exitRequestExit(self):
        pass

    def enterElevatorClosing(self):
        assert self.notify.debug("enterElevatorClosing()")

    def exitElevatorClosing(self):
        pass

    def enterExiting(self):
        pass

    def exitExiting(self):
        pass

    def enterFinal(self):
        assert self.notify.debug("enterFinal()")

    def exitFinal(self):
        pass

    def setReverseBoardingCamera(self, newVal):
        """Set the flag if True, we reverse the boarding camera."""
        self.reverseBoardingCamera = newVal
