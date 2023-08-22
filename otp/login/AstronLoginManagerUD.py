import json
import time
from datetime import datetime, timezone

from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.MsgTypes import MsgName2Id
from direct.distributed.PyDatagram import PyDatagram
from direct.fsm.FSM import FSM

from otp.login.AccountDatabases import DeveloperAccountDB
from toontown.makeatoon.NameGenerator import NameGenerator
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase.globals.TTGlobalsChat import DefaultEmotes
from toontown.toonbase.globals.TTGlobalsCore import AccessLevels


class GameOperation(FSM):
    CHOSEN_CONNECTION = False

    def __init__(self, loginManager, sender):
        super().__init__("UDGameOperation")
        self.loginManager = loginManager
        self.sender = sender
        self.callback = None
        FSM.__init__(self, self.__class__.__name__)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterKill(self, reason, errCode=122, warn=True):
        if warn:
            self.loginManager.notify.warning(f"Game operation cancelled: {reason}")
        if self.CHOSEN_CONNECTION:
            self.loginManager.killConnection(self.sender, reason, errCode)
        else:
            self.loginManager.killAccount(self.sender, reason, errCode)
        self._handleDone()

    def exitKill(self):
        pass

    def setCallback(self, callback):
        self.callback = callback

    def _handleDone(self):
        if self.__class__.__name__ == "LoginOperation":
            del self.loginManager.sender2loginOperation[self.sender]
        else:
            del self.loginManager.account2operation[self.sender]


class LoginOperation(GameOperation):
    CHOSEN_CONNECTION = True

    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
        self.playToken = ""
        self.databaseId = 0
        self.accountId = 0
        self.account = None

    def start(self, playToken):
        self.playToken = playToken
        self.loginManager.accountDb.lookup(playToken, self.__handleLookup)

    def __handleLookup(self, result):
        if err := result.get("error", 0):
            self.demand("Kill", result.get("reason", "The database rejected your token."), err or 122, False)
            return

        if not result.get("success"):
            self.demand("Kill", result.get("reason", "The database rejected your token."))
            return

        self.databaseId = result.get("databaseId", 0)
        self.extraData = result.get("extraData")
        accountId = result.get("accountId", 0)
        self.notify.info(f"received account id: {accountId}")
        self.staffAccess = result.get("staffAccess", "USER")
        self.lastLogin = result.get("lastLogin", time.ctime())
        if accountId:
            self.accountId = accountId
            self.__handleRetrieveAccount()
        else:
            self.__handleCreateAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(
            self.loginManager.air.dbId, self.accountId, self.__handleAccountRetrieved
        )

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName["AccountUD"]:
            self.demand("Kill", "Account was not found in the database.")
            return

        self.account = fields
        self.__handleSetAccount()

    def __handleCreateAccount(self):
        self.account = {
            "ACCOUNT_AV_SET": [0] * 6,
            "ESTATE_ID": 0,
            "ACCOUNT_AV_SET_DEL": [],
            "CREATED": time.ctime(),
            "LAST_LOGIN": time.ctime(),
            "ACCOUNT_ID": str(self.databaseId),
            "STAFF_ACCESS": self.staffAccess,
        }

        self.loginManager.air.dbInterface.createObject(
            self.loginManager.air.dbId,
            self.loginManager.air.dclassesByName["AccountUD"],
            self.account,
            self.__handleAccountCreated,
        )

    def __handleAccountCreated(self, accountId):
        if not accountId:
            self.demand("Kill", "Account could not be created.")
            return

        self.accountId = accountId
        self.__storeAccountId()

    def __storeAccountId(self):
        self.loginManager.accountDb.storeAccountId(
            self.databaseId, self.accountId, self.__handleAccountIdStored, self.extraData
        )

    def __handleAccountIdStored(self, success=True):
        if not success:
            self.demand("Kill", "Could not store account id.")
            return

        self.__handleSetAccount()

    def __handleSetAccount(self):
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.loginManager.GetAccountConnectionChannel(self.accountId),
            self.loginManager.air.ourChannel,
            MsgName2Id["CLIENTAGENT_EJECT"],
        )
        datagram.addUint16(100)
        datagram.addString("This account has been logged in elsewhere.")
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(self.sender, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_OPEN_CHANNEL"])
        datagram.addChannel(self.loginManager.GetAccountConnectionChannel(self.accountId))
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(self.sender, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_SET_CLIENT_ID"])
        datagram.addChannel(self.accountId << 32)
        self.loginManager.air.send(datagram)

        self.loginManager.air.setClientState(self.sender, 2)

        responseData = {
            "returnCode": 0,
            "respString": "",
            "accountNumber": self.sender,
            "accountDays": self.getAccountDays(),
            "serverTime": int(time.time()),
            "userName": str(self.databaseId),
        }
        responseBlob = json.dumps(responseData)
        self.loginManager.sendUpdateToChannel(self.sender, "loginResponse", [responseBlob])
        self._handleDone()

    def getAccountCreationDate(self):
        accountCreationDate = self.account.get("CREATED", "")
        try:
            accountCreationDate = datetime.fromtimestamp(
                time.mktime(time.strptime(accountCreationDate)), tz=timezone.utc
            )
        except ValueError:
            accountCreationDate = ""

        return accountCreationDate

    def getAccountDays(self):
        accountCreationDate = self.getAccountCreationDate()
        accountDays = -1
        if accountCreationDate:
            now = datetime.fromtimestamp(time.mktime(time.strptime(time.ctime())), tz=timezone.utc)
            accountDays = abs((now - accountCreationDate).days)

        return accountDays


class AvatarOperation(GameOperation):
    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
        self.account = None
        self.avList = []

    def start(self):
        self.__handleRetrieveAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(
            self.loginManager.air.dbId, self.sender, self.__handleAccountRetrieved
        )

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName["AccountUD"]:
            self.demand("Kill", "Account could not be retrieved.")
            return

        self.account = fields
        self.avList = self.account["ACCOUNT_AV_SET"]

        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))

        if self.callback is not None:
            self.callback()


