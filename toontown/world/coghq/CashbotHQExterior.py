from direct.fsm import State
from pandac.PandaModules import *

from toontown.elevators import Elevator
from toontown.world.coghq import CogHQExterior
from toontown.world.coghq import Train


class CashbotHQExterior(CogHQExterior.CogHQExterior):
    notify = directNotify.newCategory("CashbotHQExterior")

    TrackZ = -67
    TrainTracks = [
        {"start": Point3(-1000, -54.45, TrackZ), "end": Point3(2200, -54.45, TrackZ)},
        {"start": Point3(1800, -133.45, TrackZ), "end": Point3(-1200, -133.45, TrackZ)},
        {"start": Point3(-1000, -212.45, TrackZ), "end": Point3(2200, -212.45, TrackZ)},
        {"start": Point3(1800, -291.45, TrackZ), "end": Point3(-1200, -291.45, TrackZ)},
    ]

    def __init__(self, loader, parentFSM, doneEvent):
        CogHQExterior.CogHQExterior.__init__(self, loader, parentFSM, doneEvent)
        self.elevatorDoneEvent = "elevatorDone"
        self.trains = None

        self.fsm.addState(State.State("elevator", self.enterElevator, self.exitElevator, ["walk", "stopped"]))
        state = self.fsm.getStateNamed("walk")
        state.addTransition("elevator")
        state = self.fsm.getStateNamed("stopped")
        state.addTransition("elevator")
        state = self.fsm.getStateNamed("squished")
        state.addTransition("elevator")

    def load(self):
        CogHQExterior.CogHQExterior.load(self)

        if not self.trains:
            self.trains = []
            for track in self.TrainTracks:
                train = Train.Train(track["start"], track["end"], self.TrainTracks.index(track), len(self.TrainTracks))
                self.trains.append(train)

    def unload(self):
        CogHQExterior.CogHQExterior.unload(self)

        for train in self.trains:
            train.delete()
        self.trains = None

    def enter(self, requestStatus):
        CogHQExterior.CogHQExterior.enter(self, requestStatus)

        for train in self.trains:
            train.show()

    def exit(self):
        CogHQExterior.CogHQExterior.exit(self)

        for train in self.trains:
            train.hide()

    def enterElevator(self, distElevator, skipDFABoard=0):
        assert self.notify.debug("enterElevator()")

        self.accept(self.elevatorDoneEvent, self.handleElevatorDone)
        self.elevator = Elevator.Elevator(self.fsm.getStateNamed("elevator"), self.elevatorDoneEvent, distElevator)
        if skipDFABoard:
            self.elevator.skipDFABoard = 1
        self.elevator.load()
        self.elevator.enter()

    def exitElevator(self):
        assert self.notify.debug("exitElevator()")
        self.ignore(self.elevatorDoneEvent)
        self.elevator.unload()
        self.elevator.exit()
        del self.elevator

    def detectedElevatorCollision(self, distElevator):
        assert self.notify.debug("detectedElevatorCollision()")
        self.fsm.request("elevator", [distElevator])

    def handleElevatorDone(self, doneStatus):
        assert self.notify.debug("handleElevatorDone()")
        self.notify.debug("handling elevator done event")
        where = doneStatus["where"]
        if where == "reject":
            if hasattr(base.localAvatar, "elevatorNotifier") and base.localAvatar.elevatorNotifier.isNotifierOpen():
                pass
            else:
                self.fsm.request("walk")
        elif where == "exit":
            self.fsm.request("walk")
        elif where == "mintInterior":
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        else:
            self.notify.error("Unknown mode: " + where + " in handleElevatorDone")
