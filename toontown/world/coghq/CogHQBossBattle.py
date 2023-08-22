from direct.fsm import ClassicFSM, State
from panda3d.otp import *

from toontown.world.Place import Place


class CogHQBossBattle(Place):
    notify = directNotify.newCategory("CogHQBossBattle")

    def __init__(self, loader, parentFSM, doneEvent):
        Place.__init__(self, loader, doneEvent)
        self.parentFSM = parentFSM
        self.bossCog = None
        self.teleportInPosHpr = (0, 0, 0, 0, 0, 0)
        self.fsm = ClassicFSM.ClassicFSM(
            "CogHQBossBattle",
            [
                State.State("start", self.enterStart, self.exitStart, ["walk", "teleportIn", "movie"]),
                State.State(
                    "finalBattle",
                    self.enterFinalBattle,
                    self.exitFinalBattle,
                    [
                        "walk",
                        "teleportOut",
                        "died",
                        "movie",
                        "ouch",
                        "crane",
                        "squished",
                    ],
                ),
                State.State("movie", self.enterMovie, self.exitMovie, ["walk", "finalBattle", "died", "teleportOut"]),
                State.State("ouch", self.enterOuch, self.exitOuch, ["walk", "finalBattle", "died", "crane"]),
                State.State(
                    "crane",
                    self.enterCrane,
                    self.exitCrane,
                    ["walk", "finalBattle", "died", "ouch", "squished"],
                ),
                State.State(
                    "walk",
                    self.enterWalk,
                    self.exitWalk,
                    [
                        "teleportOut",
                        "died",
                        "movie",
                        "ouch",
                        "crane",
                        "finalBattle",
                    ],
                ),
                State.State("teleportIn", self.enterTeleportIn, self.exitTeleportIn, ["walk"]),
                State.State("teleportOut", self.enterTeleportOut, self.exitTeleportOut, ["teleportIn", "final"]),
                State.State("died", self.enterDied, self.exitDied, ["final"]),
                State.State(
                    "squished", self.enterSquished, self.exitSquished, ["finalBattle", "crane", "died", "teleportOut"]
                ),
                State.State("final", self.enterFinal, self.exitFinal, ["start"]),
            ],
            "start",
            "final",
        )
        return

    def load(self):
        Place.load(self)
        self.parentFSM.getStateNamed("cogHQBossBattle").addChild(self.fsm)

    def unload(self):
        Place.unload(self)
        self.parentFSM.getStateNamed("cogHQBossBattle").removeChild(self.fsm)
        del self.parentFSM
        del self.fsm
        self.ignoreAll()

    def getTaskZoneId(self):
        return base.cr.playGame.hood.id

    def enter(self, requestStatus, bossCog):
        self.zoneId = requestStatus["zoneId"]
        Place.enter(requestStatus)
        self.fsm.enterInitialState()
        self.bossCog = bossCog
        if self.bossCog:
            self.bossCog.d_avatarEnter()
        else:
            self.acceptOnce("announceBoss", self.__bossGenerate)
        NametagGlobals.setMasterArrowsOn(1)
        base.localAvatar.inventory.setRespectInvasions(0)
        self.fsm.request(requestStatus["how"], [requestStatus])

    def __bossGenerate(self, boss):
        if self.bossCog:
            return
        self.bossCog = boss
        self.bossCog.d_avatarEnter()

    def exit(self):
        self.fsm.requestFinalState()
        base.localAvatar.inventory.setRespectInvasions(1)
        if self.bossCog:
            self.bossCog.d_avatarExit()
        self.bossCog = None
        Place.exit(self)
        return

    def enterFinalBattle(self):
        self.walkStateData.enter()
        self.walkStateData.fsm.request("walking")
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.setTeleportAllowed(0)

    def exitFinalBattle(self):
        self.walkStateData.exit()
        base.localAvatar.setTeleportAllowed(1)

    def enterMovie(self, requestStatus=None):
        base.localAvatar.setTeleportAvailable(0)

    def exitMovie(self):
        pass

    def enterOuch(self):
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.laffMeter.start()

    def exitOuch(self):
        base.localAvatar.laffMeter.stop()

    def enterCrane(self):
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.laffMeter.start()
        base.localAvatar.collisionsOn()

    def exitCrane(self):
        base.localAvatar.collisionsOff()
        base.localAvatar.laffMeter.stop()

    def enterWalk(self, teleportIn=0):
        Place.enterWalk(self, teleportIn)
        self.ignore("teleportQuery")
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.setTeleportAllowed(0)
        self.ignore(self.walkDoneEvent)

    def exitWalk(self):
        Place.exitWalk(self)
        base.localAvatar.setTeleportAllowed(1)

    def enterTeleportIn(self, requestStatus):
        base.localAvatar.detachNode()
        base.localAvatar.setPosHpr(*self.teleportInPosHpr)
        Place.enterTeleportIn(self, requestStatus)

    def enterTeleportOut(self, requestStatus):
        Place.enterTeleportOut(self, requestStatus, self.__teleportOutDone)

    def __teleportOutDone(self, requestStatus):
        hoodId = requestStatus["hoodId"]
        self.doneStatus = requestStatus
        messenger.send(self.doneEvent)

    def enterSquished(self):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState("Flattened")

    def handleSquishDone(self, extraArgs=[]):
        base.cr.playGame.getPlace().setState("walk")

    def exitSquished(self):
        taskMgr.remove(base.localAvatar.uniqueName("finishSquishTask"))
        base.localAvatar.laffMeter.stop()
