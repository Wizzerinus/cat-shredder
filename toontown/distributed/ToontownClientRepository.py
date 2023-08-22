import json
import random
import time
from collections import deque

from direct.distributed.MsgTypes import MsgName2Id
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.interval.IntervalGlobal import ivalMgr
from direct.showbase.PythonUtil import Functor, itype, safeRepr
from panda3d.core import ModelPool, TexturePool
from panda3d.otp import NametagGlobals

from otp.avatar import Avatar
from otp.distributed import OTPClientRepository
from otp.login import AvatarChooser
from otp.uberdog.AccountDetailRecord import AccountDetailRecord
from toontown.distributed import PlayGame
from toontown.makeatoon import MakeAToon
from toontown.toon import LocalToon
from toontown.toon import ToonDNA
from toontown.toon.DistributedToon import DistributedToon
from toontown.toonbase.globals.TTGlobalsCore import *


class ToontownClientRepository(OTPClientRepository.OTPClientRepository):
    """ToontownClientRepository class: handle distribution for client"""

    GameGlobalsId = OTP_DO_ID_TOONTOWN

    SetZoneDoneEvent = "TCRSetZoneDone"
    EmuSetZoneDoneEvent = "TCREmuSetZoneDone"

    SetInterest = "Set"
    ClearInterest = "Clear"

    ClearInterestDoneEvent = "TCRClearInterestDone"

    KeepSubShardObjects = False
    _userLoggingOut = False

    def __init__(self, serverVersion):
        OTPClientRepository.OTPClientRepository.__init__(self, serverVersion, playGame=PlayGame.PlayGame)

        self._playerAvDclass = self.dclassesByName["DistributedToon"]

        self.__forbidCheesyEffects = 0

        self.ttFriendsManager = self.generateGlobalObject(OTP_DO_ID_TT_FRIENDS_MANAGER, "TTFriendsManager")

        self.__queryAvatarMap = {}

        self.setZonesEmulated = 0
        self.old_setzone_interest_handle = None
        self.setZoneQueue = deque()
        self.accept(ToontownClientRepository.SetZoneDoneEvent, self._handleEmuSetZoneDone)

        self._deletedSubShardDoIds = set()

        self.toonNameDict = {}

    def enterChooseAvatar(self, avList):
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

        self.sendSetAvatarIdMsg(0)

        self.handler = self.handleMessageType
        self.avChoiceDoneEvent = "avatarChooserDone"
        self.avChoice = AvatarChooser.AvatarChooser(avList, self.loginFSM, self.avChoiceDoneEvent)
        self.avChoice.load()
        self.avChoice.enter()

        self.accept(self.avChoiceDoneEvent, self.__handleAvatarChooserDone, [avList])

    def __handleAvatarChooserDone(self, avList, doneStatus):
        done = doneStatus["mode"]
        if done == "exit":
            self.loginFSM.request("shutdown")
            return
        index = self.avChoice.getChoice()
        assert (index >= 0) and (index <= self.avatarLimit)
        avs = [avOption for avOption in avList if avOption.position == index]
        if not avs:
            self.avChoice.exit()
            self.loginFSM.request("createAvatar", [avList, index])
            return

        avatarChoice = avs[0]
        self.notify.info("================")
        self.notify.info(f"Chose avatar id: {avatarChoice.id}")
        self.notify.info(f"Chose avatar name: {avatarChoice.avName}")
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(avatarChoice.dna)
        self.notify.info(f"Chose avatar dna: {dna.asTuple()}")
        self.notify.info(f"Chose avatar position: {avatarChoice.position}")
        self.notify.info("================")

        if done == "chose":
            self.avChoice.exit()
            self.loginFSM.request("waitForSetAvatarResponse", [avatarChoice])
        elif done == "create":
            self.loginFSM.request("createAvatar", [avList, index])
        elif done == "delete":
            self.loginFSM.request("waitForDeleteAvatarResponse", [avatarChoice])

    def exitChooseAvatar(self):
        self.handler = None
        self.avChoice.exit()
        self.avChoice.unload()
        self.avChoice = None
        self.ignore(self.avChoiceDoneEvent)

    def enterCreateAvatar(self, avList, index):
        self.avCreate = MakeAToon.MakeAToon(self.loginFSM, avList, "makeAToonComplete", index)
        self.avCreate.load()
        self.avCreate.enter()
        base.transitions.fadeIn()

        self.accept("makeAToonComplete", self.__handleMakeAToon, [avList, index])
        self.accept("createAvatar", self.sendCreateAvatarMsg)
        self.accept("nameShopPost", self.relayMessage)

    def relayMessage(self, dg):
        self.send(dg)

    def __handleMakeAToon(self, avList, avPosition):
        print(avList, avPosition)
        done = self.avCreate.getDoneStatus()

        if done == "cancel":
            if hasattr(self, "newPotAv"):
                if self.newPotAv in avList:
                    avList.remove(self.newPotAv)
            self.avCreate.exit()
            self.loginFSM.request("chooseAvatar", [avList])
        elif done == "created":
            self.avCreate.exit()
            avs = [avOption for avOption in avList if avOption.position == avPosition]
            if not avs:
                self.notify.error(f"Invalid avatar position: {avPosition}")
            self.loginFSM.request("waitForSetAvatarResponse", [avs[0]])
        else:
            self.notify.error(f"Invalid doneStatus from MakeAToon: {done}")

    def exitCreateAvatar(self):
        self.ignore("makeAToonComplete")
        self.ignore("nameShopPost")
        self.ignore("createAvatar")
        self.avCreate.unload()
        self.avCreate = None
        self.handler = None
        if hasattr(self, "newPotAv"):
            del self.newPotAv

    def handleAvatarResponseMsg(self, avatarId, di):
        """
        This is the handler called at startup time when the server is
        telling us details about our own avatar.  A different handler,
        handleGetAvatarDetailsResp, is called in response to the
        same message received while playing the game (in which case it
        is a response to a query about someone else, not information
        about ourselves).
        """
        self.cleanupWaitingForDatabase()
        dclass = self.dclassesByName["DistributedToon"]

        NametagGlobals.setMasterArrowsOn(0)
        if self.music:
            self.music.stop()
            self.music = None

        base.remakeControlManager()
        localAvatar = LocalToon.LocalToon(self)
        localAvatar.dclass = dclass

        base.localAvatar = localAvatar
        messenger.send("localAvatarCreated")

        NametagGlobals.setToon(base.localAvatar)

        localAvatar.doId = avatarId
        self.localAvatarDoId = avatarId

        localAvatar.setLocation(None, None)
        localAvatar.generateInit()
        localAvatar.generate()
        localAvatar.updateAllRequiredFields(dclass, di)

        self.doId2do[avatarId] = localAvatar

        localAvatar.initInterface()
        self.loginFSM.request("playingGame")

    def n_handleGetAvatarDetailsResp(self, avId, fields):
        self.notify.info(f"Query reponse for avId {int(avId)}")
        try:
            pad = self.__queryAvatarMap[avId]
        except BaseException:
            self.notify.warning(f"Received unexpected or outdated details for avatar {int(avId)}.")
            return

        del self.__queryAvatarMap[avId]

        for currentField in fields:
            getattr(pad.avatar, currentField[0])(*currentField[1:])

        pad.func(pad.avatar, *pad.args)

        pad.delayDelete.destroy()

    def handleGetAvatarDetailsResp(self, di):
        avId = di.getUint32()
        returncode = di.getUint8()
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")

        self.notify.info(f"Got query response for avatar {int(avId)}, code = {int(returncode)}.")

        try:
            pad = self.__queryAvatarMap[avId]
        except BaseException:
            self.notify.warning(f"Received unexpected or outdated details for avatar {int(avId)}.")
            return

        del self.__queryAvatarMap[avId]

        gotData = 0
        dclassName = pad.args[0]
        dclass = self.dclassesByName[dclassName]
        for x in dclass.fields:
            getattr(pad.avatar, x[0])(*x[1:])

        gotData = 1

        if isinstance(pad.func, (str, bytes)):
            messenger.send(pad.func, list((gotData, pad.avatar) + pad.args))
        else:
            pad.func(*(gotData, pad.avatar) + pad.args)

        pad.delayDelete.destroy()

    def enterPlayingGame(self):
        OTPClientRepository.OTPClientRepository.enterPlayingGame(self)
        shard = random.choice(self.listActiveShards())[0]
        requestStatus = dict(shardId=shard, zoneId=base.localAvatar.defaultZone, how="teleport")
        self.gameFSM.request("waitOnEnterResponses", [requestStatus])
        self._userLoggingOut = False

    def exitPlayingGame(self):
        ivalMgr.interrupt()

        taskMgr.remove("avatarRequestQueueTask")

        OTPClientRepository.OTPClientRepository.exitPlayingGame(self)

        if base.localAvatar:
            base.cmod.reparentToRender()
            camera.setPos(0, 0, 0)
            camera.setHpr(0, 0, 0)
            del self.doId2do[base.localAvatar.getDoId()]
            if base.localAvatar.getDelayDeleteCount() != 0:
                self.notify.warning(
                    f"could not delete base.localAvatar, delayDeletes={base.localAvatar.getDelayDeleteNames()}"
                )
            base.localAvatar.deleteOrDelay()
            base.localAvatar.ignoreAll()
            base.localAvatar.detectLeaks()
            NametagGlobals.setToon(base.cam)
            messenger.send("deletingLocalAvatar")
            base.localAvatar = None

        base.transitions.noTransitions()

    def enterWaitOnEnterResponses(self, requestStatus):
        self.resetDeletedSubShardDoIds()
        OTPClientRepository.OTPClientRepository.enterWaitOnEnterResponses(self, requestStatus)

    def enterSwitchShards(self, shardId, avId):
        OTPClientRepository.OTPClientRepository.enterSwitchShards(self, shardId, avId)
        self.handler = self.handleCloseShard

    def exitSwitchShards(self):
        OTPClientRepository.OTPClientRepository.exitSwitchShards(self)
        self.ignore(ToontownClientRepository.ClearInterestDoneEvent)
        self.handler = None

    def handleCloseShard(self, msgType, di):
        if msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED"]:
            di2 = PyDatagramIterator(di)
            parentId = di2.getUint32()
            if self._doIdIsOnCurrentShard(parentId):
                return
        elif msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED_OTHER"]:
            di2 = PyDatagramIterator(di)
            parentId = di2.getUint32()
            if self._doIdIsOnCurrentShard(parentId):
                return
        elif msgType == MsgName2Id["CLIENT_OBJECT_SET_FIELD"]:
            di2 = PyDatagramIterator(di)
            doId = di2.getUint32()
            if self._doIdIsOnCurrentShard(doId):
                return
        self.handleMessageType(msgType, di)

    def _logFailedDisable(self, doId, ownerView):
        if doId not in self.doId2do and doId in self._deletedSubShardDoIds:
            return
        OTPClientRepository.OTPClientRepository._logFailedDisable(self, doId, ownerView)

    def exitCloseShard(self):
        OTPClientRepository.OTPClientRepository.exitCloseShard(self)
        self.ignore(ToontownClientRepository.ClearInterestDoneEvent)
        self.handler = None

    def isShardInterestOpen(self):
        return (self.old_setzone_interest_handle is not None) or (self.uberZoneInterest is not None)

    def resetDeletedSubShardDoIds(self):
        self._deletedSubShardDoIds.clear()

    def dumpAllSubShardObjects(self):
        if self.KeepSubShardObjects:
            return

        messenger.send("clientCleanup")
        for avId, pad in list(self.__queryAvatarMap.items()):
            pad.delayDelete.destroy()
        self.__queryAvatarMap = {}
        delayDeleted = []
        doIds = list(self.doId2do.keys())
        for doId in doIds:
            obj = self.doId2do[doId]
            if base.localAvatar and obj.parentId == base.localAvatar.defaultShard and obj is not base.localAvatar:
                if not obj.neverDisable:
                    self.deleteObject(doId)
                    self._deletedSubShardDoIds.add(doId)
                    if obj.getDelayDeleteCount() != 0:
                        delayDeleted.append(obj)
        delayDeleteLeaks = []
        for obj in delayDeleted:
            if obj.getDelayDeleteCount() != 0:
                delayDeleteLeaks.append(obj)
        if len(delayDeleteLeaks):
            s = "dumpAllSubShardObjects:"
            for obj in delayDeleteLeaks:
                s += f"\n  could not delete {safeRepr(obj)} ({itype(obj)}), delayDeletes={obj.getDelayDeleteNames()}"
            self.notify.error(s)

    def _removeCurrentShardInterest(self, callback):
        if self.old_setzone_interest_handle is None:
            assert self.uberZoneInterest is None
            self.notify.warning("removeToontownShardInterest: no shard interest open")
            callback()
            return
        self.acceptOnce(
            ToontownClientRepository.ClearInterestDoneEvent, Functor(self._tcrRemoveUberZoneInterest, callback)
        )
        self._removeEmulatedSetZone(ToontownClientRepository.ClearInterestDoneEvent)

    def _tcrRemoveUberZoneInterest(self, callback):
        assert self.uberZoneInterest is not None
        self.acceptOnce(
            ToontownClientRepository.ClearInterestDoneEvent, Functor(self._tcrRemoveShardInterestDone, callback)
        )
        self.removeInterest(self.uberZoneInterest, ToontownClientRepository.ClearInterestDoneEvent)

    def _tcrRemoveShardInterestDone(self, callback):
        self.uberZoneInterest = None
        callback()

    def _doIdIsOnCurrentShard(self, doId):
        if doId == base.localAvatar.defaultShard:
            return True
        do = self.getDo(doId)
        if do:
            if do.parentId == base.localAvatar.defaultShard:
                return True
        return False

    def identifyAvatar(self, doId):
        """
        Returns either an avatar or a FriendHandle, whichever we can
        find, to reference the indicated doId.
        """
        if doId in self.doId2do:
            return self.doId2do[doId]
        else:
            return self.identifyFriend(doId)

    def identifyFriend(self, doId):
        avatar = self.doId2do.get(doId)
        if not avatar or not isinstance(avatar, DistributedToon):
            return None
        return avatar

    def forbidCheesyEffects(self, forbid):
        """
        If forbid is 1, increments the forbidCheesyEffects counter,
        preventing cheesy effects in the current context.  If forbid is
        0, decrements this counter.  You should always match
        increments with decrements.
        """
        wasAllowed = self.__forbidCheesyEffects != 0
        if forbid:
            self.__forbidCheesyEffects += 1
        else:
            self.__forbidCheesyEffects -= 1

        assert self.__forbidCheesyEffects >= 0
        isAllowed = self.__forbidCheesyEffects != 0
        if wasAllowed != isAllowed:
            for av in Avatar.Avatar.ActiveAvatars:
                if hasattr(av, "reconsiderCheesyEffect"):
                    av.reconsiderCheesyEffect()

            base.localAvatar.reconsiderCheesyEffect()

    def areCheesyEffectsAllowed(self):
        return self.__forbidCheesyEffects == 0

    def getNextSetZoneDoneEvent(self):
        """this returns the event that will be generated when the next
        emulated setZone msg (not yet sent) completes, and we are fully
        in the new zone with all DOs in that zone"""
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        return f"{ToontownClientRepository.EmuSetZoneDoneEvent}-{self.setZonesEmulated + 1}"

    def getLastSetZoneDoneEvent(self):
        """this returns the event that will be generated when the last
        emulated setZone msg (already sent) completes, and we are fully
        in the new zone with all DOs in that zone"""
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        return f"{ToontownClientRepository.EmuSetZoneDoneEvent}-{self.setZonesEmulated}"

    def sendSetZoneMsg(self, zoneId, visibleZoneList=None):
        event = self.getNextSetZoneDoneEvent()
        self.setZonesEmulated += 1
        parentId = base.localAvatar.defaultShard

        self.sendSetLocation(base.localAvatar.doId, parentId, zoneId)
        base.localAvatar.setLocation(parentId, zoneId)

        interestZones = zoneId
        if visibleZoneList is not None:
            assert zoneId in visibleZoneList
            interestZones = visibleZoneList

        self._addInterestOpToQueue(
            ToontownClientRepository.SetInterest, [parentId, interestZones, "OldSetZoneEmulator"], event
        )

    def resetInterestStateForConnectionLoss(self):
        OTPClientRepository.OTPClientRepository.resetInterestStateForConnectionLoss(self)
        self.old_setzone_interest_handle = None
        self.setZoneQueue.clear()

    def _removeEmulatedSetZone(self, doneEvent):
        self._addInterestOpToQueue(ToontownClientRepository.ClearInterest, None, doneEvent)

    def _addInterestOpToQueue(self, op, args, event):
        self.setZoneQueue.append([op, args, event])
        if len(self.setZoneQueue) == 1:
            self._sendNextSetZone()

    def _sendNextSetZone(self):
        op, args, event = self.setZoneQueue[0]
        if op == ToontownClientRepository.SetInterest:
            parentId, interestZones, name = args
            if self.old_setzone_interest_handle is None:
                self.old_setzone_interest_handle = self.addInterest(
                    parentId, interestZones, name, ToontownClientRepository.SetZoneDoneEvent
                )
            else:
                self.alterInterest(
                    self.old_setzone_interest_handle,
                    parentId,
                    interestZones,
                    name,
                    ToontownClientRepository.SetZoneDoneEvent,
                )
        elif op == ToontownClientRepository.ClearInterest:
            self.removeInterest(self.old_setzone_interest_handle, ToontownClientRepository.SetZoneDoneEvent)
            self.old_setzone_interest_handle = None
        else:
            self.notify.error(f"unknown setZone op: {op}")

    def _handleEmuSetZoneDone(self):
        op, args, event = self.setZoneQueue.popleft()
        queueIsEmpty = len(self.setZoneQueue) == 0
        if event is not None:
            if not base.killInterestResponse:
                messenger.send(event)
            else:
                if not hasattr(self, "_dontSendSetZoneDone"):
                    import random

                    if random.random() < 0.05:
                        self._dontSendSetZoneDone = True
                    else:
                        messenger.send(event)
        if not queueIsEmpty:
            self._sendNextSetZone()

    def _isPlayerDclass(self, dclass):
        return dclass == self._playerAvDclass

    def isValidPlayerLocation(self, parentId, zoneId):
        if not self.distributedDistrict:
            return False
        if parentId != self.distributedDistrict.doId:
            return False
        if (parentId == self.distributedDistrict.doId) and (zoneId == OTP_ZONE_ID_MANAGEMENT):
            return False
        return True

    def sendQuietZoneRequest(self):
        assert self.notify.debugStateCall(self, "loginFSM", "gameFSM")
        self.sendSetZoneMsg(OTP_ZONE_ID_QUIET_ZONE)

    def handleQuietZoneGenerateWithRequired(self, di):
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        doId = di.getUint32()
        dclass = self.dclassesByNumber[classId]
        if dclass.getClassDef().neverDisable:
            dclass.startGenerate()
            distObj = self.generateWithRequiredFields(dclass, doId, di, parentId, zoneId)
            dclass.stopGenerate()

    def handleQuietZoneGenerateWithRequiredOther(self, di):
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        doId = di.getUint32()
        dclass = self.dclassesByNumber[classId]
        if dclass.getClassDef().neverDisable:
            dclass.startGenerate()
            distObj = self.generateWithRequiredOtherFields(dclass, doId, di, parentId, zoneId)
            dclass.stopGenerate()

    def handleQuietZoneUpdateField(self, di):
        di2 = PyDatagramIterator(di.getDatagram())
        doId = di2.getUint32()
        if doId in self.deferredDoIds:
            args, deferrable, dg0, updates = self.deferredDoIds[doId]
            dclass = args[2]
            if not dclass.getClassDef().neverDisable:
                return
        else:
            do = self.getDo(doId)
            if do:
                if not do.neverDisable:
                    return
        OTPClientRepository.OTPClientRepository.handleUpdateField(self, di)

    def handleDelete(self, di):
        doId = di.getUint32()
        self.deleteObject(doId)

    def deleteObject(self, doId, ownerView=False):
        """
        Removes the object from the client's view of the world.  This
        should normally not be called except in the case of error
        recovery, since the server will normally be responsible for
        deleting and disabling objects as they go out of scope.

        After this is called, future updates by server on this object
        will be ignored (with a warning message).  The object will
        become valid again the next time the server sends a generate
        message for this doId.

        This is not a distributed message and does not delete the
        object on the server or on any other client.
        """
        if doId in self.doId2do:
            obj = self.doId2do[doId]
            del self.doId2do[doId]
            obj.deleteOrDelay()
            if obj.getDelayDeleteCount() <= 0:
                obj.detectLeaks()
        elif self.cache.contains(doId):
            self.cache.delete(doId)
        else:
            self.notify.warning(f"Asked to delete non-existent DistObj {doId}")

    def _abandonShard(self):
        for doId, obj in list(self.doId2do.items()):
            if (obj.parentId == base.localAvatar.defaultShard) and (obj is not base.localAvatar):
                self.deleteObject(doId)

    def handleGenerateWithRequiredOtherOwner(self, di):
        if self.loginFSM.getCurrentState().getName() == "waitForSetAvatarResponse":
            doId = di.getUint32()
            parentId = di.getUint32()
            zoneId = di.getUint32()
            dclassId = di.getUint16()
            self.handleAvatarResponseMsg(doId, di)

    def renderFrame(self):
        gsg = base.win.getGsg()
        if gsg:
            render2d.prepareScene(gsg)
        base.graphicsEngine.renderFrame()

    def renderFrames(self):
        base.graphicsEngine.renderFrame()
        base.graphicsEngine.renderFrame()

    def handleLoginToontownResponse(self, responseBlob):
        """Handle the new toontown specific login response.

        We having gotten a toontown specific login response from the
        server for our normal Toontown login, via the account server.
        We can also get here with use-tt-specific-dev-login set to 1
        """
        self.notify.debug("handleLoginToontownResponse")

        responseData = json.loads(responseBlob)

        now = time.time()

        returnCode = responseData.get("returnCode")
        errorString = responseData.get("respString")

        self.accountName = responseData.get("userName")

        self.accountNameApproved = "YES"

        accountDetailRecord = AccountDetailRecord()
        self.accountDetailRecord = accountDetailRecord

        createFriendsWithChat = responseData.get("createFriendsWithChat")
        canChat = (createFriendsWithChat == "YES") or (createFriendsWithChat == "CODE")
        self.secretChatAllowed = canChat
        self.notify.info(f"CREATE_FRIENDS_WITH_CHAT from game server login: {createFriendsWithChat} {canChat}")

        sec = time.time()
        usec = time.process_time()
        serverTime = sec + usec / 1000000.0
        self.serverTimeUponLogin = serverTime
        self.clientTimeUponLogin = now
        self.globalClockRealTimeUponLogin = globalClock.getRealTime()
        serverDelta = serverTime - now
        self.setServerDelta(serverDelta)
        self.notify.setServerDelta(serverDelta, 28800)
        self.whiteListChatEnabled = 1

        self.accountDays = responseData.get("accountDays", 0)

        self.userName = responseData.get("userName")

        self.notify.info(f"Login response return code {returnCode}")

        if returnCode == 0:
            self.loginFSM.request("waitForGameList")
        else:
            self.notify.warning(f"Login failed: {errorString}")
            self.loginFSM.request("reject")
