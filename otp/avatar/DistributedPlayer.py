from panda3d.otp import CFQuicktalker, CFSpeech, CFTimeout, WhisperPopup

from otp.avatar import Avatar, PlayerBase
from otp.avatar import DistributedAvatar
from otp.speedchat import SCDecoders
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals import TTGlobalsChat


class DistributedPlayer(DistributedAvatar.DistributedAvatar, PlayerBase.PlayerBase):
    """Distributed Player class:"""

    TeleportFailureTimeout = 60.0

    DistributedPlayer_initialized = False
    DistributedPlayer_deleted = False

    frameTimeWeArrivedOnDistrict = -1
    accountName = None

    def __init__(self, cr):
        """
        Handle distributed updates
        """
        if self.DistributedPlayer_initialized:
            return
        self.DistributedPlayer_initialized = True

        DistributedAvatar.DistributedAvatar.__init__(self, cr)
        PlayerBase.PlayerBase.__init__(self)

        self.__teleportAvailable = 0

        self.inventory = None

        self.ignoreList = set()

        self.lastFailedTeleportMessage = {}
        self._districtWeAreGeneratedOn = None

        self.DISLname = ""
        self.DISLid = 0
        self.staffAccess = 0
        self.autoRun = 0

    def disable(self):
        DistributedAvatar.DistributedAvatar.disable(self)

    def delete(self):
        if self.DistributedPlayer_deleted:
            return

        self.DistributedPlayer_deleted = True
        if self.inventory:
            self.inventory.unload()
        del self.inventory
        DistributedAvatar.DistributedAvatar.delete(self)

    def generate(self):
        DistributedAvatar.DistributedAvatar.generate(self)

    def setLocation(self, parentId, zoneId, teleport=0):
        DistributedAvatar.DistributedAvatar.setLocation(self, parentId, zoneId, teleport)
        if not (parentId in (0, None) and zoneId in (0, None)):
            if not self.cr.isValidPlayerLocation(parentId, zoneId):
                self.cr.disableDoId(self.doId)
                self.cr.deleteObject(self.doId)

    def isGeneratedOnDistrict(self, districtId=None):
        if districtId is None:
            return self._districtWeAreGeneratedOn is not None
        else:
            return self._districtWeAreGeneratedOn == districtId

    @staticmethod
    def getArrivedOnDistrictEvent(districtId=None):
        if districtId is None:
            return "arrivedOnDistrict"
        else:
            return f"arrivedOnDistrict-{districtId}"

    def arrivedOnDistrict(self, districtId):
        curFrameTime = globalClock.getFrameTime()
        if curFrameTime == self.frameTimeWeArrivedOnDistrict:
            if districtId == 0 and self._districtWeAreGeneratedOn:
                self.notify.warning(
                    f"ignoring arrivedOnDistrict 0, since arrivedOnDistrict "
                    f"{self._districtWeAreGeneratedOn} occured on the same frame"
                )
                return
        self._districtWeAreGeneratedOn = districtId
        self.frameTimeWeArrivedOnDistrict = globalClock.getFrameTime()
        messenger.send(self.getArrivedOnDistrictEvent(districtId))
        messenger.send(self.getArrivedOnDistrictEvent())

    def setLeftDistrict(self):
        self._districtWeAreGeneratedOn = None

    def hasParentingRules(self):
        if self is base.localAvatar:
            return True

    def setAccountName(self, accountName):
        self.accountName = accountName

    def setSystemMessage(self, aboutId, chatString, whisperType=WhisperPopup.WTSystem):
        """setSystemMessage(self, int aboutId, string chatString)

        A message generated from the system (or the AI, or something
        like that).  If this involves another avatar (e.g. Flippy is
        now online), the aboutId is filled in; otherwise, aboutId is
        zero.
        """
        self.displayWhisper(aboutId, chatString, whisperType)

    def displayWhisper(self, fromId, chatString, whisperType):
        """displayWhisper(self, int fromId, string chatString, int whisperType)

        Displays the whisper message in whatever capacity makes sense.
        This is separate from setWhisper so we can safely call it by
        name from within setWhisper and expect the derived function to
        override it.
        """
        self.notify.info(f"Whisper type {whisperType} from {fromId}: {chatString}")

    def setWhisperSCFrom(self, fromId, msgIndex):
        if base.localAvatar.checkIgnored(fromId):
            return

        chatString = SCDecoders.decodeSCStaticTextMsg(msgIndex)
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTQuickTalker)
            base.talkAssistant.receiveSCMessage(TTGlobalsChat.SPEEDCHAT_NORMAL, fromId, msgIndex, True)

    @staticmethod
    def whisperSCCustomTo(msgIndex, sendToId):
        """
        Sends a speedchat whisper message to the indicated
        toon, prefixed with our own name.
        """
        messenger.send("wakeup")
        base.cr.ttFriendsManager.d_whisperSCCustomTo(sendToId, msgIndex)

    def setWhisperSCCustomFrom(self, fromId, msgIndex):
        """
        Receive and decode the SC message.
        """
        if base.localAvatar.checkIgnored(fromId):
            return

        chatString = SCDecoders.decodeSCCustomMsg(msgIndex)
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTQuickTalker)
            base.talkAssistant.receiveSCMessage(TTGlobalsChat.SPEEDCHAT_CUSTOM, fromId, msgIndex, True)

    @staticmethod
    def whisperSCEmoteTo(emoteId, sendToId):
        """
        Sends a speedchat whisper message to the indicated
        toon, prefixed with our own name.
        """
        messenger.send("wakeup")
        base.cr.ttFriendsManager.d_whisperSCEmoteTo(sendToId, emoteId)

    @staticmethod
    def whisperSCTo(msgIndex, sendToId):
        """
        Sends a speedchat whisper message to the indicated
        avatar/player.
        """
        messenger.send("wakeup")
        base.cr.ttFriendsManager.d_whisperSCTo(sendToId, msgIndex)

    def setWhisperSCEmoteFrom(self, fromId, emoteId):
        """
        Receive and decode the SC message.
        """
        handle = base.cr.identifyAvatar(fromId)
        if handle is None:
            return

        if base.localAvatar.checkIgnored(fromId):
            return

        chatString = SCDecoders.decodeSCEmoteWhisperMsg(emoteId, handle.getName())
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTEmote)
            base.talkAssistant.receiveSCMessage(TTGlobalsChat.SPEEDCHAT_EMOTE, fromId, emoteId, True)

    def setTalk(self, avId, chat, mods):
        if base.localAvatar.checkIgnored(avId):
            return

        newText, scrubbed = self.scrubTalk(chat, mods)
        self.displayTalk(newText)
        base.talkAssistant.receiveMessage(avId, newText)

    def setTalkWhisper(self, avId, avName, chat, mods):
        if base.localAvatar.checkIgnored(avId):
            return

        newText, scrubbed = self.scrubTalk(chat, mods)
        self.displayTalkWhisper(avId, avName, chat, mods)
        base.talkAssistant.receiveMessage(avId, newText, avName)

    def displayTalkWhisper(self, fromId, avatarName, chatString, mods):
        """displayTalkWhisper(self, int fromId, string chatString)

        Displays the whisper message in whatever capacity makes sense.
        This is separate from setWhisper, so we can safely call it by
        name from within setWhisper and expect the derived function to
        override it.
        """
        self.notify.info(f"TalkWhisper from {fromId}: {chatString}")

    def scrubTalk(self, chat, mods):
        """
        returns chat where the mods have been replaced with appropreiate words
        this is not in chat assistant because the replacement needs to be done
        by the object that speeaks them. A pirate says "arr",
        a duck says "quack", etc..
        """
        return chat, 0

    def b_setSC(self, msgIndex):
        self.setSC(msgIndex)
        self.d_setSC(msgIndex)

    def d_setSC(self, msgIndex):
        messenger.send("wakeup")
        self.sendUpdate("setSC", [msgIndex])

    def setSC(self, msgIndex):
        """
        Receive and decode the SC message
        """

        if base.localAvatar.checkIgnored(self.doId):
            return

        chatString = SCDecoders.decodeSCStaticTextMsg(msgIndex)
        if chatString:
            self.setChatAbsolute(chatString, CFSpeech | CFQuicktalker | CFTimeout)
        base.talkAssistant.receiveSCMessage(TTGlobalsChat.SPEEDCHAT_NORMAL, self.doId, msgIndex)

    def b_setSCCustom(self, msgIndex):
        self.setSCCustom(msgIndex)
        self.d_setSCCustom(msgIndex)

    def d_setSCCustom(self, msgIndex):
        messenger.send("wakeup")
        self.sendUpdate("setSCCustom", [msgIndex])

    def setSCCustom(self, msgIndex):
        """
        Receive and decode the SC message
        """

        if base.localAvatar.checkIgnored(self.doId):
            return

        chatString = SCDecoders.decodeSCCustomMsg(msgIndex)
        if chatString:
            self.setChatAbsolute(chatString, CFSpeech | CFQuicktalker | CFTimeout)
        base.talkAssistant.receiveSCMessage(TTGlobalsChat.SPEEDCHAT_CUSTOM, self.doId, msgIndex)

    def b_setSCEmote(self, emoteId):
        self.b_setEmoteState(emoteId, animMultiplier=self.animMultiplier)

    @staticmethod
    def d_teleportQuery(sendToId=None):
        base.cr.ttFriendsManager.d_teleportQuery(sendToId)

    def teleportQuery(self, requesterId):
        """teleportQuery(self, int requesterId)

        This distributed message is sent peer-to-peer from one client
        who is considering teleporting to another client.  When it is
        received, the receiving client should send back a
        teleportResponse indicating whether she is available to be
        teleported to (e.g. not on a trolley or something), and if so,
        where she is.
        """
        avatar = base.cr.identifyAvatar(requesterId)
        if avatar is None:
            self.d_teleportResponse(self.doId, 0, 0, 0)
            return

        if base.localAvatar.checkIgnored(requesterId):
            self.d_teleportResponse(self.doId, 2, 0, 0)
            return

        if hasattr(base, "distributedParty"):
            if base.distributedParty.partyInfo.isPrivate:
                if requesterId not in base.distributedParty.inviteeIds:
                    self.d_teleportResponse(self.doId, 0, 0, 0)
                    return

            if base.distributedParty.isPartyEnding:
                self.d_teleportResponse(self.doId, 0, 0, 0)
                return

        if self.__teleportAvailable and not self.ghostMode:
            self.setSystemMessage(requesterId, TTLocalizer.WhisperComingToVisit % (avatar.getName()))

            messenger.send("teleportQuery", [avatar, self])
            return

        if self.failedTeleportMessageOk(requesterId):
            self.setSystemMessage(requesterId, TTLocalizer.WhisperFailedVisit % (avatar.getName()))

        self.d_teleportResponse(self.doId, 0, 0, 0)

    def failedTeleportMessageOk(self, fromId):
        """failedTeleportMessageOk(self, int fromId)

        Registers a failure-to-teleport attempt from the indicated
        avatar.  Returns true if it is ok to display this message, or
        false if the message should be suppressed (because we just
        recently displayed one).
        """
        now = globalClock.getFrameTime()
        lastTime = self.lastFailedTeleportMessage.get(fromId, None)
        if lastTime is not None:
            elapsed = now - lastTime
            if elapsed < self.TeleportFailureTimeout:
                return 0

        self.lastFailedTeleportMessage[fromId] = now
        return 1

    @staticmethod
    def d_teleportResponse(avId, available, shardId, zoneId):
        base.cr.ttFriendsManager.d_teleportResponse(avId, available, shardId, zoneId)

    @staticmethod
    def teleportResponse(avId, available, shardId, zoneId):
        messenger.send("teleportResponse", [avId, available, shardId, zoneId])

    @staticmethod
    def d_teleportGiveup(sendToId=None):
        base.cr.ttFriendsManager.d_teleportGiveup(sendToId)

    def teleportGiveup(self, requesterId):
        """teleportGiveup(self, int requesterId)

        This message is sent after a client has failed to teleport
        successfully to another client, probably because the target
        client didn't stay put.  It just pops up a whisper message to
        that effect.

        """
        avatar = base.cr.identifyAvatar(requesterId)

        if not self.isValidWhisperSource(avatar):
            self.notify.warning(f"teleportGiveup from non-toon {requesterId}")
            return

        if avatar is not None:
            self.setSystemMessage(requesterId, TTLocalizer.WhisperGiveupVisit % (avatar.getName()))

    def b_teleportGreeting(self, avId):
        self.d_teleportGreeting(avId)
        self.teleportGreeting(avId)

    def d_teleportGreeting(self, avId):
        self.sendUpdate("teleportGreeting", [avId])

    def teleportGreeting(self, avId):
        avatar = base.cr.getDo(avId)
        if isinstance(avatar, Avatar.Avatar):
            self.setChatAbsolute(TTLocalizer.TeleportGreeting % (avatar.getName()), CFSpeech | CFTimeout)
        elif avatar is not None:
            self.notify.warning(f"got teleportGreeting from {self.doId} referencing non-toon {avId}")

    def setTeleportAvailable(self, available):
        """setTeleportAvailable(self, bool available)

        Sets the 'teleportAvailable' flag.  When this is true, the
        client is deemed to be available to be teleported to, and
        someone should be listening to teleportQuery messages from the
        messenger.  When it is false, teleport queries from nearby
        toons will automatically be returned with a false response
        without generating a teleportQuery message.
        """
        self.__teleportAvailable = available

    def getTeleportAvailable(self):
        return self.__teleportAvailable

    def setDISLid(self, accountId):
        self.DISLid = accountId

    def setAutoRun(self, value):
        self.autoRun = value

    def getAutoRun(self):
        return self.autoRun

    def setStaffAccess(self, staffAccess):
        self.staffAccess = staffAccess

    def getStaffAccess(self):
        return self.staffAccess

    def addIgnore(self, av):
        self.ignoreList.add(av)

    def removeIgnore(self, av):
        self.ignoreList.remove(av)
