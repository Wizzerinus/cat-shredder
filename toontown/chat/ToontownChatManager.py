"""ChatManager module: contains the ChatManager class"""
import string

from direct.fsm import ClassicFSM, State
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectCheckButton import DirectCheckButton
from direct.gui.DirectFrame import DirectFrame
from direct.showbase.DirectObject import DirectObject
from panda3d.core import TextNode, Vec4

from toontown.chat.TTChatInputMenu import TTChatInputMenu
from toontown.chat.TTChatInputSpeedChat import TTChatInputSpeedChat
from toontown.chat.TTChatInputUnites import TTChatInputUnites
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals import TTGlobalsChat
from toontown.toonbase.globals.TTGlobalsChat import MagicWordStartSymbols


class HackedDirectRadioButton(DirectCheckButton):
    def __init__(self, parent=None, **kw):
        optiondefs = ()
        self.defineoptions(kw, optiondefs)
        DirectCheckButton.__init__(self, parent)
        self.initialiseoptions(HackedDirectRadioButton)

    def commandFunc(self, event):
        if self["indicatorValue"]:
            self["indicatorValue"] = 0
        DirectCheckButton.commandFunc(self, event)


class ToontownChatManager(DirectObject):
    """
    contains methods for turning chat inputs
    into onscreen thought/word balloons"""

    notify = directNotify.newCategory("ToontownChatManager")
    passwordEntry = None

    def __init__(self, cr, localAvatar):
        gui = loader.loadModel("phase_3.5/models/gui/chat_input_gui")
        chatButtonImage = (
            gui.find("**/ChtBx_ChtBtn_UP").copyTo(hidden),
            gui.find("**/ChtBx_ChtBtn_DN").copyTo(hidden),
            gui.find("**/ChtBx_ChtBtn_RLVR").copyTo(hidden),
        )

        self.openScSfx = loader.loadSfx("phase_3.5/audio/sfx/GUI_quicktalker.ogg")
        self.openScSfx.setVolume(0.8)

        self.normalButton = DirectButton(
            image=chatButtonImage,
            pos=(0.0683, 0, -0.07),
            parent=base.a2dTopLeft,
            scale=1.179,
            relief=None,
            image_color=Vec4(1, 1, 1, 1),
            text=("", TTLocalizer.ChatManagerChat, TTLocalizer.ChatManagerChat),
            text_align=TextNode.ALeft,
            text_scale=0.06,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_pos=(-0.0525, -0.09),
            textMayChange=0,
            sortOrder=DirectGuiGlobals.FOREGROUND_SORT_INDEX,
            command=self.__normalButtonPressed,
            clickSound=self.openScSfx,
        )
        self.scButton = DirectButton(
            image=chatButtonImage,
            pos=(0.2, 0, -0.07),
            parent=base.a2dTopLeft,
            scale=1.179,
            relief=None,
            image_color=Vec4(0.75, 1, 0.6, 1),
            text=("", TTLocalizer.GlobalSpeedChatName, TTLocalizer.GlobalSpeedChatName),
            text_scale=0.06,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_pos=(0, -0.09),
            textMayChange=0,
            sortOrder=DirectGuiGlobals.FOREGROUND_SORT_INDEX,
            command=self.__scButtonPressed,
            clickSound=self.openScSfx,
        )
        self.uniteButton = DirectButton(
            image=loader.loadModel("phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist").find("**/*fistIcon*"),
            pos=(0.3317, 0, -0.275),
            parent=base.a2dTopLeft,
            image_scale=0.179,
            relief=None,
            text=("", TTLocalizer.GlobalUniteName, TTLocalizer.GlobalUniteName, ""),
            text_scale=0.06,
            text_fg=Vec4(1, 1, 1, 1),
            text_shadow=Vec4(0, 0, 0, 1),
            text_pos=(0, 0.09),
            textMayChange=0,
            sortOrder=DirectGuiGlobals.FOREGROUND_SORT_INDEX,
            command=self.__uniteButtonPressed,
            clickSound=self.openScSfx,
        )
        self.unitesActive = True
        self.normalButton.hide()
        self.scButton.hide()
        self.uniteButton.hide()

        self.whisperFrame = DirectFrame(
            parent=base.a2dTopLeft,
            relief=None,
            image=DirectGuiGlobals.getDefaultDialogGeom(),
            image_scale=(0.79, 0.7, 0.2),
            image_color=(1, 1, 0.75, 1),
            pos=(0.4, 0, -0.105),
            text=TTLocalizer.ChatManagerWhisperTo,
            text_wordwrap=6.5,
            text_scale=0.06,
            text_fg=Vec4(0, 0, 0, 1),
            text_pos=(0.18, 0.01),
            textMayChange=1,
            sortOrder=DirectGuiGlobals.FOREGROUND_SORT_INDEX,
        )
        self.whisperFrame.hide()

        self.whisperButton = DirectButton(
            parent=self.whisperFrame,
            image=chatButtonImage,
            pos=(-0.32, 0, 0.032),
            scale=1.179,
            relief=None,
            image_color=Vec4(1, 1, 1, 1),
            text=("", TTLocalizer.ChatManagerChat, TTLocalizer.ChatManagerChat, ""),
            image3_color=Vec4(0.6, 0.6, 0.6, 0.6),
            text_scale=0.05,
            text_fg=(0, 0, 0, 1),
            text_pos=(0, -0.09),
            textMayChange=0,
            command=self.__whisperButtonPressed,
        )

        self.whisperScButton = DirectButton(
            parent=self.whisperFrame,
            image=chatButtonImage,
            pos=(-0.2, 0, 0.032),
            scale=1.179,
            relief=None,
            image_color=Vec4(0.75, 1, 0.6, 1),
            text=("", TTLocalizer.GlobalSpeedChatName, TTLocalizer.GlobalSpeedChatName, ""),
            image3_color=Vec4(0.6, 0.6, 0.6, 0.6),
            text_scale=0.05,
            text_fg=(0, 0, 0, 1),
            text_pos=(0, -0.09),
            textMayChange=0,
            command=self.__whisperScButtonPressed,
        )

        self.whisperCancelButton = DirectButton(
            parent=self.whisperFrame,
            image=(
                gui.find("**/CloseBtn_UP"),
                gui.find("**/CloseBtn_DN"),
                gui.find("**/CloseBtn_Rllvr"),
            ),
            pos=(-0.06, 0, 0.033),
            scale=1.179,
            relief=None,
            text=("", "Cancel", "Cancel"),
            text_scale=0.05,
            text_fg=(0, 0, 0, 1),
            text_pos=(0, -0.09),
            textMayChange=0,
            command=self.__whisperCancelPressed,
        )

        self.chatInputSpeedChat = TTChatInputSpeedChat(self)
        self.chatInputSpeedChat.acceptSCEvents()
        self.chatInputUnites = TTChatInputUnites(self)
        self.chatInputMenu = TTChatInputMenu(self, parent=base.a2dTopLeft)

        self.cr = cr
        self.localAvatar = localAvatar

        self.wantBackgroundFocus = base.hotkeyManager.chatCanAutoFocus

        self.__scObscured = 0
        self.__normalObscured = 0
        self.__uniteObscured = 0

        self.fsm = ClassicFSM.ClassicFSM(
            "chatManager",
            [
                State.State("off", self.enterOff, self.exitOff),
                State.State("mainMenu", self.enterMainMenu, self.exitMainMenu),
                State.State("speedChat", self.enterSpeedChat, self.exitSpeedChat),
                State.State("chatMenu", self.enterChatMenu, self.exitChatMenu),
                State.State("whisper", self.enterWhisper, self.exitWhisper),
                State.State("whisperChat", self.enterWhisperChat, self.exitWhisperChat),
                State.State("whisperSpeedChat", self.enterWhisperSpeedChat, self.exitWhisperSpeedChat),
                State.State("unites", self.enterUnites, self.exitUnites),
            ],
            "off",
            "off",
        )
        self.fsm.enterInitialState()
        self.accept("ReloadControls", self.__reloadControls)
        self.accept("dropdownClosed", self.fsm.request, ["mainMenu"])

    def __reloadControls(self):
        if self.fsm.getCurrentState().getName() != "mainMenu":
            self.wantBackgroundFocus = base.hotkeyManager.chatCanAutoFocus
            self.fsm.request("mainMenu")
        else:
            self.exitMainMenu()
            self.wantBackgroundFocus = base.hotkeyManager.chatCanAutoFocus
            self.enterMainMenu()

    @staticmethod
    def isAlphaNumericHotkey(hotkey):
        hotkey = str(hotkey)
        for prefix in ("shift", "control", "alt"):
            if prefix in hotkey:
                hotkey = hotkey.replace(prefix, "")
                if "-" in hotkey:
                    hotkey = hotkey.replace("-", "")
                else:
                    return False

        if len(hotkey) > 1:
            if hotkey == "space":
                return True
            return False

        characters = string.printable
        if hotkey in characters:
            return True

        return False

    def delete(self):
        self.ignoreAll()
        self.chatInputSpeedChat.delete()
        del self.chatInputSpeedChat

        loader.unloadModel("phase_3.5/models/gui/chat_input_gui")
        self.normalButton.destroy()
        self.scButton.destroy()
        self.whisperFrame.destroy()
        self.whisperButton.destroy()
        self.whisperScButton.destroy()
        self.whisperCancelButton.destroy()
        self.chatInputMenu.destroy()
        if hasattr(self, "uniteButton"):
            self.uniteButton.destroy()
            self.ignore("updateUniteCooldown")

    def obscure(self, normal=None, sc=None, unite=None):
        if normal is not None:
            self.__normalObscured = normal
            if self.__normalObscured:
                self.normalButton.hide()
        if sc is not None:
            self.__scObscured = sc
            if self.__scObscured:
                self.scButton.hide()
        if unite is not None:
            self.__uniteObscured = unite
            if self.__uniteObscured:
                self.uniteButton.hide()

    def isObscured(self):
        return self.__normalObscured, self.__scObscured, self.__uniteObscured

    @staticmethod
    def sendSCUnite(textId, prime):
        """
        Send resistance speedchat message update
        """

        messenger.send("chatUpdateSCResistance", [textId, prime])

    @staticmethod
    def sendSCToontaskChatMessage(taskId, toonProgress, msgIndex):
        """
        Send speedchat message update
        """

        messenger.send("chatUpdateSCToontask", [taskId, toonProgress, msgIndex])

    @staticmethod
    def sendSCToontaskWhisperMessage(taskId, toonProgress, msgIndex, whisperAvatarId):
        """
        Send speedchat message update
        """

        messenger.send("whisperUpdateSCToontask", [taskId, toonProgress, msgIndex, whisperAvatarId])

    def checkBackgroundFocus(self):
        if not self.chatInputMenu.active:
            if self.wantBackgroundFocus:
                self.chatInputMenu.chatEntry["backgroundFocus"] = 1
            self.acceptOnce("enterWhiteListChat", self.fsm.request, ["chatMenu"])

            if not self.wantBackgroundFocus:
                self.accept(base.CHAT, messenger.send, ["enterWhiteListChat"])

    def enterMainMenu(self):
        self.checkObscurred()
        self.checkBackgroundFocus()
        self.checkUniteButton()
        self.accept("resistanceMessagesChanged", self.checkUniteButton)

    def __normalButtonPressed(self):
        """
        The "normal button" is the button in the upper left of the screen
        that is normally used to do free chat.
        """

        messenger.send("wakeup")
        self.fsm.request("chatMenu")

    def __scButtonPressed(self):
        messenger.send("wakeup")
        if self.fsm.getCurrentState().getName() == "speedChat":
            self.fsm.request("mainMenu")
        else:
            self.fsm.request("speedChat")

    def __uniteButtonPressed(self):
        messenger.send("wakeup")
        if self.fsm.getCurrentState().getName() == "unites":
            self.fsm.request("mainMenu")
        else:
            self.fsm.request("unites")

    def __whisperButtonPressed(self, avatarId):
        messenger.send("wakeup")
        if avatarId:
            self.fsm.request("whisperChat", [avatarId])

    def enterChatMenu(self):
        self.hideButtons()
        if base.localAvatar.controlManager.wantWASD:
            base.localAvatar.controlManager.disableWASD()

        result = self.chatInputMenu.activateByData()
        if result is None:
            self.notify.warning("something went wrong in enterWhiteListChat, falling back to main menu")
            self.fsm.request("mainMenu")
        self.ignore("dropdownClosed")

    def exitChatMenu(self):
        if base.localAvatar.controlManager.wantWASD:
            base.localAvatar.controlManager.enableWASD()
        self.chatInputMenu.deactivate()
        self.accept("dropdownClosed", self.fsm.request, ["mainMenu"])

    def enterWhisperChat(self, avatarId):
        self.hideButtons()
        if base.localAvatar.controlManager.wantWASD:
            base.localAvatar.controlManager.disableWASD()

        result = self.chatInputMenu.activateByData(avatarId)
        if result is None:
            self.notify.warning("something went wrong in enterWhisperChat, falling back to main menu")
            self.fsm.request("mainMenu")
        self.ignore("dropdownClosed")

    def exitWhisperChat(self):
        if base.localAvatar.controlManager.wantWASD:
            base.localAvatar.controlManager.enableWASD()
        self.chatInputMenu.deactivate()
        self.accept("dropdownClosed", self.fsm.request, ["mainMenu"])

    def __whisperScButtonPressed(self, avatarName, avatarId):
        messenger.send("wakeup")

        if avatarId:
            if self.fsm.getCurrentState().getName() == "whisperSpeedChat":
                self.fsm.request("whisper", [avatarName, avatarId])
            else:
                self.fsm.request("whisperSpeedChat", [avatarId])

    def __whisperCancelPressed(self):
        self.fsm.request("mainMenu")

    def __handleOpenChatWarningOK(self):
        self.fsm.request("mainMenu")

    def __handleNoSecretChatAtAllOK(self):
        self.fsm.request("mainMenu")

    def __handleNoSecretChatWarningCancel(self):
        self.fsm.request("mainMenu")

    def __handleActivateChatMoreInfo(self):
        self.fsm.request("chatMoreInfo")

    def __handleActivateChatNo(self):
        self.fsm.request("mainMenu")

    def __handleSecretChatActivatedOK(self):
        self.fsm.request("mainMenu")

    def __handleSecretChatActivatedChangeOptions(self):
        self.fsm.request("activateChat")

    def __handleProblemActivatingChatOK(self):
        self.fsm.request("mainMenu")

    def messageSent(self):
        pass

    def deactivateChat(self):
        pass

    def start(self):
        self.fsm.request("mainMenu")
        if not self.wantBackgroundFocus:
            for char in MagicWordStartSymbols:
                self.accept(char, self.__beginMagicWord, [char])

    def __beginMagicWord(self, char):
        self.__normalButtonPressed()
        self.chatInputMenu.chatEntry.set(char)
        self.chatInputMenu.chatEntry.setCursorPosition(1)

    def checkUniteButton(self):
        self.obscure(unite=not (any(base.localAvatar.resistanceMessages)))

    def stop(self):
        self.fsm.request("off")
        self.ignoreAll()

    @staticmethod
    def sendSCChatMessage(msgIndex):
        """
        Send speedchat message update
        """
        base.talkAssistant.sendSCMessage(TTGlobalsChat.SPEEDCHAT_NORMAL, msgIndex)

    @staticmethod
    def sendSCWhisperMessage(msgIndex, whisperAvatarId):
        """
        Send speedchat message update
        """
        base.talkAssistant.sendSCMessage(TTGlobalsChat.SPEEDCHAT_NORMAL, msgIndex, whisperAvatarId)

    @staticmethod
    def sendSCCustomChatMessage(msgIndex):
        """
        Send speedchat message update
        """
        base.talkAssistant.sendSCMessage(TTGlobalsChat.SPEEDCHAT_CUSTOM, msgIndex)

    @staticmethod
    def sendSCCustomWhisperMessage(msgIndex, whisperAvatarId):
        """
        Send speedchat message update
        """
        base.talkAssistant.sendSCMessage(TTGlobalsChat.SPEEDCHAT_CUSTOM, msgIndex, whisperAvatarId)

    @staticmethod
    def sendSCEmoteChatMessage(emoteId):
        """
        Send speedchat message update
        """
        base.talkAssistant.sendSCMessage(TTGlobalsChat.SPEEDCHAT_EMOTE, emoteId)

    @staticmethod
    def sendSCEmoteWhisperMessage(emoteId, whisperAvatarId):
        """
        Send speedchat message update
        """
        base.talkAssistant.sendSCMessage(TTGlobalsChat.SPEEDCHAT_EMOTE, emoteId, whisperAvatarId)

    def enterOff(self):
        self.hideButtons()
        self.ignoreAll()

    def exitOff(self):
        pass

    def checkObscurred(self):
        if not self.__scObscured:
            self.scButton.show()
        if not self.__normalObscured:
            self.normalButton.show()
        if not self.__uniteObscured:
            self.uniteButton.show()

    def exitMainMenu(self):
        self.ignore("enterWhiteListChat")
        if self.wantBackgroundFocus:
            self.chatInputMenu.chatEntry["backgroundFocus"] = 0

    def whisperTo(self, avatarName, avatarId):
        """
        Interface for the outside world to bring up the whisper interface
        for this avatar
        """
        self.fsm.request("whisper", [avatarName, avatarId])

    def noWhisper(self):
        """
        Interface for the outside world to shut down the whisper
        interface if it is up.
        """
        self.fsm.request("mainMenu")

    def enterWhisper(self, avatarName, avatarId):
        self.hideButtons()
        self.whisperScButton["extraArgs"] = [avatarName, avatarId]
        self.whisperButton["extraArgs"] = [avatarId]

        online = 0
        if avatarId in self.cr.doId2do:
            online = 1
        elif self.cr.isFriend(avatarId):
            online = self.cr.isFriendOnline(avatarId)

        chatName = avatarName

        normalButtonObscured, scButtonObscured, clButtonObscured = self.isObscured()

        if online and not normalButtonObscured:
            self.whisperButton["state"] = "normal"
        else:
            self.whisperButton["state"] = "inactive"

        if online:
            self.whisperScButton["state"] = "normal"
            self.changeFrameText(TTLocalizer.ChatManagerWhisperToName % chatName)
        else:
            self.whisperScButton["state"] = "inactive"
            self.changeFrameText(TTLocalizer.ChatManagerWhisperOffline % chatName)

        self.whisperFrame.show()

        if online:
            if self.wantBackgroundFocus:
                self.chatInputMenu.chatEntry["backgroundFocus"] = 1
            self.acceptOnce("enterWhiteListChat", self.fsm.request, ["whisperChat", [avatarId]])

    def changeFrameText(self, newText):
        """
        using this to abstract out the message so
        that other gui structures can be supported
        """
        if len(newText) > 24:
            self.whisperFrame["text_pos"] = (0.18, 0.042)
        self.whisperFrame["text"] = newText

    def exitWhisper(self):
        self.whisperFrame.hide()
        self.ignore("enterWhiteListChat")
        self.chatInputMenu.chatEntry["backgroundFocus"] = 0

    def enterWhisperSpeedChat(self, avatarId):
        self.whisperFrame.show()
        if self.wantBackgroundFocus:
            self.chatInputMenu.chatEntry["backgroundFocus"] = 0
        self.chatInputSpeedChat.show(avatarId, pos=(0.28, -0.04))

    def exitWhisperSpeedChat(self):
        self.whisperFrame.hide()
        self.chatInputSpeedChat.hide()

    def enterSpeedChat(self):
        messenger.send("enterSpeedChat")
        if not self.__scObscured:
            self.scButton.show()
        if not self.__normalObscured:
            self.normalButton.show()
        if self.wantBackgroundFocus:
            self.chatInputMenu.chatEntry["backgroundFocus"] = 0
        self.chatInputSpeedChat.show(pos=(0.28, -0.04))

    def exitSpeedChat(self):
        self.chatInputSpeedChat.hide()

    def enterUnites(self):
        messenger.send("enterSpeedChat")
        if not self.__normalObscured:
            self.normalButton.show()
        if not self.__scObscured:
            self.scButton.show()
        if not self.__uniteObscured:
            self.uniteButton.show()
        if self.wantBackgroundFocus:
            self.chatInputMenu.chatEntry["backgroundFocus"] = 0
        self.chatInputUnites.show()

    def exitUnites(self):
        self.chatInputUnites.hide()

    def setBackgroundFocus(self, backgroundFocus):
        self.wantBackgroundFocus = backgroundFocus

    def hideButtons(self):
        self.scButton.hide()
        self.normalButton.hide()
        self.uniteButton.hide()

    def updateChatMenu(self):
        self.chatInputMenu.refreshMenu()
