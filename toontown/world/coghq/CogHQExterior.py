from direct.fsm import ClassicFSM, State
from panda3d.otp import *

from toontown.world.HoodClientData import getPlaygroundCenterFromId
from toontown.world.Place import Place


class CogHQExterior(Place):
    notify = directNotify.newCategory("CogHQExterior")

    def __init__(self, loader, parentFSM, doneEvent):
        Place.__init__(self, loader, doneEvent)
        self.parentFSM = parentFSM
        self.fsm = ClassicFSM.ClassicFSM(
            "CogHQExterior",
            [
                State.State("start", self.enterStart, self.exitStart, ["walk", "teleportIn", "doorIn"]),
                State.State(
                    "walk",
                    self.enterWalk,
                    self.exitWalk,
                    [
                        "teleportOut",
                        "doorOut",
                        "died",
                        "stopped",
                        "squished",
                        "stopped",
                    ],
                ),
                State.State("stopped", self.enterStopped, self.exitStopped, ["walk", "teleportOut"]),
                State.State("doorIn", self.enterDoorIn, self.exitDoorIn, ["walk", "stopped"]),
                State.State("doorOut", self.enterDoorOut, self.exitDoorOut, ["walk", "stopped"]),
                State.State("squished", self.enterSquished, self.exitSquished, ["walk", "died", "teleportOut"]),
                State.State("teleportIn", self.enterTeleportIn, self.exitTeleportIn, ["walk"]),
                State.State(
                    "teleportOut", self.enterTeleportOut, self.exitTeleportOut, ["teleportIn", "final", "WaitForBattle"]
                ),
                State.State("died", self.enterDied, self.exitDied, ["quietZone"]),
                State.State("final", self.enterFinal, self.exitFinal, ["start"]),
            ],
            "start",
            "final",
        )

    def load(self):
        self.parentFSM.getStateNamed("cogHQExterior").addChild(self.fsm)
        Place.load(self)

    def unload(self):
        self.parentFSM.getStateNamed("cogHQExterior").removeChild(self.fsm)
        del self.fsm
        Place.unload(self)

    def enter(self, requestStatus):
        self.zoneId = requestStatus["zoneId"]
        Place.enter(self)
        self.fsm.enterInitialState()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        self.nodeList = [self.loader.geom]
        self.accept("doorDoneEvent", self.handleDoorDoneEvent)
        self.accept("DistributedDoor_doorTrigger", self.handleDoorTrigger)
        NametagGlobals.setMasterArrowsOn(1)
        how = requestStatus["how"]
        self.fsm.request(how, [requestStatus])

    def exit(self):
        self.fsm.requestFinalState()
        self.loader.music.stop()

        if self.loader.geom:
            self.loader.geom.reparentTo(hidden)
        self.ignoreAll()
        Place.exit(self)

    def enterTeleportIn(self, requestStatus):
        print(requestStatus, base.localAvatar.defaultZone)
        x, y, z, h, p, r = getPlaygroundCenterFromId(base.localAvatar.defaultZone)
        base.localAvatar.setPosHpr(render, x, y, z, h, p, r)
        Place.enterTeleportIn(self, requestStatus)

    def __teleportOutDone(self, requestStatus):
        hoodId = requestStatus["hoodId"]
        zoneId = requestStatus["zoneId"]
        shardId = requestStatus["shardId"]
        if hoodId == self.loader.hood.hoodId and zoneId == self.loader.hood.hoodId and shardId == None:
            self.fsm.request("teleportIn", [requestStatus])
        else:
            self.doneStatus = requestStatus
            messenger.send(self.doneEvent)
        return

    def enterSquished(self):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState("Squish")
        taskMgr.doMethodLater(2.0, self.handleSquishDone, base.localAvatar.uniqueName("finishSquishTask"))

    def handleSquishDone(self, extraArgs=[]):
        base.cr.playGame.getPlace().setState("walk")

    def exitSquished(self):
        taskMgr.remove(base.localAvatar.uniqueName("finishSquishTask"))
        base.localAvatar.laffMeter.stop()
