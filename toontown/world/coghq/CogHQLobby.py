from direct.fsm import ClassicFSM, State
from panda3d.otp import *

from toontown.elevators import Elevator
from toontown.world import Place
from toontown.world.HoodClientData import getPlaygroundCenterFromId


class CogHQLobby(Place.Place):
    notify = directNotify.newCategory("CogHQLobby")

    def __init__(self, hood, parentFSM, doneEvent):
        assert self.notify.debug("__init__()")
        Place.Place.__init__(self, hood, doneEvent)
        self.parentFSM = parentFSM
        self.elevatorDoneEvent = "elevatorDone"
        self.fsm = ClassicFSM.ClassicFSM(
            "CogHQLobby",
            [
                State.State(
                    "start",
                    self.enterStart,
                    self.exitStart,
                    [
                        "walk",
                        "tunnelIn",
                        "teleportIn",
                        "doorIn",
                    ],
                ),
                State.State(
                    "walk",
                    self.enterWalk,
                    self.exitWalk,
                    [
                        "elevator",
                        "doorOut",
                        "stopped",
                    ],
                ),
                State.State(
                    "stopped",
                    self.enterStopped,
                    self.exitStopped,
                    [
                        "walk",
                        "teleportOut",
                        "elevator",
                    ],
                ),
                State.State("doorIn", self.enterDoorIn, self.exitDoorIn, ["walk"]),
                State.State("doorOut", self.enterDoorOut, self.exitDoorOut, ["walk"]),
                State.State(
                    "teleportIn",
                    self.enterTeleportIn,
                    self.exitTeleportIn,
                    [
                        "walk",
                    ],
                ),
                State.State("elevator", self.enterElevator, self.exitElevator, ["walk", "stopped"]),
                State.State("final", self.enterFinal, self.exitFinal, ["start"]),
            ],
            "start",
            "final",
        )

    def load(self):
        self.parentFSM.getStateNamed("cogHQLobby").addChild(self.fsm)
        Place.Place.load(self)

    def unload(self):
        self.parentFSM.getStateNamed("cogHQLobby").removeChild(self.fsm)
        Place.Place.unload(self)
        self.fsm = None

    def enter(self, requestStatus):
        self.zoneId = requestStatus["zoneId"]
        Place.Place.enter(self)
        self.fsm.enterInitialState()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        self.accept("doorDoneEvent", self.handleDoorDoneEvent)
        self.accept("DistributedDoor_doorTrigger", self.handleDoorTrigger)
        NametagGlobals.setMasterArrowsOn(1)
        how = requestStatus["how"]
        self.fsm.request(how, [requestStatus])

    def exit(self):
        self.fsm.requestFinalState()
        self.ignoreAll()
        self.loader.music.stop()
        if self.loader.geom is not None:
            self.loader.geom.reparentTo(hidden)
        Place.Place.exit(self)

    def enterWalk(self, teleportIn=0):
        Place.Place.enterWalk(self, teleportIn)
        self.ignore("teleportQuery")
        base.localAvatar.setTeleportAvailable(0)

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
        elif where == "cogHQBossBattle":
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        else:
            self.notify.error("Unknown mode: " + where + " in handleElevatorDone")

    def enterTeleportIn(self, requestStatus):
        x, y, z, h, p, r = getPlaygroundCenterFromId(base.localAvatar.defaultZone)
        base.localAvatar.setPosHpr(render, x, y, z, h, p, r)
        Place.Place.enterTeleportIn(self, requestStatus)
