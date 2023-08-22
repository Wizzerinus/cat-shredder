from direct.distributed import DistributedObject
from direct.distributed import DistributedSmoothNode
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import Func, Sequence, Wait
from direct.task.Task import Task
from panda3d.core import *
from panda3d.otp import *

from otp.avatar import DistributedAvatar
from otp.avatar import DistributedPlayer
from otp.speedchat import SCDecoders
from toontown.chat import ResistanceChat, TTSCResistanceTerminal
from toontown.distributed import DelayDelete
from toontown.distributed.DelayDeletable import DelayDeletable
from toontown.toon import TTEmote as Emote
from toontown.toon import Toon
from toontown.toonbase.globals import TTGlobalsChat
from toontown.toonbase.globals.TTGlobalsChat import CheesyEffects
from toontown.toonbase.globals.TTGlobalsGUI import getSignFont
from toontown.toonbase.globals.TTGlobalsRender import *
from toontown.world import ZoneUtil


class DistributedToon(
    DistributedPlayer.DistributedPlayer, Toon.Toon, DistributedSmoothNode.DistributedSmoothNode, DelayDeletable
):
    notify = directNotify.newCategory("DistributedToon")
    partyNotify = directNotify.newCategory("DistributedToon_Party")
    gmNameTag = None

    def __init__(self, cr, bFake=False):
        DistributedPlayer.DistributedPlayer.__init__(self, cr)
        Toon.Toon.__init__(self)
        DistributedSmoothNode.DistributedSmoothNode.__init__(self, cr)

        self.boardingParty = None
        self.track = None
        self.effect = None
        self.splash = None
        self.__currentDialogue = None

    def disable(self):
        if self.boardingParty:
            self.boardingParty.demandDrop()
            self.boardingParty = None
        self.ignore("clientCleanup")
        self.stopAnimations()
        self.clearCheesyEffect()
        self.stopBlink()
        self.stopSmooth()
        self.stopLookAroundNow()
        self.setGhostMode(0)
        if self.track is not None:
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        if self.effect is not None:
            self.effect.destroy()
            self.effect = None
        if self.splash is not None:
            self.splash.destroy()
            self.splash = None
        if self.emote is not None:
            self.emote.finish()
            self.emote = None
        DistributedPlayer.DistributedPlayer.disable(self)

    def delete(self):
        DistributedPlayer.DistributedPlayer.delete(self)
        Toon.Toon.delete(self)
        DistributedSmoothNode.DistributedSmoothNode.delete(self)

    def generate(self):
        DistributedPlayer.DistributedPlayer.generate(self)
        DistributedSmoothNode.DistributedSmoothNode.generate(self)
        self.startBlink()
        self.startSmooth()
        self.accept("clientCleanup", self._handleClientCleanup)

    def announceGenerate(self):
        DistributedPlayer.DistributedPlayer.announceGenerate(self)
        if self.animFSM.getCurrentState().getName() == "off":
            self.setAnimState("neutral")

    def _handleClientCleanup(self):
        if self.track is not None:
            DelayDelete.cleanupDelayDeletes(self.track)

    def setDNAString(self, dnaString):
        Toon.Toon.setDNAString(self, dnaString)

    def setDNA(self, dna):
        oldHat = self.getHat()
        oldGlasses = self.getGlasses()
        oldBackpack = self.getBackpack()
        oldShoes = self.getShoes()
        self.setHat(0, 0)
        self.setGlasses(0, 0)
        self.setBackpack(0, 0)
        self.setShoes(0, 0)
        Toon.Toon.setDNA(self, dna)
        self.setHat(*oldHat)
        self.setGlasses(*oldGlasses)
        self.setBackpack(*oldBackpack)
        self.setShoes(*oldShoes)

    def getNearbyPlayers(self, radius, includeSelf=True):
        nearbyToons = []
        toonIds = self.cr.getObjectsOfExactClass(DistributedToon)
        for toonId, toon in list(toonIds.items()):
            if toon is not self:
                dist = toon.getDistance(self)
                if dist < radius:
                    nearbyToons.append(toonId)

        if includeSelf:
            nearbyToons.append(self.doId)
        return nearbyToons

    def setSCResistance(self, msgIndex, nearbyToons=None):
        if nearbyToons is None:
            nearbyToons = []
        chatString = TTSCResistanceTerminal.decodeTTSCResistanceMsg(msgIndex)
        if chatString:
            self.setChatAbsolute(chatString, CFSpeech | CFTimeout)
        ResistanceChat.doEffect(msgIndex, self, nearbyToons)

    def setDefaultZone(self, zoneId):
        self.defaultZone = zoneId

    def setTalk(self, fromId, chat, mods):
        if base.localAvatar.checkIgnored(fromId):
            return

        newText, scrubbed = self.scrubTalk(chat, mods)
        self.displayTalk(newText)
        base.talkAssistant.receiveMessage(fromId, newText)

    def checkIgnored(self, fromAV):
        if fromAV in self.ignoreList:
            return True

        return False

    def setTalkWhisper(self, avId, avatarName, chat, mods):
        """Overridden from Distributed player becase pirates ignores players a different way"""
        if self.checkIgnored(avId):
            return

        newText, scrubbed = self.scrubTalk(chat, mods)
        self.displayTalkWhisper(avId, avatarName, chat, mods)
        base.talkAssistant.receiveMessage(avId, newText, avatarName)

        if base.localAvatar.sleepFlag == 1 and base.cr.identifyAvatar(avId) != base.localAvatar:
            base.cr.ttFriendsManager.d_sleepAutoReply(avId)

    def setSleepAutoReply(self, fromId):
        """To be overrided by subclass"""

    def setWhisperSCEmoteFrom(self, fromId, emoteId):
        """
        Receive and decode the SC message.
        """
        handle = base.cr.identifyAvatar(fromId)
        if handle is None:
            return

        if not self.isValidWhisperSource(handle):
            self.notify.warning(f"setWhisperSCEmoteFrom non-toon {fromId}")
            return

        if self.checkIgnored(fromId):
            return

        chatString = SCDecoders.decodeSCEmoteWhisperMsg(emoteId, handle.getName())
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTEmote)
            base.talkAssistant.receiveSCMessage(TTGlobalsChat.SPEEDCHAT_EMOTE, emoteId, fromId, True)

    def setWhisperSCFrom(self, fromId, msgIndex):
        """
        Receive and decode the SpeedChat message.
        """
        handle = base.cr.identifyAvatar(fromId)
        if handle is None:
            return

        if not self.isValidWhisperSource(handle):
            self.notify.warning(f"setWhisperSCFrom non-toon {fromId}")
            return

        if self.checkIgnored(fromId):
            return

        chatString = SCDecoders.decodeSCStaticTextMsg(msgIndex)
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTQuickTalker)
            base.talkAssistant.receiveSCMessage(TTGlobalsChat.SPEEDCHAT_NORMAL, msgIndex, fromId, True)

    def died(self):
        messenger.send(self.uniqueName("died"))
        if self.isLocal():
            target_sz = ZoneUtil.getSafeZoneId(self.defaultZone)
            place = self.cr.playGame.getPlace()
            if place and place.fsm:
                place.fsm.request(
                    "died",
                    [
                        {
                            "loader": ZoneUtil.getLoaderName(target_sz),
                            "where": ZoneUtil.getWhereName(target_sz, 1),
                            "how": "teleportIn",
                            "hoodId": target_sz,
                            "zoneId": target_sz,
                            "shardId": None,
                            "avId": -1,
                            "battle": 1,
                        }
                    ],
                )

    def wrtReparentTo(self, parent):
        DistributedSmoothNode.DistributedSmoothNode.wrtReparentTo(self, parent)

    def enterTeleportOut(self, *args, **kw):
        Toon.Toon.enterTeleportOut(self, *args, **kw)
        if self.track:
            self.track.delayDelete = DelayDelete.DelayDelete(self, "enterTeleportOut")

    def exitTeleportOut(self):
        if self.track is not None:
            DelayDelete.cleanupDelayDeletes(self.track)
        Toon.Toon.exitTeleportOut(self)

    def b_setAnimState(self, animName, animMultiplier=1.0, callback=None, extraArgs=None):
        if extraArgs is None:
            extraArgs = []
        self.d_setAnimState(animName, animMultiplier, None, extraArgs)
        self.setAnimState(animName, animMultiplier, None, None, callback, extraArgs)

    def d_setAnimState(self, animName, animMultiplier=1.0, timestamp=None, extraArgs=None):
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate("setAnimState", [animName, animMultiplier, timestamp])

    def setAnimState(self, animName, animMultiplier=1.0, timestamp=None, animType=None, callback=None, extraArgs=None):
        if extraArgs is None:
            extraArgs = []
        if not animName or animName == "None":
            return
        ts = 0.0 if timestamp is None else globalClockDelta.localElapsedTime(timestamp)
        if animMultiplier > 1.0 and animName in ["neutral"]:
            animMultiplier = 1.0
        if self.animFSM.getStateNamed(animName):
            self.animFSM.request(animName, [animMultiplier, ts, callback, extraArgs])
        return

    def b_setEmoteState(self, animIndex, animMultiplier):
        self.setEmoteState(animIndex, animMultiplier)
        self.d_setEmoteState(animIndex, animMultiplier)

    def d_setEmoteState(self, animIndex, animMultiplier):
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate("setEmoteState", [animIndex, animMultiplier, timestamp])

    def setEmoteState(self, animIndex, animMultiplier, timestamp=None):
        if animIndex == Emote.EmoteClear:
            return
        ts = 0.0 if timestamp is None else globalClockDelta.localElapsedTime(timestamp)
        callback = None
        extraArgs = []
        extraArgs.insert(0, animIndex)
        self.doEmote(animIndex, animMultiplier, ts, callback, extraArgs)
        return

    def reconsiderCheesyEffect(self, lerpTime=0.0):
        effect = CheesyEffects.GHOST if self.ghostMode else CheesyEffects.NORMAL
        self.applyCheesyEffect(effect, lerpTime=lerpTime)

    def setGhostMode(self, flag):
        if self.ghostMode != flag:
            self.ghostMode = flag
            if not hasattr(self, "cr"):
                return
            if self.activeState <= DistributedObject.ESDisabled:
                self.notify.debug("not applying cheesy effect to disabled Toon")
            elif self.activeState == DistributedObject.ESGenerating:
                self.reconsiderCheesyEffect()
            elif self.activeState == DistributedObject.ESGenerated:
                self.reconsiderCheesyEffect(lerpTime=0.5)
            else:
                self.notify.warning("unknown activeState: %s" % self.activeState)
            self.showNametag2d()
            self.showNametag3d()
            if hasattr(self, "collNode"):
                if self.ghostMode:
                    self.collNode.setCollideMask(GhostBitmask)
                else:
                    self.collNode.setCollideMask(WallBitmask | PieBitmask)
            if self.isLocal():
                if self.ghostMode:
                    self.useGhostControls()
                else:
                    self.useWalkControls()

    def setResistanceMessages(self, resistanceMessages):
        self.resistanceMessages = resistanceMessages
        if self.isLocal():
            messenger.send("resistanceMessagesChanged")

    def getResistanceMessageCharges(self, textId):
        msgs = self.resistanceMessages
        for i in range(len(msgs)):
            if msgs[i][0] == textId:
                return msgs[i][1]

        return 0

    def doSmoothTask(self, task):
        self.smoother.computeAndApplySmoothPosHpr(self, self)
        self.setSpeed(self.smoother.getSmoothForwardVelocity(), self.smoother.getSmoothRotationalVelocity())
        return Task.cont

    def d_setParent(self, parentToken):
        DistributedSmoothNode.DistributedSmoothNode.d_setParent(self, parentToken)

    def setEmoteAccess(self, bits):
        self.emoteAccess = bits
        if self == base.localAvatar:
            messenger.send("emotesChanged")

    def getZoneId(self):
        place = base.cr.playGame.getPlace()
        if place:
            return place.getZoneId()
        return None

    def squish(self, damage):
        if self == base.localAvatar:
            base.cr.playGame.getPlace().fsm.request("squished")
            self.stunToon()
            self.setZ(self.getZ(render) + 0.025)

    def d_squish(self, damage):
        self.sendUpdate("squish", [damage])

    def b_squish(self, damage):
        if not self.isStunned:
            self.squish(damage)
            self.d_squish(damage)
            self.playDialogueForString("!")

    def playCurrentDialogue(self, dialogue, chatFlags, interrupt=1):
        if interrupt and self.__currentDialogue is not None:
            self.__currentDialogue.stop()
        self.__currentDialogue = dialogue
        if dialogue:
            base.playSfx(dialogue, node=self)
        elif chatFlags & CFSpeech != 0:
            if self.nametag.getNumChatPages() > 0:
                self.playDialogueForString(self.nametag.getChat())
                if self.soundChatBubble is not None:
                    base.playSfx(self.soundChatBubble, node=self)
            elif self.nametag.getChatStomp() > 0:
                self.playDialogueForString(self.nametag.getStompText(), self.nametag.getStompDelay())

    def setChatAbsolute(self, chatString, chatFlags, dialogue=None, interrupt=1, quiet=0):
        DistributedAvatar.DistributedAvatar.setChatAbsolute(self, chatString, chatFlags, dialogue, interrupt)

    def setChatMuted(self, chatString, chatFlags, dialogue=None, interrupt=1, quiet=0):
        self.nametag.setChat(chatString, chatFlags)
        self.playCurrentDialogue(dialogue, chatFlags - CFSpeech, interrupt)

    def displayTalk(self, chatString, mods=None):
        chatString, flags = base.talkAssistant.parseMessage(chatString)
        self.nametag.setChat(chatString, flags)
        if base.toonChatSounds:
            self.playCurrentDialogue(None, flags, interrupt=1)

    def scrubTalk(self, message, mods):
        return message, 0

    def toonUp(self, hpGained):
        if self.hp is None or hpGained < 0:
            return
        oldHp = self.hp
        if self.hp + hpGained <= 0:
            self.hp += hpGained
        else:
            self.hp = min(max(self.hp, 0) + hpGained, self.maxHp)
        hpGained = self.hp - max(oldHp, 0)
        if hpGained > 0:
            self.showHpText(hpGained)
            self.hpChange(quietly=0)
        return

    def showHpText(self, number, bonus=0, scale=1):
        if self.HpTextEnabled and not self.ghostMode and number != 0:
            if self.hpText:
                self.hideHpText()
            self.HpTextGenerator.setFont(getSignFont())
            if number < 0:
                self.HpTextGenerator.setText(str(number))
            else:
                hpGainedStr = "+" + str(number)
                self.HpTextGenerator.setText(hpGainedStr)
            self.HpTextGenerator.clearShadow()
            self.HpTextGenerator.setAlign(TextNode.ACenter)
            if bonus == 1:
                r = 1.0
                g = 1.0
                b = 0
                a = 1
            elif bonus == 2:
                r = 1.0
                g = 0.5
                b = 0
                a = 1
            elif number < 0:
                r = 0.9
                g = 0
                b = 0
                a = 1
            else:
                r = 0
                g = 0.9
                b = 0
                a = 1
            self.HpTextGenerator.setTextColor(r, g, b, a)
            self.hpTextNode = self.HpTextGenerator.generate()
            self.hpText = self.attachNewNode(self.hpTextNode)
            self.hpText.setScale(scale)
            self.hpText.setBillboardPointEye()
            self.hpText.setBin("fixed", 100)
            self.hpText.setPos(0, 0, self.height / 2)
            self.hpTextSeq = Sequence(
                self.hpText.posInterval(1.0, Point3(0, 0, self.height + 1.5), blendType="easeOut"),
                Wait(0.85),
                self.hpText.colorInterval(0.1, Vec4(r, g, b, 0)),
                Func(self.hideHpText),
            )
            self.hpTextSeq.start()

    def getDialogueArray(self):
        # So we don't get the undefined DistributedAvatar version
        return Toon.Toon.getDialogueArray(self)
