import inspect
import os
import random
import sys
import types

from direct.distributed import DistributedSmoothNode
from direct.distributed.ClientRepositoryBase import ClientRepositoryBase
from direct.distributed.MsgTypes import MsgName2Id
from direct.distributed.PyDatagram import PyDatagram
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.showbase.PythonUtil import Functor
from direct.task import Task
from panda3d.core import (
    ConfigVariableInt,
    Datagram,
    DatagramIterator,
    HashVal,
    NodePath,
    Notify,
    hashPrcVariables,
)
from panda3d.otp import WhisperPopup

from otp.distributed import DCClassImports, DisneyMessageTypes
from otp.distributed.PotentialAvatar import PotentialAvatar
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals.TTGlobalsCore import *
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont
from toontown.toontowngui import OTPDialog
from toontown.toontowngui.TTDialog import TTDialog, TTGlobalDialog


class OTPClientRepository(ClientRepositoryBase):
    notify = directNotify.newCategory("OTPClientRepository")

    avatarLimit = 6

    hashVal = 0
    serverList = None
    avList = None
    cleanGameExit = None
    handlerArgs = None
    distributedDistrict = None

    connectingBox = None
    failedToConnectBox = None
    missingGameRootObjectBox = None
    noShardsBox = None
    lostConnectionBox = None
    afkDialog = None
    rejectRemoveAvatarBox = None

    def __init__(self, serverVersion, playGame=None):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.dclassesByName = {}
        self.dclassesByNumber = {}
        ClientRepositoryBase.__init__(self)

        self.handler = None

        self.__currentAvId = 0

        self.createAvatarClass = None

        self.systemMessageSfx = None

        self.playToken = os.getenv("TT_PLAYCOOKIE", "faketoken")

        self.parentMgr.registerParent(SPRender, base.render)
        self.parentMgr.registerParent(SPHidden, NodePath())

        self.timeManager = None

        self.activeDistrictMap = {}

        self.serverVersion = serverVersion

        self.waitingForDatabase = None

        self.loginFSM = ClassicFSM(
            "loginFSM",
            [
                State("loginOff", self.enterLoginOff, self.exitLoginOff, ["connect"]),
                State(
                    "connect",
                    self.enterConnect,
                    self.exitConnect,
                    ["login", "failedToConnect"],
                ),
                State(
                    "login",
                    self.enterLogin,
                    self.exitLogin,
                    [
                        "noConnection",
                        "waitForGameList",
                        "reject",
                        "failedToConnect",
                        "shutdown",
                    ],
                ),
                State(
                    "failedToConnect",
                    self.enterFailedToConnect,
                    self.exitFailedToConnect,
                    ["connect", "shutdown", "noConnection"],
                ),
                State(
                    "shutdown",
                    self.enterShutdown,
                    self.exitShutdown,
                    [
                        "loginOff",
                    ],
                ),
                State(
                    "waitForGameList",
                    self.enterWaitForGameList,
                    self.exitWaitForGameList,
                    [
                        "noConnection",
                        "waitForShardList",
                        "missingGameRootObject",
                    ],
                ),
                State(
                    "missingGameRootObject",
                    self.enterMissingGameRootObject,
                    self.exitMissingGameRootObject,
                    [
                        "waitForGameList",
                        "shutdown",
                    ],
                ),
                State(
                    "waitForShardList",
                    self.enterWaitForShardList,
                    self.exitWaitForShardList,
                    [
                        "noConnection",
                        "waitForAvatarList",
                        "noShards",
                        "shutdown",
                    ],
                ),
                State(
                    "noShards",
                    self.enterNoShards,
                    self.exitNoShards,
                    [
                        "noConnection",
                        "noShardsWait",
                        "shutdown",
                    ],
                ),
                State(
                    "noShardsWait",
                    self.enterNoShardsWait,
                    self.exitNoShardsWait,
                    [
                        "noConnection",
                        "waitForShardList",
                        "shutdown",
                    ],
                ),
                State("reject", self.enterReject, self.exitReject, []),
                State(
                    "noConnection",
                    self.enterNoConnection,
                    self.exitNoConnection,
                    [
                        "login",
                        "connect",
                        "shutdown",
                    ],
                ),
                State(
                    "afkTimeout",
                    self.enterAfkTimeout,
                    self.exitAfkTimeout,
                    [
                        "waitForAvatarList",
                        "shutdown",
                    ],
                ),
                State(
                    "waitForAvatarList",
                    self.enterWaitForAvatarList,
                    self.exitWaitForAvatarList,
                    [
                        "noConnection",
                        "chooseAvatar",
                        "shutdown",
                    ],
                ),
                State(
                    "chooseAvatar",
                    self.enterChooseAvatar,
                    self.exitChooseAvatar,
                    [
                        "noConnection",
                        "createAvatar",
                        "waitForAvatarList",
                        "waitForSetAvatarResponse",
                        "waitForDeleteAvatarResponse",
                        "shutdown",
                        "login",
                    ],
                ),
                State(
                    "createAvatar",
                    self.enterCreateAvatar,
                    self.exitCreateAvatar,
                    [
                        "noConnection",
                        "chooseAvatar",
                        "waitForSetAvatarResponse",
                        "shutdown",
                    ],
                ),
                State(
                    "waitForDeleteAvatarResponse",
                    self.enterWaitForDeleteAvatarResponse,
                    self.exitWaitForDeleteAvatarResponse,
                    [
                        "noConnection",
                        "chooseAvatar",
                        "shutdown",
                    ],
                ),
                State(
                    "rejectRemoveAvatar",
                    self.enterRejectRemoveAvatar,
                    self.exitRejectRemoveAvatar,
                    [
                        "noConnection",
                        "chooseAvatar",
                        "shutdown",
                    ],
                ),
                State(
                    "waitForSetAvatarResponse",
                    self.enterWaitForSetAvatarResponse,
                    self.exitWaitForSetAvatarResponse,
                    [
                        "noConnection",
                        "playingGame",
                        "shutdown",
                    ],
                ),
                State(
                    "playingGame",
                    self.enterPlayingGame,
                    self.exitPlayingGame,
                    [
                        "noConnection",
                        "waitForAvatarList",
                        "login",
                        "shutdown",
                        "afkTimeout",
                        "noShards",
                    ],
                ),
            ],
            "loginOff",
            "loginOff",
        )

        self.gameFSM = ClassicFSM(
            "gameFSM",
            [
                State("gameOff", self.enterGameOff, self.exitGameOff, ["waitOnEnterResponses"]),
                State(
                    "waitOnEnterResponses",
                    self.enterWaitOnEnterResponses,
                    self.exitWaitOnEnterResponses,
                    ["playGame", "gameOff"],
                ),
                State("playGame", self.enterPlayGame, self.exitPlayGame, ["gameOff", "closeShard", "switchShards"]),
                State(
                    "switchShards", self.enterSwitchShards, self.exitSwitchShards, ["gameOff", "waitOnEnterResponses"]
                ),
                State("closeShard", self.enterCloseShard, self.exitCloseShard, ["gameOff", "waitOnEnterResponses"]),
            ],
            "gameOff",
            "gameOff",
        )

        self.loginFSM.getStateNamed("playingGame").addChild(self.gameFSM)

        self.loginFSM.enterInitialState()
        self.gameDoneEvent = "playGameDone"
        self.playGame = playGame(self.gameFSM, self.gameDoneEvent)
        self.shardInterestHandle = None
        self.uberZoneInterest = None

        self.astronLoginManager = self.generateGlobalObject(OTP_DO_ID_ASTRON_LOGIN_MANAGER, "AstronLoginManager")
        self.chatRouter = self.generateGlobalObject(OTP_DO_ID_CHAT_ROUTER, "ChatRouter")

    def readDCFileContents(self, dcFile):
        dcFile.readAll()

    def readDCFile(self, dcFileNames=None):
        dcFile = self.getDcFile()
        dcFile.clear()
        self.dclassesByName = {}
        self.dclassesByNumber = {}
        self.readDCFileContents(dcFile)

        self.hashVal = ConfigVariableInt("dc-file-hash", 0).value
        for i in range(dcFile.getNumClasses()):
            dclass = dcFile.getClass(i)
            number = dclass.getNumber()
            className = dclass.getName()
            classDef = DCClassImports.dcImports.get(className)
            if classDef is None:
                self.notify.debug(f"No class definition for {className}.")
            else:
                if isinstance(classDef, types.ModuleType):
                    if not hasattr(classDef, className):
                        self.notify.warning(f"Module {className} does not define class {className}.")
                        continue
                    classDef = getattr(classDef, className)
                if not inspect.isclass(classDef):
                    self.notify.error(f"Symbol {className} is not a class name.")
                else:
                    dclass.setClassDef(classDef)
            self.dclassesByName[className] = dclass
            if number >= 0:
                self.dclassesByNumber[number] = dclass

    def getGameDoId(self):
        return self.GameGlobalsId

    def enterLoginOff(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = self.handleMessageType
        self.shardInterestHandle = None

    def exitLoginOff(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None

    def getServerVersion(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        return self.serverVersion

    def enterConnect(self, serverList):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.serverList = serverList

        self.connectingBox = TTGlobalDialog(message=TTLocalizer.CRConnecting)
        self.connectingBox.show()
        self.renderFrame()

        self.handler = self.handleMessageType

        self.connect(self.serverList, successCallback=self.gotoFirstScreen, failureCallback=self.failedToConnect)

    def failedToConnect(self, statusCode, statusString):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.loginFSM.request("failedToConnect", [statusCode, statusString])

    def exitConnect(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.connectingBox.cleanup()
        del self.connectingBox

    def handleSystemMessage(self, di):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        message = ClientRepositoryBase.handleSystemMessage(self, di)

        whisper = WhisperPopup(message, getInterfaceFont(), WhisperPopup.WTSystem)
        whisper.manage(base.marginManager)

        if not self.systemMessageSfx:
            self.systemMessageSfx = base.loader.loadSfx("phase_3.5/audio/sfx/GUI_whisper_3.ogg")

        if self.systemMessageSfx:
            base.playSfx(self.systemMessageSfx)

    def gotoFirstScreen(self):
        self.startReaderPollTask()
        self.loginFSM.request("login")

    def enterLogin(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.sendSetAvatarIdMsg(0)

        self.handler = self.handleLoginMessageType
        datagram = PyDatagram()
        datagram.addUint16(MsgName2Id["CLIENT_HELLO"])
        datagram.addUint32(self.hashVal)
        datagram.addString(self.serverVersion)
        self.waitForDatabaseTimeout(requestName="WaitForLoginResponse")
        self.send(datagram)

    def handleLoginMessageType(self, msgType, di):
        if msgType == MsgName2Id["CLIENT_HELLO_RESP"]:
            self.startHeartbeat()
            self.astronLoginManager.handleRequestLogin()
        else:
            self.handleMessageType(msgType, di)

    def exitLogin(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None

    def enterFailedToConnect(self, statusCode, statusString):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = self.handleMessageType
        messenger.send("connectionIssue")
        url = self.serverList[0]
        self.notify.warning(f"Failed to connect to {url} ({statusCode} {statusString}).  Notifying user.")

        if statusCode in (1400, 1403, 1405):
            message = TTLocalizer.CRNoConnectProxyNoPort % (url.getServer(), url.getPort(), url.getPort())
            style = OTPDialog.CancelOnly
        else:
            message = TTLocalizer.CRNoConnectTryAgain % (url.getServer(), url.getPort())
            style = OTPDialog.TwoChoice

        self.failedToConnectBox = TTGlobalDialog(
            message=message, doneEvent="failedToConnectAck", text_wordwrap=18, style=style
        )
        self.failedToConnectBox.show()

        self.notify.info(message)

        self.accept("failedToConnectAck", self.__handleFailedToConnectAck)

    def __handleFailedToConnectAck(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        doneStatus = self.failedToConnectBox.doneStatus
        if doneStatus == "ok":
            self.loginFSM.request("connect", [self.serverList])
            messenger.send("connectionRetrying")
        elif doneStatus == "cancel":
            self.loginFSM.request("shutdown")
        else:
            self.notify.error("Unrecognized doneStatus: " + str(doneStatus))

    def exitFailedToConnect(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None
        self.ignore("failedToConnectAck")
        self.failedToConnectBox.cleanup()
        del self.failedToConnectBox

    def enterShutdown(self, errorCode=None):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = self.handleMessageType
        self.sendDisconnect()
        self.notify.info("Exiting cleanly")

    def exitShutdown(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None

    def enterWaitForGameList(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.addInterest(self.GameGlobalsId, OTP_ZONE_ID_MANAGEMENT, "game directory", "GameList_Complete")
        self.acceptOnce("GameList_Complete", self.waitForGetGameListResponse)

    def waitForGetGameListResponse(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        if self.isGameListCorrect():
            self.loginFSM.request("waitForShardList")
        else:
            self.loginFSM.request("missingGameRootObject")

    def isGameListCorrect(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        return 1

    def exitWaitForGameList(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None

    def enterMissingGameRootObject(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.notify.warning("missing some game root objects.")
        self.handler = self.handleMessageType
        self.missingGameRootObjectBox = TTGlobalDialog(
            message=TTLocalizer.CRMissingGameRootObject,
            doneEvent="missingGameRootObjectBoxAck",
            style=OTPDialog.TwoChoice,
        )
        self.missingGameRootObjectBox.show()
        self.accept("missingGameRootObjectBoxAck", self.__handleMissingGameRootObjectAck)

    def __handleMissingGameRootObjectAck(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        doneStatus = self.missingGameRootObjectBox.doneStatus
        if doneStatus == "ok":
            self.loginFSM.request("waitForGameList")
        elif doneStatus == "cancel":
            self.loginFSM.request("shutdown")
        else:
            self.notify.error("Unrecognized doneStatus: " + str(doneStatus))

    def exitMissingGameRootObject(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None
        self.ignore("missingGameRootObjectBoxAck")
        self.missingGameRootObjectBox.cleanup()
        del self.missingGameRootObjectBox

    def enterWaitForShardList(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        if not self.isValidInterestHandle(self.shardInterestHandle):
            self.shardInterestHandle = self.addInterest(
                self.GameGlobalsId, OTP_ZONE_ID_DISTRICTS, "LocalShardList", "ShardList_Complete"
            )
            self.acceptOnce("ShardList_Complete", self._wantShardListComplete)
        else:
            self._wantShardListComplete()

    def exitWaitForShardList(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.ignore("ShardList_Complete")
        self.handler = None

    def _shardsAreReady(self):
        return any(shard.available for shard in list(self.activeDistrictMap.values()))

    def _wantShardListComplete(self):
        if self._shardsAreReady():
            self.loginFSM.request("waitForAvatarList")
        else:
            self.loginFSM.request("noShards")

    def enterNoShards(self):
        messenger.send("connectionIssue")
        self.handler = self.handleMessageType
        self.noShardsBox = TTGlobalDialog(
            message=TTLocalizer.CRNoDistrictsTryAgain, doneEvent="noShardsAck", style=OTPDialog.TwoChoice
        )
        self.noShardsBox.show()
        self.accept("noShardsAck", self.__handleNoShardsAck)

    def __handleNoShardsAck(self):
        doneStatus = self.noShardsBox.doneStatus
        if doneStatus == "ok":
            messenger.send("connectionRetrying")
            self.loginFSM.request("noShardsWait")
        elif doneStatus == "cancel":
            self.loginFSM.request("shutdown")
        else:
            self.notify.error("Unrecognized doneStatus: " + str(doneStatus))

    def exitNoShards(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None
        self.ignore("noShardsAck")
        self.noShardsBox.cleanup()
        del self.noShardsBox

    def enterNoShardsWait(self):
        self.connectingBox = TTGlobalDialog(message=TTLocalizer.CRConnecting)
        self.connectingBox.show()
        self.renderFrame()

        def doneWait(task):
            self.loginFSM.request("waitForShardList")

        delay = 3.5 + random.random() * 2.0
        taskMgr.doMethodLater(delay, doneWait, "noShardsWait")

    def exitNoShardsWait(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        taskMgr.remove("noShardsWait")
        self.connectingBox.cleanup()
        del self.connectingBox

    def enterReject(self):
        self.handler = self.handleMessageType

        self.notify.warning("Connection Rejected")
        sys.exit()

    def exitReject(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None

    def enterNoConnection(self):
        messenger.send("connectionIssue")
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")

        self.resetInterestStateForConnectionLoss()
        self.shardInterestHandle = None

        self.handler = self.handleMessageType

        self.__currentAvId = 0

        self.stopHeartbeat()

        self.stopReaderPollTask()

        if self.bootedText is not None:
            message = TTLocalizer.CRBootedReasonUnknownCode % self.bootedIndex

        else:
            message = TTLocalizer.CRLostConnection

        self.lostConnectionBox = TTGlobalDialog(
            doneEvent="lostConnectionAck", message=message, text_wordwrap=18, style=OTPDialog.Acknowledge
        )
        self.lostConnectionBox.show()
        self.accept("lostConnectionAck", self.__handleLostConnectionAck)

        self.notify.warning("Lost connection to server. Notifying user.")

    def __handleLostConnectionAck(self):
        self.loginFSM.request("shutdown")

    def exitNoConnection(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None
        self.ignore("lostConnectionAck")
        self.lostConnectionBox.cleanup()
        messenger.send("connectionRetrying")

    def enterAfkTimeout(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.sendSetAvatarIdMsg(0)
        msg = TTLocalizer.AfkForceAcknowledgeMessage
        messenger.send("drp.overwrite", ["sleep"])
        self.afkDialog = TTDialog(text=msg, command=self.__handleAfkOk, style=OTPDialog.Acknowledge)
        self.handler = self.handleMessageType

    def __handleAfkOk(self, value):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.loginFSM.request("waitForAvatarList")

    def exitAfkTimeout(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        if self.afkDialog:
            self.afkDialog.cleanup()
            self.afkDialog = None
        self.handler = None
        messenger.send("drp.refresh")

    def __handlePeriodOk(self, value):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        base.exitShow()

    def enterWaitForAvatarList(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self._requestAvatarList()

    def _requestAvatarList(self):
        self.cleanupWaitingForDatabase()
        self.sendGetAvatarsMsg()
        self.waitForDatabaseTimeout(requestName="WaitForAvatarList")

    def sendGetAvatarsMsg(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.astronLoginManager.sendRequestAvatarList()

    def exitWaitForAvatarList(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.cleanupWaitingForDatabase()
        self.handler = None

    def handleAvatarListResponse(self, avatarList):
        avList = []
        for avNum, avName, avDNA, avPosition in avatarList:
            potAv = PotentialAvatar(avNum, avName, avDNA, avPosition)
            avList.append(potAv)

        self.avList = avList
        self.loginFSM.request("chooseAvatar", [self.avList])

    def enterChooseAvatar(self, avList):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        pass

    def exitChooseAvatar(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        pass

    def enterCreateAvatar(self, avList, index, newDNA=None):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        pass

    def exitCreateAvatar(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        pass

    def sendCreateAvatarMsg(self, avDNA, avName, avPosition):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.astronLoginManager.sendCreateAvatar(avDNA, avName, avPosition)

    def enterWaitForDeleteAvatarResponse(self, potAv):
        self.astronLoginManager.sendRequestRemoveAvatar(potAv.id)
        self.waitForDatabaseTimeout(requestName="WaitForDeleteAvatarResponse")

    def sendDeleteAvatarMsg(self, avId):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        datagram = PyDatagram()
        datagram.addUint16(MsgName2Id["CLIENT_DELETE_AVATAR"])
        datagram.addUint32(avId)
        self.send(datagram)

    def exitWaitForDeleteAvatarResponse(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.cleanupWaitingForDatabase()
        self.handler = None

    def enterRejectRemoveAvatar(self, reasonCode):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.notify.warning(f"Rejected removed avatar. ({reasonCode})")
        self.handler = self.handleMessageType
        self.rejectRemoveAvatarBox = TTGlobalDialog(
            message=f"{TTLocalizer.CRRejectRemoveAvatar}\n({reasonCode})",
            doneEvent="rejectRemoveAvatarAck",
            style=OTPDialog.Acknowledge,
        )
        self.rejectRemoveAvatarBox.show()
        self.accept("rejectRemoveAvatarAck", self.__handleRejectRemoveAvatar)

    def __handleRejectRemoveAvatar(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.loginFSM.request("chooseAvatar")

    def exitRejectRemoveAvatar(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None
        self.ignore("rejectRemoveAvatarAck")
        self.rejectRemoveAvatarBox.cleanup()
        del self.rejectRemoveAvatarBox

    def enterWaitForSetAvatarResponse(self, potAv):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.sendSetAvatarMsg(potAv)
        self.waitForDatabaseTimeout(requestName="WaitForSetAvatarResponse")

    def exitWaitForSetAvatarResponse(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.cleanupWaitingForDatabase()
        self.handler = None

    def sendSetAvatarMsg(self, potAv):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.sendSetAvatarIdMsg(potAv.id)

    def sendSetAvatarIdMsg(self, avId):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        if avId != self.__currentAvId:
            self.__currentAvId = avId
            self.astronLoginManager.sendRequestPlayAvatar(avId)

    def handleAvatarResponseMsg(self, di):
        pass

    def enterPlayingGame(self):
        pass

    def exitPlayingGame(self):
        self.notify.info("sending clientLogout")
        messenger.send("clientLogout")

    def _abandonShard(self):
        self.notify.error(f"{self.__class__.__name__} must override _abandonShard")

    def enterGameOff(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.uberZoneInterest = None
        if not hasattr(self, "cleanGameExit"):
            self.cleanGameExit = True

        if self.cleanGameExit is not False:
            if self.isShardInterestOpen():
                self.notify.error("enterGameOff: shard interest is still open")
            assert self.cache.isEmpty()
        elif self.isShardInterestOpen():
            self.notify.warning("unclean exit, abandoning shard")
            self._abandonShard()

        self.cleanupWaitAllInterestsComplete()

        self.cleanGameExit = None

        self.cache.flush()
        self.doDataCache.flush()

        self.handler = self.handleMessageType

    def exitGameOff(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.handler = None

    def enterWaitOnEnterResponses(self, requestStatus):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.cleanGameExit = False
        self.handlerArgs = requestStatus
        if (shardId := requestStatus.get("shardId")) is not None:
            district = self.activeDistrictMap.get(shardId)
        else:
            district = None
        if not district:
            self.distributedDistrict = self.getStartingDistrict()
            if self.distributedDistrict is None:
                self.loginFSM.request("noShards")
                return
            shardId = self.distributedDistrict.doId
        else:
            self.distributedDistrict = district

        self.notify.info(f"Entering shard {shardId}")
        base.localAvatar.setLocation(shardId, requestStatus["zoneId"])

        base.localAvatar.defaultShard = shardId
        self.waitForDatabaseTimeout(requestName="WaitOnEnterResponses")

        self.handleSetShardComplete()

    def handleSetShardComplete(self):
        self.cleanupWaitingForDatabase()

        self.uberZoneInterest = self.addInterest(
            base.localAvatar.defaultShard, OTP_ZONE_ID_MANAGEMENT, "uberZone", "uberZoneInterestComplete"
        )
        self.acceptOnce("uberZoneInterestComplete", self.uberZoneInterestComplete)
        self.waitForDatabaseTimeout(20, requestName="waitingForUberZone")

    def uberZoneInterestComplete(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.cleanupWaitingForDatabase()

        if self.timeManager is None:
            self.notify.warning("TimeManager is not present.")
            DistributedSmoothNode.globalActivateSmoothing(0, 0)
            self.gotTimeSync()
        else:
            DistributedSmoothNode.globalActivateSmoothing(1, 0)

            h = HashVal()
            hashPrcVariables(h)
            self.timeManager.d_setSignature(h.asBin())

            if self.timeManager.synchronize("startup"):
                self.accept("gotTimeSync", self.gotTimeSync)
                self.waitForDatabaseTimeout(requestName="uberZoneInterest-timeSync")
            else:
                self.notify.info("No sync from TimeManager.")
                self.gotTimeSync()

    def exitWaitOnEnterResponses(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.ignore("uberZoneInterestComplete")
        self.cleanupWaitingForDatabase()
        self.handler = None
        self.handlerArgs = None

    def enterCloseShard(self, loginState=None):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.notify.info("Exiting shard")
        self.setNoNewInterests(True)
        self.handler = self.handleCloseShard
        self.sendSetAvatarIdMsg(0)
        self._removeAllOV()
        callback = Functor(self.loginFSM.request, loginState or "waitForAvatarList")
        if base.slowCloseShard:
            taskMgr.doMethodLater(
                base.slowCloseShardDelay * 0.5, Functor(self.removeShardInterest, callback), "slowCloseShard"
            )
        else:
            self.removeShardInterest(callback)

    def _removeAllOV(self):
        ownerDoIds = list(self.doId2ownerView.keys())
        for doId in ownerDoIds:
            self.disableDoId(doId, ownerView=True)

    def isShardInterestOpen(self):
        self.notify.error(f"{self.__class__.__name__} must override isShardInterestOpen")

    def removeShardInterest(self, callback, task=None, *args):
        self._removeCurrentShardInterest(Functor(self._removeShardInterestComplete, callback, args))

    def _removeShardInterestComplete(self, callback, args):
        self.cleanGameExit = True
        self.cache.flush()
        self.doDataCache.flush()
        if base.slowCloseShard:
            taskMgr.doMethodLater(
                base.slowCloseShardDelay * 0.5,
                Functor(self._callRemoveShardInterestCallback, callback, args),
                "slowCloseShardCallback",
            )
        else:
            self._callRemoveShardInterestCallback(callback, None, args)

    @staticmethod
    def _callRemoveShardInterestCallback(callback, task, args=None):
        callback(*args)
        return Task.done

    def _removeCurrentShardInterest(self, callback):
        self.notify.error(f"{self.__class__.__name__} must override _removeCurrentShardInterest")

    def exitCloseShard(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.setNoNewInterests(False)

    def enterPlayGame(self, requestStatus):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")

        self.handler = self.handlePlayGame

        self.accept(self.gameDoneEvent, self.handleGameDone)
        base.transitions.noFade()

        self.playGame.load()
        self.playGame.enter(requestStatus)

        def checkScale(task):
            if not base.localAvatar.getTransform().hasUniformScale():
                raise ValueError("Expected uniform scale, got %s" % base.localAvatar.getTransform().getScale())
            return task.again

        taskMgr.doMethodLater(0.5, checkScale, "globalScaleCheck")

    def handleGameDone(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")

        if self.timeManager:
            self.timeManager.setDisconnectReason(DisconnectSwitchShards)

        doneStatus = self.playGame.getDoneStatus()
        how = doneStatus["how"]
        shardId = doneStatus.get("shardId", None)
        avId = doneStatus["avId"]

        if how == "teleport":
            self.gameFSM.request("switchShards", [shardId, avId])
        else:
            self.notify.error(f"Exited shard with unexpected mode {how}")

    def exitPlayGame(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        taskMgr.remove("globalScaleCheck")

        self.handler = None
        self.playGame.exit()
        self.playGame.unload()

        self.ignore(self.gameDoneEvent)

    def gotTimeSync(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.notify.info("gotTimeSync")
        self.ignore("gotTimeSync")
        self.moveOnFromUberZone()

    def moveOnFromUberZone(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.gameFSM.request("playGame", [self.handlerArgs])

    def handlePlayGame(self, msgType, di):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        if self.notify.getDebug():
            self.notify.debug("handle play game got message type: " + repr(msgType))
        if msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED"]:
            self.handleGenerateWithRequired(di)
        elif msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED_OTHER"]:
            self.handleGenerateWithRequiredOther(di)
        elif msgType == MsgName2Id["CLIENT_OBJECT_SET_FIELD"]:
            self.handleUpdateField(di)
        elif msgType == DisneyMessageTypes.CLIENT_OBJECT_DISABLE_RESP:
            self.handleDisable(di)
        elif msgType == DisneyMessageTypes.CLIENT_OBJECT_DELETE_RESP:
            self.handleDelete(di)
        else:
            self.handleMessageType(msgType, di)

    def enterSwitchShards(self, shardId, avId):
        base.localAvatar.setLeftDistrict()
        messenger.send("drp.setDistrict", [base.cr.activeDistrictMap[shardId].name])
        requestStatus = dict(shardId=shardId, avId=avId)

        self.removeShardInterest(self._handleOldShardGone, [requestStatus])

    def _handleOldShardGone(self, params):
        self.gameFSM.request("waitOnEnterResponses", params)

    def exitSwitchShards(self):
        pass

    def getStartingDistrict(self):
        """
        Get a Proper District For a starting location
        None if no District in core
        """
        district = None

        availableDistricts = [district for district in self.activeDistrictMap.values() if district.available]
        if len(availableDistricts) == 0:
            self.notify.info("no shards")
            return None

        presetDistrict = os.getenv("DISTRICT_OVERRIDE", "")
        if presetDistrict:
            presetDistrictList = [district for district in availableDistricts if district.name == presetDistrict]
            if presetDistrictList:
                district = presetDistrictList[0]

        if district is None:
            district = min(availableDistricts, key=lambda x: x.avatarCount)

        messenger.send("drp.setDistrict", [district.name])
        return district

    def getShardName(self, shardId):
        """
        Returns the name associated with the indicated shard ID, or
        None if the shard is unknown.
        """
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        try:
            return self.activeDistrictMap[shardId].name
        except KeyError:
            return None

    def listActiveShards(self):
        """
        Returns a list of tuples, such that each element of the list
        is a tuple of the form (shardId, name, population) for all the shards believed to be
        currently up and running, and accepting avatars.
        """
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        shardList = []
        for s in list(self.activeDistrictMap.values()):
            if s.available:
                shardList.append((s.doId, s.name, s.avatarCount))

        return shardList

    def queryObjectField(self, dclassName, fieldName, doId, context=0):
        assert self.notify.debugStateCall(self)
        assert len(dclassName) > 0
        assert len(fieldName) > 0
        assert doId > 0
        dclass = self.dclassesByName.get(dclassName)
        assert dclass is not None
        if dclass is not None:
            fieldId = dclass.getFieldByName(fieldName).getNumber()
            assert fieldId
            self.queryObjectFieldId(doId, fieldId, context)

    def lostConnection(self):
        ClientRepositoryBase.lostConnection(self)
        self.loginFSM.request("noConnection")

    def waitForDatabaseTimeout(self, extraTimeout=0, requestName="unknown"):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        assert self.waitingForDatabase is None
        OTPClientRepository.notify.debug(f"waiting for database timeout {requestName} at {globalClock.getFrameTime()}")
        taskMgr.remove("waitingForDatabase")
        globalClock.tick()
        taskMgr.doMethodLater(
            (20 + extraTimeout),
            self.__showWaitingForDatabase,
            "waitingForDatabase",
            extraArgs=[requestName],
        )

    def __showWaitingForDatabase(self, requestName):
        messenger.send("connectionIssue")
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        OTPClientRepository.notify.info(f"timed out waiting for {requestName} at {globalClock.getFrameTime()}")
        self.waitingForDatabase = TTDialog(
            text=TTLocalizer.CRToontownUnavailable,
            dialogName="WaitingForDatabase",
            buttonTextList=["Cancel"],
            style=OTPDialog.CancelOnly,
            command=self.__handleCancelWaiting,
        )
        self.waitingForDatabase.show()
        taskMgr.remove("waitingForDatabase")
        taskMgr.doMethodLater(
            45,
            self.__giveUpWaitingForDatabase,
            "waitingForDatabase",
            extraArgs=[requestName],
        )
        return Task.done

    def __giveUpWaitingForDatabase(self, requestName):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        OTPClientRepository.notify.info(f"giving up waiting for {requestName} at {globalClock.getFrameTime()}")
        self.cleanupWaitingForDatabase()
        self.loginFSM.request("noConnection")
        return Task.done

    def cleanupWaitingForDatabase(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        if self.waitingForDatabase is not None:
            self.waitingForDatabase.hide()
            self.waitingForDatabase.cleanup()
            self.waitingForDatabase = None
        taskMgr.remove("waitingForDatabase")

    def __handleCancelWaiting(self, value):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.loginFSM.request("shutdown")

    def renderFrame(self):
        """
        force a frame render; this is useful for screen transitions,
        where we destroy one screen and load the next; during the load,
        we don't want the user staring at the old screen
        """
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")

        gsg = base.win.getGsg()
        if gsg:
            render2d.prepareScene(gsg)

        base.graphicsEngine.renderFrame()

    def handleMessageType(self, msgType, di):
        if msgType == MsgName2Id["CLIENT_EJECT"]:
            self.handleGoGetLost(di)
        elif msgType == MsgName2Id["CLIENT_HEARTBEAT"]:
            self.handleServerHeartbeat(di)
        elif msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED"]:
            self.handleGenerateWithRequired(di)
        elif msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED_OTHER"]:
            self.handleGenerateWithRequiredOther(di)
        elif msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED_OTHER_OWNER"]:
            self.handleGenerateWithRequiredOtherOwner(di)
        elif msgType == MsgName2Id["CLIENT_OBJECT_SET_FIELD"]:
            self.handleUpdateField(di)
        elif msgType in (DisneyMessageTypes.CLIENT_OBJECT_DISABLE, MsgName2Id["CLIENT_OBJECT_LEAVING"]):
            self.handleDisable(di)
        elif msgType in (DisneyMessageTypes.CLIENT_OBJECT_DISABLE_OWNER, MsgName2Id["CLIENT_OBJECT_LEAVING_OWNER"]):
            self.handleDisable(di, ownerView=True)
        elif msgType == DisneyMessageTypes.CLIENT_OBJECT_DELETE_RESP:
            self.handleDelete(di)
        elif msgType == MsgName2Id["CLIENT_DONE_INTEREST_RESP"]:
            self.gotInterestDoneMessage(di)
        elif msgType == MsgName2Id["CLIENT_OBJECT_LOCATION"]:
            self.gotObjectLocationMessage(di)
        else:
            currentLoginState = self.loginFSM.getCurrentState()
            currentLoginStateName = currentLoginState.getName() if currentLoginState else "None"
            currentGameState = self.gameFSM.getCurrentState()
            currentGameStateName = currentGameState.getName() if currentGameState else "None"
            ClientRepositoryBase.notify.warning(
                "Ignoring unexpected message type: "
                + str(msgType)
                + " login state: "
                + currentLoginStateName
                + " game state: "
                + currentGameStateName
            )

    def gotInterestDoneMessage(self, di):
        if self.deferredGenerates:
            dg = Datagram(di.getDatagram())
            di = DatagramIterator(dg, di.getCurrentIndex())

            self.deferredGenerates.append((MsgName2Id["CLIENT_DONE_INTEREST_RESP"], (dg, di)))

        else:
            self.handleInterestDoneMessage(di)

    def gotObjectLocationMessage(self, di):
        if self.deferredGenerates:
            dg = Datagram(di.getDatagram())
            di = DatagramIterator(dg, di.getCurrentIndex())
            di2 = DatagramIterator(dg, di.getCurrentIndex())
            doId = di2.getUint32()
            if doId in self.deferredDoIds:
                self.deferredDoIds[doId][3].append((MsgName2Id["CLIENT_OBJECT_LOCATION"], (dg, di)))
            else:
                self.handleObjectLocation(di)
        else:
            self.handleObjectLocation(di)

    def replayDeferredGenerate(self, msgType, extra):
        """Override this to do something appropriate with deferred
        "generate" messages when they are replayed()."""

        if msgType == MsgName2Id["CLIENT_DONE_INTEREST_RESP"]:
            dg, di = extra
            self.handleInterestDoneMessage(di)
        elif msgType == MsgName2Id["CLIENT_OBJECT_LOCATION"]:
            dg, di = extra
            self.handleObjectLocation(di)
        else:
            ClientRepositoryBase.replayDeferredGenerate(self, msgType, extra)

    def handleDatagram(self, di):
        if self.notify.getDebug():
            self.notify.debug("ClientRepository received datagram:")
            di.getDatagram().dumpHex(Notify.out())

        msgType = self.getMsgType()
        if msgType == 65535:
            self.lostConnection()
            return

        if self.handler is None:
            self.handleMessageType(msgType, di)
        else:
            self.handler(msgType, di)

        self.considerHeartbeat()

    def askAvatarKnown(self, avId):
        return 0

    def identifyAvatar(self, doId):
        """
        Returns either an avatar, FriendInfo,
        whichever we can find, to reference the indicated avatar doId.
        """
        return self.doId2do.get(doId)

    def sendDisconnect(self):
        if self.isConnected():
            datagram = PyDatagram()
            datagram.addUint16(MsgName2Id["CLIENT_DISCONNECT"])
            self.send(datagram)
            self.notify.info("Sent disconnect message to server")
            self.disconnect()
        self.stopHeartbeat()

    def _isPlayerDclass(self, dclass):
        return False

    def isValidPlayerLocation(self, parentId, zoneId):
        return True

    def _isInvalidPlayerAvatarGenerate(self, doId, dclass, parentId, zoneId):
        if self._isPlayerDclass(dclass) and not self.isValidPlayerLocation(parentId, zoneId):
            return True
        return False

    def handleGenerateWithRequired(self, di):
        doId = di.getUint32()
        parentId = di.getUint32()
        zoneId = di.getUint32()
        assert parentId == self.GameGlobalsId or parentId in self.doId2do
        classId = di.getUint16()
        dclass = self.dclassesByNumber[classId]

        if self._isInvalidPlayerAvatarGenerate(doId, dclass, parentId, zoneId):
            return

        dclass.startGenerate()
        self.generateWithRequiredFields(dclass, doId, di, parentId, zoneId)
        dclass.stopGenerate()

    def handleGenerateWithRequiredOther(self, di):
        doId = di.getUint32()
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()

        dclass = self.dclassesByNumber[classId]

        if self._isInvalidPlayerAvatarGenerate(doId, dclass, parentId, zoneId):
            return

        deferrable = getattr(dclass.getClassDef(), "deferrable", False)
        if not self.deferInterval or self.noDefer:
            deferrable = False

        now = globalClock.getFrameTime()
        if self.deferredGenerates or deferrable:
            if self.deferredGenerates or now - self.lastGenerate < self.deferInterval:
                assert self.notify.debug(f"deferring generate for {dclass.getName()} {doId}")
                self.deferredGenerates.append((MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED_OTHER"], doId))

                dg = Datagram(di.getDatagram())
                di = DatagramIterator(dg, di.getCurrentIndex())

                self.deferredDoIds[doId] = ((parentId, zoneId, classId, doId, di), deferrable, dg, [])
                if len(self.deferredGenerates) == 1:
                    taskMgr.remove("deferredGenerate")
                    taskMgr.doMethodLater(self.deferInterval, self.doDeferredGenerate, "deferredGenerate")

            else:
                self.lastGenerate = now
                self.doGenerate(parentId, zoneId, classId, doId, di)

        else:
            self.doGenerate(parentId, zoneId, classId, doId, di)

    def handleGenerateWithRequiredOtherOwner(self, di):
        doId = di.getUint32()
        di.getUint32()
        di.getUint32()
        classId = di.getUint16()
        dclass = self.dclassesByNumber[classId]
        dclass.startGenerate()
        self.generateWithRequiredOtherFieldsOwner(dclass, doId, di)
        dclass.stopGenerate()

    def handleQuietZoneGenerateWithRequired(self, di):
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        doId = di.getUint32()
        dclass = self.dclassesByNumber[classId]
        dclass.startGenerate()
        self.generateWithRequiredFields(dclass, doId, di, parentId, zoneId)
        dclass.stopGenerate()

    def handleQuietZoneGenerateWithRequiredOther(self, di):
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        doId = di.getUint32()
        dclass = self.dclassesByNumber[classId]
        dclass.startGenerate()
        self.generateWithRequiredOtherFields(dclass, doId, di, parentId, zoneId)
        dclass.stopGenerate()

    def handleDisable(self, di, ownerView=False):
        doId = di.getUint32()
        if not self.isLocalId(doId):
            self.disableDoId(doId, ownerView)

    def sendSetLocation(self, doId, parentId, zoneId):
        datagram = PyDatagram()
        datagram.addUint16(MsgName2Id["CLIENT_OBJECT_LOCATION"])
        datagram.addUint32(doId)
        datagram.addUint32(parentId)
        datagram.addUint32(zoneId)
        self.send(datagram)

    def sendHeartbeat(self):
        datagram = PyDatagram()
        datagram.addUint16(MsgName2Id["CLIENT_HEARTBEAT"])
        self.send(datagram)
        self.lastHeartbeat = globalClock.getRealTime()
        self.considerFlush()

    def isLocalId(self, doId):
        return base.localAvatar and base.localAvatar.doId == doId

    def callbackWithDo(self, doId, callback):
        if isinstance(doId, int):
            doId = [doId]

        if all(do in self.doId2do for do in doId):
            callback([self.doId2do[do] for do in doId])
        else:
            self.relatedObjectMgr.requestObjects(doId, allCallback=callback)
