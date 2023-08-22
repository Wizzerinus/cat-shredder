from direct.fsm import StateData
from direct.gui import OnscreenText
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

from . import QuietZoneState
from . import ZoneUtil
from .HoodClientData import getFullnameFromId
from toontown.toonbase.TTLZones import PlaceNames
from toontown.toonbase.globals.TTGlobalsGUI import getSignFont


class Hood(StateData.StateData):
    """
    The base class for the Hood State Data
    Every neighborhood should have a Hood subclass to implement
    neighborhood specific things like fog

    To subclass from hood, you need to define a Town, a SafeZone, a storage
    DNA file, and an id.
    """

    notify = directNotify.newCategory("Hood")

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        assert self.notify.debug(
            "__init__(parentFSM="
            + str(parentFSM)
            + ", doneEvent="
            + str(doneEvent)
            + ", dnaStore="
            + str(dnaStore)
            + ")"
        )
        StateData.StateData.__init__(self, doneEvent)

        self.parentFSM = parentFSM
        self.dnaStore = dnaStore

        self.loaderDoneEvent = "loaderDone"

        self.hoodId = hoodId

        self.titleText = None
        self.titleTextSeq = None
        self.titleColor = (1, 1, 1, 1)

        self.holidayStorageDNADict = {}

        self.spookySkyFile = None
        self.halloweenLights = []

    def enter(self, requestStatus):
        """
        enter this hood and start the state machine
        """
        assert self.notify.debug("enter(requestStatus=" + str(requestStatus) + ")")
        requestStatus["hoodId"]
        zoneId = requestStatus["zoneId"]

        hoodText = self.getHoodText(zoneId)

        self.titleText = OnscreenText.OnscreenText(
            hoodText,
            fg=self.titleColor,
            font=getSignFont(),
            pos=(0, -0.5),
            scale=0.16,
            drawOrder=0,
            mayChange=1,
        )

        self.fsm.request(requestStatus["loader"], [requestStatus])

    def getHoodText(self, zoneId):
        hoodText = getFullnameFromId(self.hoodId)
        streetName = PlaceNames.get(ZoneUtil.getBranchZone(zoneId))
        if streetName:
            hoodText = hoodText + "\n" + streetName[-1]

        return hoodText

    def spawnTitleText(self, zoneId):
        hoodText = self.getHoodText(zoneId)
        self.doSpawnTitleText(hoodText)

    def doSpawnTitleText(self, text):
        self.titleText.setText(text)
        self.titleText.show()
        self.titleText.setColor(Vec4(*self.titleColor))
        self.titleText.clearColorScale()
        self.titleText.setFg(self.titleColor)
        self.titleTextSeq = Sequence(
            Wait(0.1),
            Wait(6.0),
            self.titleText.colorScaleInterval(0.5, Vec4(1.0, 1.0, 1.0, 1.0), Vec4(1.0, 1.0, 1.0, 0.0)),
            Func(self.hideTitleText),
        )
        self.titleTextSeq.start()

    def hideTitleText(self):
        """
        This gets called from the town and safe zone to cleanup
        the title text if we leave walk mode for instance
        """
        assert self.notify.debug("hideTitleText()")
        if self.titleText:
            self.titleText.hide()

    def exit(self):
        """
        exit this hood
        """
        assert self.notify.debug("exit()")
        taskMgr.remove("titleText")
        if self.titleTextSeq:
            self.titleTextSeq.finish()
            self.titleTextSeq = None
        if self.titleText:
            self.titleText.cleanup()
            self.titleText = None
        base.localAvatar.stopChat()

    def load(self):
        """
        load the hood models and dna storage
        """
        assert self.notify.debug("load()")
        if self.storageDNAFile:
            loadDNAFile(self.dnaStore, self.storageDNAFile)

        self.sky = loader.loadModel(self.skyFile)
        self.sky.setTag("sky", "Regular")
        self.sky.setScale(1.0)
        self.sky.setFogOff()

    def unload(self):
        """
        unload the hood models and dna storage
        """
        assert self.notify.debug("unload()")

        if hasattr(self, "loader"):
            self.notify.info("Aggressively cleaning up loader: %s" % (self.loader))
            self.loader.exit()
            self.loader.unload()
            del self.loader

        del self.fsm
        del self.parentFSM

        self.dnaStore.resetHood()
        del self.dnaStore

        self.sky.removeNode()
        del self.sky

        self.ignoreAll()
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enterStart(self):
        assert self.notify.debug("enterStart()")

    def exitStart(self):
        assert self.notify.debug("exitStart()")

    def isSameHood(self, status):
        """return true if the request status is in the same hood"""
        return status["hoodId"] == self.hoodId and status["shardId"] is None

    def enterFinal(self):
        """enterFinal(self)"""
        assert self.notify.debug("enterFinal()")

    def exitFinal(self):
        """exitFinal(self)"""
        assert self.notify.debug("exitFinal()")

    def enterQuietZone(self, requestStatus):
        assert self.notify.debug("enterQuietZone(requestStatus = %s)" % (requestStatus))
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

    def loadLoader(self, requestStatus):
        pass

    def handleWaitForSetZoneResponse(self, requestStatus):
        assert self.notify.debug("handleWaitForSetZoneResponse(requestStatus=" + str(requestStatus) + ")")
        self.loadLoader(requestStatus)

    def handleQuietZoneDone(self):
        assert self.notify.debug("handleQuietZoneDone()")
        status = self.quietZoneStateData.getRequestStatus()
        self.fsm.request(status["loader"], [status])

    def enterSafeZoneLoader(self, requestStatus):
        """enterSafeZoneLoader(self)"""
        assert self.notify.debug("enterSafeZoneLoader()")
        self.accept(self.loaderDoneEvent, self.handleSafeZoneLoaderDone)
        self.loader.enter(requestStatus)
        self.spawnTitleText(requestStatus["zoneId"])

    def exitSafeZoneLoader(self):
        """exitSafeZoneLoader(self)"""
        assert self.notify.debug("exitSafeZoneLoader()")
        taskMgr.remove("titleText")
        self.hideTitleText()
        self.ignore(self.loaderDoneEvent)
        self.loader.exit()
        self.loader.unload()
        del self.loader

    def handleSafeZoneLoaderDone(self):
        assert self.notify.debug("handleSafeZoneLoaderDone()")
        doneStatus = self.loader.getDoneStatus()
        if (self.isSameHood(doneStatus) and doneStatus["where"] != "party") or doneStatus["loader"] == "minigame":
            self.fsm.request("quietZone", [doneStatus])
        else:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def startSky(self):
        self.sky.reparentTo(camera)
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def stopSky(self):
        taskMgr.remove("skyTrack")
        self.sky.reparentTo(hidden)

    def startSpookySky(self):
        if not self.spookySkyFile:
            return
        if hasattr(self, "sky") and self.sky:
            self.stopSky()
        self.sky = loader.loadModel(self.spookySkyFile)
        self.sky.setTag("sky", "Halloween")
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.reparentTo(camera)

        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(
            1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType="easeInOut"
        )
        fadeIn.start()

        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def endSpookySky(self):
        if hasattr(self, "sky") and self.sky:
            self.sky.reparentTo(hidden)
        if hasattr(self, "sky"):
            self.sky = loader.loadModel(self.skyFile)
            self.sky.setTag("sky", "Regular")
            self.sky.setScale(1.0)
            self.startSky()
