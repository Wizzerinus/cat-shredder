from panda3d.otp import CFThought, CFTimeout, WhisperPopup

from otp.avatar import LocalAvatar
from otp.avatar import PositionExaminer
from otp.chat.TalkAssistantV2 import TalkAssistantV2
from toontown.chat import ResistanceChat, ToontownChatManager
from toontown.toon import DistributedToon
from toontown.toon import LaffMeter
from toontown.toon import Toon
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont


class LocalToon(DistributedToon.DistributedToon, LocalAvatar.LocalAvatar):
    neverDisable = 1
    orbitalMode = False

    def __init__(self, cr):
        try:
            self.LocalToon_initialized
            return
        except:
            self.LocalToon_initialized = 1

        DistributedToon.DistributedToon.__init__(self, cr)
        chatMgr = ToontownChatManager.ToontownChatManager(cr, self)
        talkAssistant = TalkAssistantV2()
        LocalAvatar.LocalAvatar.__init__(self, cr, chatMgr, talkAssistant, passMessagesThrough=True)
        self.soundRun = base.loader.loadSfx("phase_3.5/audio/sfx/AV_footstep_runloop.ogg")
        self.soundWalk = base.loader.loadSfx("phase_3.5/audio/sfx/AV_footstep_walkloop.ogg")
        self.soundWhisper = base.loader.loadSfx("phase_3.5/audio/sfx/GUI_whisper_3.ogg")
        self.soundPhoneRing = base.loader.loadSfx("phase_3.5/audio/sfx/telephone_ring.ogg")
        self.soundSystemMessage = base.loader.loadSfx("phase_3/audio/sfx/clock03.ogg")
        self.positionExaminer = PositionExaminer.PositionExaminer()
        self.laffMeter = None

    def wantLegacyLifter(self):
        return True

    def announceGenerate(self):
        self.startLookAround()
        if base.wantNametags:
            self.nametag.manage(base.marginManager)
        DistributedToon.DistributedToon.announceGenerate(self)

    def disable(self):
        self.laffMeter.destroy()
        del self.laffMeter
        if base.wantNametags:
            self.nametag.unmanage(base.marginManager)
        self.ignoreAll()
        DistributedToon.DistributedToon.disable(self)

    def disableBodyCollisions(self):
        pass

    def delete(self):
        try:
            self.LocalToon_deleted
            return
        except:
            self.LocalToon_deleted = 1

        Toon.unloadDialog()
        DistributedToon.DistributedToon.delete(self)
        LocalAvatar.LocalAvatar.delete(self)

    def initInterface(self):
        self.laffMeter = LaffMeter.LaffMeter(self.style, self.hp, self.maxHp)
        self.laffMeter.setAvatar(self)
        self.laffMeter.setScale(0.075)
        self.laffMeter.reparentTo(base.a2dBottomLeft)
        self.laffMeter.setPos(0.15, 0.0, 0.13)
        self.laffMeter.stop()

    def isLocal(self):
        return 1

    def displayTalkWhisper(self, fromId, avatarName, rawString, mods):
        """displayWhisper(self, int fromId, string chatString, int whisperType)

        Displays the whisper message in whatever capacity makes sense.
        This function overrides a similar function in DistributedAvatar.
        """
        sender = base.cr.identifyAvatar(fromId)
        if sender:
            chatString, scrubbed = sender.scrubTalk(rawString, mods)
        else:
            chatString, scrubbed = self.scrubTalk(rawString, mods)

        sfx = self.soundWhisper

        chatString = avatarName + ": " + chatString

        whisper = WhisperPopup(chatString, getInterfaceFont(), WhisperPopup.WTNormal)
        whisper.setClickable(avatarName, fromId)
        whisper.manage(base.marginManager)
        base.playSfx(sfx)

    def canChat(self):
        return 1

    def startChat(self):
        self.notify.info("calling LocalAvatar.startchat")
        LocalAvatar.LocalAvatar.startChat(self)
        self.accept("chatUpdateSCResistance", self.d_reqSCResistance)

    def d_reqSCResistance(self, msgIndex):
        messenger.send("wakeup")
        nearbyPlayers = self.getNearbyPlayers(ResistanceChat.EFFECT_RADIUS)
        self.sendUpdate("reqSCResistance", [msgIndex, nearbyPlayers])

    def stopChat(self):
        LocalAvatar.LocalAvatar.stopChat(self)
        self.ignore("chatUpdateSCResistance")

    def displayWhisper(self, fromId, chatString, whisperType):
        """displayWhisper(self, int fromId, string chatString, int whisperType)

        Displays the whisper message in whatever capacity makes sense.
        This function overrides a similar function in DistributedAvatar.
        """
        sfx = self.soundWhisper
        sender = base.cr.identifyAvatar(fromId)

        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            if sender is None:
                return
            chatString = sender.getName() + ": " + chatString

        whisper = WhisperPopup(chatString, getInterfaceFont(), whisperType)
        if sender is not None:
            whisper.setClickable(sender.getName(), fromId)

        whisper.manage(base.marginManager)
        base.playSfx(sfx)

    def displaySystemClickableWhisper(self, fromId, chatString, whisperType):
        """displayPartyCanStartWhisper (self, int fromId, string chatString, int whisperType)

        Displays the party can start whisper message.
        """
        sfx = self.soundWhisper
        sender = base.cr.identifyAvatar(fromId)

        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            if sender is None:
                return
            chatString = sender.getName() + ": " + chatString

        whisper = WhisperPopup(chatString, getInterfaceFont(), whisperType)
        whisper.setClickable("", fromId)

        whisper.manage(base.marginManager)
        base.playSfx(sfx)

    def thinkPos(self):
        pos = self.getPos()
        hpr = self.getHpr()
        serverVersion = base.cr.getServerVersion()
        districtName = base.cr.getShardName(base.localAvatar.defaultShard)
        if (
            hasattr(base.cr.playGame.hood, "loader")
            and hasattr(base.cr.playGame.hood.loader, "place")
            and base.cr.playGame.getPlace() != None
        ):
            zoneId = base.cr.playGame.getPlace().getZoneId()
        else:
            zoneId = "?"
        strPos = (
            "(%.3f" % pos[0]
            + "\n %.3f" % pos[1]
            + "\n %.3f)" % pos[2]
            + "\nH: %.3f" % hpr[0]
            + "\nZone: %s" % str(zoneId)
            + ",\nVer: %s, " % serverVersion
            + "\nDistrict: %s" % districtName
        )
        print("Current position=", strPos.replace("\n", ", "))
        self.setChatAbsolute(strPos, CFThought | CFTimeout)
        return

    def setGhostMode(self, flag):
        if flag == 2:
            self.seeGhosts = 1
        DistributedToon.DistributedToon.setGhostMode(self, flag)

    def hasActiveBoardingGroup(self):
        if hasattr(self, "boardingParty") and self.boardingParty:
            return self.boardingParty.hasActiveGroup(self.doId)
        else:
            return False

    def getZoneId(self):
        return self._zoneId

    def setZoneId(self, value):
        if value == -1:
            self.notify.error("zoneId should not be set to -1, tell Redmond")
        self._zoneId = value

    zoneId = property(getZoneId, setZoneId)

    def setSleepAutoReply(self, fromId):
        av = base.cr.identifyAvatar(fromId)
        if isinstance(av, DistributedToon.DistributedToon):
            base.localAvatar.setSystemMessage(
                0, TTLocalizer.sleep_auto_reply % av.getName(), WhisperPopup.WTToontownBoardingGroup
            )
        elif av is not None:
            self.notify.warning("setSleepAutoReply from non-toon %s" % fromId)
        return
