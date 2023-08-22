from direct.fsm import ClassicFSM, State
from direct.fsm import StateData
from pandac.PandaModules import *

from . import CogHQLobby
from toontown.world import QuietZoneState, ZoneUtil


class CogHQLoader(StateData.StateData):
    notify = directNotify.newCategory("CogHQLoader")

    def __init__(self, hood, parentFSMState, doneEvent):
        assert self.notify.debug(
            "__init__(hood="
            + str(hood)
            + ", parentFSMState="
            + str(parentFSMState)
            + ", doneEvent="
            + str(doneEvent)
            + ")"
        )
        StateData.StateData.__init__(self, doneEvent)
        self.hood = hood
        self.parentFSMState = parentFSMState
        self.placeDoneEvent = "cogHQLoaderPlaceDone"
        self.fsm = ClassicFSM.ClassicFSM(
            "CogHQLoader",
            [
                State.State(
                    "start",
                    None,
                    None,
                    [
                        "quietZone",
                        "cogHQExterior",  # Tunnel from toon hood
                        "cogHQBossBattle",  # magic word ~bossBattle
                        "cogHQLobby",  # current settings
                    ],
                ),
                State.State(
                    "cogHQExterior",
                    self.enterCogHQExterior,
                    self.exitCogHQExterior,
                    [
                        "quietZone",
                        "cogHQLobby",  # Door transition
                    ],
                ),
                State.State(
                    "cogHQLobby",
                    self.enterCogHQLobby,
                    self.exitCogHQLobby,
                    [
                        "quietZone",
                        "cogHQExterior",  # Front door
                        "cogHQBossBattle",  # Elevator to top
                    ],
                ),
                State.State(
                    "cogHQBossBattle",
                    self.enterCogHQBossBattle,
                    self.exitCogHQBossBattle,
                    [
                        "quietZone",
                    ],
                ),
                State.State(
                    "quietZone",
                    self.enterQuietZone,
                    self.exitQuietZone,
                    [
                        "cogHQExterior",
                        "cogHQLobby",
                        "cogHQBossBattle",
                    ],
                ),
                State.State("final", None, None, ["start"]),
            ],
            "start",
            "final",
        )

    def load(self, zoneId):
        self.parentFSMState.addChild(self.fsm)
        self.music = base.loader.loadMusic(self.musicFile)
        self.loadPlaceGeom(zoneId)

    def loadPlaceGeom(self, zoneId):
        return

    def unloadPlaceGeom(self):
        return

    def unload(self):
        assert self.notify.debug("unload()")
        self.unloadPlaceGeom()
        self.parentFSMState.removeChild(self.fsm)
        del self.parentFSMState
        del self.fsm
        del self.hood
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enter(self, requestStatus):
        self.fsm.enterInitialState()
        self.fsm.request(requestStatus["where"], [requestStatus])

    def exit(self):
        self.ignoreAll()

    def enterQuietZone(self, requestStatus):
        self.quietZoneDoneEvent = "quietZoneDone"
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self.quietZoneDoneEvent)
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None

    def handleQuietZoneDone(self):
        status = self.quietZoneStateData.getRequestStatus()
        self.fsm.request(status["where"], [status])

    def enterPlace(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.placeDone)
        self.place = self.placeClass(self, self.fsm, self.placeDoneEvent)
        base.cr.playGame.setPlace(self.place)
        self.place.load()
        self.place.enter(requestStatus)

    def exitPlace(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)

    def placeDone(self):
        self.requestStatus = self.place.doneStatus
        assert self.notify.debug("placeDone() doneStatus=" + str(self.requestStatus))
        status = self.place.doneStatus
        if (status.get("shardId") is None) and self.isInThisHq(status):
            self.unloadPlaceGeom()
            zoneId = status["zoneId"]
            self.loadPlaceGeom(zoneId)
            self.fsm.request("quietZone", [status])
        else:
            self.doneStatus = status
            messenger.send(self.doneEvent)

    def isInThisHq(self, status):
        if ZoneUtil.isDynamicZone(status["zoneId"]):
            return status["hoodId"] == self.hood.hoodId

        return ZoneUtil.getHoodId(status["zoneId"]) == self.hood.hoodId

    def enterCogHQExterior(self, requestStatus):
        self.placeClass = self.getExteriorPlaceClass()
        self.enterPlace(requestStatus)
        self.hood.spawnTitleText(requestStatus["zoneId"])

    def exitCogHQExterior(self):
        taskMgr.remove("titleText")
        self.hood.hideTitleText()
        self.exitPlace()
        self.placeClass = None

    def enterCogHQLobby(self, requestStatus):
        self.placeClass = CogHQLobby.CogHQLobby
        self.enterPlace(requestStatus)
        self.hood.spawnTitleText(requestStatus["zoneId"])

    def exitCogHQLobby(self):
        taskMgr.remove("titleText")
        self.hood.hideTitleText()
        self.exitPlace()
        self.placeClass = None

    def enterCogHQBossBattle(self, requestStatus):
        self.placeClass = self.getBossPlaceClass()
        self.enterPlace(requestStatus)

    def exitCogHQBossBattle(self):
        self.exitPlace()
        self.placeClass = None