class GetAvatarsOperation(AvatarOperation):
    def __init__(self, loginManager, sender):
        AvatarOperation.__init__(self, loginManager, sender)
        self.setCallback(self._handleQueryAvatars)
        self.pendingAvatars = None
        self.avatarFields = None
        self.potentialAvatars = []

    def _handleQueryAvatars(self):
        self.pendingAvatars = set()
        self.avatarFields = {}
        for avId in self.avList:
            if avId:
                self.pendingAvatars.add(avId)

                def response(dclass, fields, avId=avId):
                    if dclass != self.loginManager.air.dclassesByName["DistributedToonUD"]:
                        self.demand("Kill", "One of the toons is invalid.")
                        return

                    self.avatarFields[avId] = fields
                    self.pendingAvatars.remove(avId)
                    if not self.pendingAvatars:
                        self.__handleSendAvatars()

                self.loginManager.air.dbInterface.queryObject(self.loginManager.air.dbId, avId, response)

        if not self.pendingAvatars:
            self.__handleSendAvatars()

    def __handleSendAvatars(self):
        self.neededAvatars = len(self.avatarFields) + 1
        for avId, fields in list(self.avatarFields.items()):
            index = self.avList.index(avId)
            name = fields["setName"][0]

            dnaString = fields["setDNAString"][0]
            self.potentialAvatars.append([avId, name, dnaString, index])
            self.__updatedPotentialAvatars()
        self.__updatedPotentialAvatars()

    def __updatedPotentialAvatars(self, *args):
        self.neededAvatars -= 1
        if not self.neededAvatars:
            self.finishOperation()

    def finishOperation(self):
        self.loginManager.sendUpdateToAccountId(self.sender, "avatarListResponse", [self.potentialAvatars])
        self._handleDone()


