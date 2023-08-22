"""
PlayGame module: contains the PlayGame class
"""

from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.fsm import StateData
from panda3d.core import *
from panda3d.toontown import DNAStorage, loadDNAFile

from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont, getSignFont, getSuitFont
from toontown.toonbase.globals.TTGlobalsWorld import ZoneIDs
from toontown.world import QuietZoneState, ZoneUtil
from toontown.world.coghq import CashbotHQ


class PlayGame(StateData.StateData):
    """PlayGame class"""

    notify = directNotify.newCategory("PlayGame")

    Hood2ClassDict = {
        ZoneIDs.CashbotHQ: CashbotHQ.CashbotHQ,
    }

    Hood2StateDict = {
        ZoneIDs.CashbotHQ: "CashbotHQ",
    }

    def __init__(self, parentFSM, doneEvent):
        """__init__(self, ClassicFSM, string)
        PlayGame constructor: create a play game ClassicFSM
        """
        StateData.StateData.__init__(self, doneEvent)
        self.place = None
        self.fsm = ClassicFSM.ClassicFSM(
            "PlayGame",
            [
                State.State("start", self.enterStart, self.exitStart, ["quietZone"]),
                State.State(
                    "quietZone",
                    self.enterQuietZone,
                    self.exitQuietZone,
                    [
                        "CashbotHQ",
                    ],
                ),
                State.State("CashbotHQ", self.enterCashbotHQ, self.exitCashbotHQ, ["quietZone"]),
            ],
            "start",
            "start",
        )

        self.fsm.enterInitialState()

        self.parentFSM = parentFSM
        self.parentFSM.getStateNamed("playGame").addChild(self.fsm)
        self.hoodDoneEvent = "hoodDone"
        self.hood = None

    def enter(self, requestStatus):
        """enter(self)
        You will only get this case if you came from outside this shard
        This means login, or switching shards
        avId is the avatar to teleport to, or -1 to put you at the
        safezone.
        """

        zoneId = requestStatus["zoneId"]
        hoodId = ZoneUtil.getHoodId(zoneId)
        avId = requestStatus.get("avId", -1)
        loaderName = ZoneUtil.getLoaderName(zoneId)
        whereName = ZoneUtil.getToonWhereName(zoneId)

        self.fsm.request(
            "quietZone",
            [
                {
                    "loader": loaderName,
                    "where": whereName,
                    "how": "teleportIn",
                    "hoodId": hoodId,
                    "zoneId": zoneId,
                    "shardId": None,
                    "avId": avId,
                }
            ],
        )

    def exit(self):
        """exit(self)"""

    def load(self):
        """load(self)"""

    def loadDnaStore(self):
        if not hasattr(self, "dnaStore"):
            self.dnaStore = DNAStorage()
            # No storage DNA needed for Cashbot HQ
            # loadDNAFile(self.dnaStore, "phase_4/dna/storage.dna")

            self.dnaStore.storeFont("humanist", getInterfaceFont())
            self.dnaStore.storeFont("mickey", getSignFont())
            self.dnaStore.storeFont("suit", getSuitFont())

            # loadDNAFile(self.dnaStore, "phase_3.5/dna/storage_interior.dna")

    def unloadDnaStore(self):
        if hasattr(self, "dnaStore"):
            self.dnaStore.resetNodes()
            self.dnaStore.resetTextures()
            del self.dnaStore
            ModelPool.garbageCollect()
            TexturePool.garbageCollect()

    def unload(self):
        """unload(self)"""
        self.unloadDnaStore()

        if self.hood:
            self.notify.info("Aggressively cleaning up hood: %s" % (self.hood))
            self.hood.exit()
            self.hood.unload()
            self.hood = None

    def enterStart(self):
        """enterStart(self)"""

    def exitStart(self):
        """exitStart(self)"""

    def handleHoodDone(self):
        doneStatus = self.hood.getDoneStatus()
        shardId = doneStatus["shardId"]
        if shardId is not None:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
            base.transitions.fadeOut(0)
            return

        if doneStatus["where"] == "party":
            self.getPartyZoneAndGoToParty(doneStatus["avId"], doneStatus["zoneId"])
            return

        how = doneStatus["how"]
        if how in ["teleportIn", "doorIn", "elevatorIn"]:
            self.fsm.request("quietZone", [doneStatus])
        else:
            self.notify.error("Exited hood with unexpected mode %s" % (how))

    def _destroyHood(self):
        self.ignore(self.hoodDoneEvent)
        self.hood.exit()
        self.hood.unload()
        self.hood = None
        base.cr.cache.flush()

    def enterQuietZone(self, requestStatus):
        assert self.notify.debug("enterQuietZone()")
        self.quietZoneDoneEvent = "quietZoneDone"
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.acceptOnce("enterWaitForSetZoneResponse", self.handleWaitForSetZoneResponse)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        assert self.notify.debug("exitQuietZone()")
        self.ignore(self.quietZoneDoneEvent)
        self.ignore("enterWaitForSetZoneResponse")
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None

    def handleWaitForSetZoneResponse(self, requestStatus):
        assert self.notify.debug("handleWaitForSetZoneResponse(requestStatus=" + str(requestStatus) + ")")

        hoodId = requestStatus["hoodId"]
        self.loadDnaStore()
        hoodClass = self.getHoodClassByNumber(hoodId)

        self.hood = hoodClass(self.fsm, self.hoodDoneEvent, self.dnaStore, hoodId)
        self.hood.load()
        self.hood.loadLoader(requestStatus)

    def handleQuietZoneDone(self):
        assert self.notify.debug("handleQuietZoneDone()")
        status = self.quietZoneStateData.getRequestStatus()
        hoodId = status["hoodId"]
        hoodState = self.getHoodStateByNumber(hoodId)
        self.fsm.request(hoodState, [status])

    def enterCashbotHQ(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitCashbotHQ(self):
        self._destroyHood()

    def getCatalogCodes(self, category):
        numCodes = self.dnaStore.getNumCatalogCodes(category)
        codes = []
        for i in range(numCodes):
            codes.append(self.dnaStore.getCatalogCode(category, i))
        return codes

    def getNodePathList(self, catalogGroup):
        result = []
        codes = self.getCatalogCodes(catalogGroup)
        for code in codes:
            np = self.dnaStore.findNode(code)
            result.append(np)
        return result

    def getNodePathDict(self, catalogGroup):
        result = {}
        codes = self.getCatalogCodes(catalogGroup)
        for code in codes:
            np = self.dnaStore.findNode(code)
            result[code] = np
        return result

    def getHoodClassByNumber(self, hoodNumber):
        return self.Hood2ClassDict[hoodNumber]

    def getHoodStateByNumber(self, hoodNumber):
        return self.Hood2StateDict[hoodNumber]

    def setPlace(self, place):
        self.place = place
        if self.place:
            messenger.send("playGameSetPlace")

    def getPlace(self):
        return self.place

    def getPlaceId(self):
        if self.hood:
            return self.hood.hoodId

        return None
