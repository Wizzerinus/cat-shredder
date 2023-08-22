from otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI

from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from toontown.toonbase.globals.TTGlobalsCore import *


class ToontownUDRepository(ToontownInternalRepository):
    InitialContext = 100000

    notify = directNotify.newCategory("ToontownUDRepository")

    def __init__(self, baseChannel, serverId):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix="UD")
        self.astronLoginManager = None

        self.context = self.InitialContext
        self.contextToClassName = {}

        self.onlineAccountDetails = {}
        self.onlineAvatars = {}
        self.onlinePlayers = {}
        self.pending = {}
        self.doId2doCache = {}
        self.ttFriendsManager = None

    def handleConnected(self):
        self.notify.info(f"Creating root object ({self.getGameDoId()})...")
        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)

        self.notify.info("Creating global objects...")
        self.createGlobals()

        self.notify.info("UberDOG server is ready.")

    def createGlobals(self):
        self.astronLoginManager = self.generateGlobalObject(OTP_DO_ID_ASTRON_LOGIN_MANAGER, "AstronLoginManager")

        self.chatRouter = self.generateGlobalObject(OTP_DO_ID_CHAT_ROUTER, "ChatRouter")

        self.ttFriendsManager = self.generateGlobalObject(OTP_DO_ID_TT_FRIENDS_MANAGER, "TTFriendsManager")

    def allocateContext(self):
        self.context += 1
        if self.context >= (1 << 32):
            self.context = self.InitialContext
        return self.context