class CreateAvatarOperation(GameOperation):
    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
        self.avPosition = None
        self.avDNA = None
        self.avName = None

    def start(self, avDNA, avName, avPosition):
        if avPosition >= 6:
            self.demand("Kill", "Can't have position at 6")
            return
        valid = ToonDNA.isValidNetString(avDNA)
        if not valid:
            self.demand("Kill", f"Toon's DNA is not valid (received: {avDNA.hex()}).")
            return

        self.avPosition = avPosition
        self.avDNA = avDNA
        self.avName = avName

        self.__handleRetrieveAccount()

    def __handleRetrieveAccount(self):
        self.loginManager.air.dbInterface.queryObject(
            self.loginManager.air.dbId, self.sender, self.__handleAccountRetrieved
        )

    def __handleAccountRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName["AccountUD"]:
            self.demand("Kill", "Failed to retrieve account.")

            return

        self.account = fields
        self.avList = self.account["ACCOUNT_AV_SET"]
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))
        if self.avList[self.avPosition]:
            self.demand("Kill", "Toon slot is already taken")
            return

        self.__handleCreateAvatar()

    def __handleCreateAvatar(self):
        dna = ToonDNA()
        dna.makeFromNetString(self.avDNA)
        toonFields = {
            "setName": (self.avName,),
            "setDNAString": (self.avDNA,),
            "setDISLid": (self.sender,),
            "setEmoteAccess": (DefaultEmotes,),
        }

        self.loginManager.air.dbInterface.createObject(
            self.loginManager.air.dbId,
            self.loginManager.air.dclassesByName["DistributedToonUD"],
            toonFields,
            self.__handleToonCreated,
        )

    def __handleToonCreated(self, avId):
        if not avId:
            self.demand("Kill", "Failed to create a new toon.")
            return

        self.avId = avId
        self.__handleStoreAvatar()

    def __handleStoreAvatar(self):
        self.avList[self.avPosition] = self.avId
        self.loginManager.air.dbInterface.updateObject(
            self.loginManager.air.dbId,
            self.sender,
            self.loginManager.air.dclassesByName["AccountUD"],
            {"ACCOUNT_AV_SET": self.avList},
            {"ACCOUNT_AV_SET": self.account["ACCOUNT_AV_SET"]},
            self.__handleAvatarStored,
        )

    def __handleAvatarStored(self, fields):
        if fields:
            self.demand("Kill", "Failed to associate new toon to your account!")
            return

        self.loginManager.sendUpdateToAccountId(self.sender, "createAvatarResponse", [self.avId])
        self._handleDone()


class RemoveAvatarOperation(GetAvatarsOperation):
    def __init__(self, loginManager, sender):
        GetAvatarsOperation.__init__(self, loginManager, sender)
        self.setCallback(self.__handleRemoveAvatar)
        self.avId = None

    def start(self, avId):
        self.avId = avId
        GetAvatarsOperation.start(self)

    def __handleRemoveAvatar(self):
        if self.avId not in self.avList:
            self.demand("Kill", "Tried to remove a toon not in the account.")
            return

        index = self.avList.index(self.avId)
        self.avList[index] = 0
        avatarsRemoved = list(self.account.get("ACCOUNT_AV_SET_DEL", []))
        avatarsRemoved.append([self.avId, int(time.time())])
        self.loginManager.air.dbInterface.updateObject(
            self.loginManager.air.dbId,
            self.sender,
            self.loginManager.air.dclassesByName["AccountUD"],
            {"ACCOUNT_AV_SET": self.avList, "ACCOUNT_AV_SET_DEL": avatarsRemoved},
            {
                "ACCOUNT_AV_SET": self.account["ACCOUNT_AV_SET"],
                "ACCOUNT_AV_SET_DEL": self.account["ACCOUNT_AV_SET_DEL"],
            },
            self.__handleAvatarRemoved,
        )

    def __handleAvatarRemoved(self, fields):
        if fields:
            self.demand("Kill", "Database failed to associate the new avatar to your account!")
            return

        self._handleQueryAvatars()


class LoadAvatarOperation(AvatarOperation):
    def __init__(self, loginManager, sender):
        AvatarOperation.__init__(self, loginManager, sender)
        self.setCallback(self.__handleGetTargetAvatar)
        self.avId = None

    def start(self, avId):
        self.avId = avId
        AvatarOperation.start(self)

    def __handleGetTargetAvatar(self):
        if self.avId not in self.avList:
            return

        self.loginManager.air.dbInterface.queryObject(
            self.loginManager.air.dbId, self.avId, self.__handleAvatarRetrieved
        )

    def __handleAvatarRetrieved(self, dclass, fields):
        if dclass != self.loginManager.air.dclassesByName["DistributedToonUD"]:
            return

        self.avatar = fields
        self.__handleSetAvatar()

    def __handleSetAvatar(self):
        channel = self.loginManager.GetAccountConnectionChannel(self.sender)

        cleanupDatagram = PyDatagram()
        cleanupDatagram.addServerHeader(self.avId, channel, MsgName2Id["STATESERVER_OBJECT_DELETE_RAM"])
        cleanupDatagram.addUint32(self.avId)
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_ADD_POST_REMOVE"])
        datagram.addUint16(cleanupDatagram.getLength())
        datagram.appendData(cleanupDatagram.getMessage())
        self.loginManager.air.send(datagram)
        staffAccess = AccessLevels.ADMIN
        self.loginManager.air.sendActivate(
            self.avId,
            0,
            0,
            self.loginManager.air.dclassesByName["DistributedToonUD"],
            {"setStaffAccess": [staffAccess], "bogusField": []},
        )

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_OPEN_CHANNEL"])
        datagram.addChannel(self.loginManager.GetPuppetConnectionChannel(self.avId))
        self.loginManager.air.send(datagram)

        self.loginManager.air.clientAddSessionObject(channel, self.avId)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_SET_CLIENT_ID"])
        datagram.addChannel(self.sender << 32 | self.avId)
        self.loginManager.air.send(datagram)

        self.loginManager.air.setOwner(self.avId, channel)
        self._handleDone()


