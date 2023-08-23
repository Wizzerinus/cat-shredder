from direct.task.Task import Task
from panda3d.core import *
from panda3d.toontown import *

from otp.ai.AIZoneData import AIZoneDataStore
from otp.ai.TimeManagerAI import TimeManagerAI
from otp.distributed.DistributedDistrictAI import DistributedDistrictAI
from toontown.chat.magic.DistributedMagicWordManagerAI import DistributedMagicWordManagerAI
from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from toontown.toonbase.globals.TTGlobalsCore import *
from toontown.toonbase.globals.TTGlobalsWorld import DynamicZonesBegin, DynamicZonesEnd, ZoneIDs
from toontown.world import ZoneUtil
from toontown.world.coghq.CashbotHQDataAI import CashbotHQDataAI


class ToontownAIRepository(ToontownInternalRepository):
    notify = directNotify.newCategory("ToontownAIRepository")

    def __init__(self, baseChannel, serverId, districtName):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix="AI")

        self.districtName = districtName
        self.districtId = 0
        self.district = None
        self.zoneDataStore = None
        self.zoneAllocator = None

        self.dnaStoreMap = {}
        self.dnaDataMap = {}
        self.hoods = []

        self._population = 0

        self._avatarDisconnectReasons = {}

    def handleConnected(self):
        self.districtId = self.allocateChannel()
        self.district = DistributedDistrictAI(self)
        self.district.setName(self.districtName)
        self.district.generateWithRequiredAndId(self.districtId, self.getGameDoId(), OTP_ZONE_ID_DISTRICTS)

        self.district.setAI(self.ourChannel)

        self.createLocals()
        self.createGlobals()

        self.createZones()

        self.district.b_setAvailable(True)
        self.notify.info("Done.")
        self.__leaderboardFlush(None)
        taskMgr.doMethodLater(30, self.__leaderboardFlush, "leaderboardFlush", appendTask=True)

    def createGlobals(self):
        self.timeManager = TimeManagerAI(self)
        self.timeManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        self.magicWordManager = DistributedMagicWordManagerAI(self)
        self.magicWordManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

    def __leaderboardFlush(self, task):
        messenger.send("leaderboardFlush")
        return Task.again

    def createLocals(self):
        """
        Creates "local" (non-distributed) objects.
        """

        self.zoneDataStore = AIZoneDataStore()

        self.zoneAllocator = UniqueIdAllocator(DynamicZonesBegin, DynamicZonesEnd)

    def generateHood(self, hoodConstructor, zoneId):
        self.dnaStoreMap[zoneId] = DNAStorage()
        dnaFile = ZoneUtil.genDNAFileName(zoneId)
        self.dnaDataMap[zoneId] = loadDNAFileAI(self.dnaStoreMap[zoneId], dnaFile)

        hood = hoodConstructor(self, zoneId)
        hood.startup()
        self.hoods.append(hood)

    def createZones(self):
        self.generateHood(CashbotHQDataAI, ZoneIDs.CashbotHQ)

    def getAvatarExitEvent(self, avId):
        return f"distObjDelete-{int(avId)}"

    def setAvatarDisconnectReason(self, avId, disconnectReason):
        self._avatarDisconnectReasons[avId] = disconnectReason

    def getAvatarDisconnectReason(self, avId):
        return self._avatarDisconnectReasons.get(avId, 0)

    def getZoneDataStore(self):
        return self.zoneDataStore

    def incrementPopulation(self):
        self._population += 1

    def decrementPopulation(self):
        if __dev__:
            assert self._population > 0
        self._population = max(0, self._population - 1)

    def allocateZone(self):
        return self.zoneAllocator.allocate()

    def deallocateZone(self, zone):
        self.zoneAllocator.free(zone)

    def createPondBingoMgrAI(self, estate):
        """
        estate - the estate for which the PBMgrAI should
                be created.
        returns: None

        This method instructs the BingoManagerAI to
        create a new PBMgrAI for a newly generated
        estate.
        """
        if self.bingoMgr:
            self.notify.info("createPondBingoMgrAI: Creating a DPBMAI for Dynamic Estate")
            self.bingoMgr.createPondBingoMgrAI(estate, 1)