class UnloadAvatarOperation(GameOperation):
    def __init__(self, loginManager, sender):
        GameOperation.__init__(self, loginManager, sender)
        self.avId = None

    def start(self, avId):
        self.avId = avId
        self.__handleUnloadAvatar()

    def __handleUnloadAvatar(self):
        channel = self.loginManager.GetAccountConnectionChannel(self.sender)
        self.loginManager.air.ttFriendsManager.friendOffline(self.avId)
        datagram = PyDatagram()
        datagram.addServerHeader(
            channel, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_CLEAR_POST_REMOVES"]
        )
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_CLOSE_CHANNEL"])
        datagram.addChannel(self.loginManager.GetPuppetConnectionChannel(self.avId))
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_SET_CLIENT_ID"])
        datagram.addChannel(self.sender << 32)
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(
            channel, self.loginManager.air.ourChannel, MsgName2Id["CLIENTAGENT_REMOVE_SESSION_OBJECT"]
        )
        datagram.addUint32(self.avId)
        self.loginManager.air.send(datagram)

        datagram = PyDatagram()
        datagram.addServerHeader(self.avId, channel, MsgName2Id["STATESERVER_OBJECT_DELETE_RAM"])
        datagram.addUint32(self.avId)
        self.loginManager.air.send(datagram)

        self._handleDone()


class AstronLoginManagerUD(DistributedObjectGlobalUD):
    notify = directNotify.newCategory("AstronLoginManagerUD")

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.nameGenerator = None
        self.accountDb = None
        self.sender2loginOperation = {}
        self.account2operation = {}

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)

        self.nameGenerator = NameGenerator()
        self.accountDb = DeveloperAccountDB(self)

    def runLoginOperation(self, playToken):
        sender = self.air.getMsgSender()

        if sender >> 32:
            return

        if sender in list(self.sender2loginOperation.keys()):
            return

        newLoginOperation = LoginOperation(self, sender)
        self.sender2loginOperation[sender] = newLoginOperation
        newLoginOperation.start(playToken)

    def runGameOperation(self, operationType, *args):
        sender = self.air.getAccountIdFromSender()
        if not sender:
            return

        if sender in self.account2operation:
            return

        newOperation = operationType(self, sender)
        self.account2operation[sender] = newOperation
        newOperation.start(*args)

    def requestLogin(self, playToken):
        self.runLoginOperation(playToken)

    def requestAvatarList(self):
        self.runGameOperation(GetAvatarsOperation)

    def createAvatar(self, avDNA, avName, avPosition):
        self.runGameOperation(CreateAvatarOperation, avDNA, avName, avPosition)

    def requestRemoveAvatar(self, avId):
        self.runGameOperation(RemoveAvatarOperation, avId)

    def requestPlayAvatar(self, avId):
        currentAvId = self.air.getAvatarIdFromSender()
        accId = self.air.getAccountIdFromSender()
        if currentAvId and avId:
            self.killAccount(accId, "A Toon is already chosen!")
            return
        if not currentAvId and not avId:
            return

        if avId:
            self.runGameOperation(LoadAvatarOperation, avId)
        else:
            self.runGameOperation(UnloadAvatarOperation, currentAvId)

    def killConnection(self, connectionId, reason, errCode=122):
        dg = PyDatagram()
        dg.addServerHeader(connectionId, self.air.ourChannel, MsgName2Id["CLIENTAGENT_EJECT"])
        dg.addUint16(errCode)
        dg.addString(reason)
        self.air.send(dg)

    def killAccount(self, accId, reason, errCode=122):
        self.killConnection(self.GetAccountConnectionChannel(accId), reason, errCode)

    def giveAdmin(self, accountName):
        self.accountDb.lookup(accountName, self.__handleAdminLookup)

    def __handleAdminLookup(self, account):
        if account is None or not account.get("accountId"):
            return
        self.air.dbInterface.updateObject(
            self.air.dbId,
            account.get("accountId"),
            self.air.dclassesByName["AccountUD"],
            {"STAFF_ACCESS": "SYSTEM ADMIN"},
        )
