from direct.fsm.FSM import FSM
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import TextNode, Vec4

from toontown.chat import ChatLog
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont


class TTChatInputMenu(FSM, DirectFrame):
    notify = directNotify.newCategory("TTChatInputMenu")
    chatLog = None

    entryWidth = 20
    logLines = 8

    borderWidth = 0.02
    halfIcon = 0.0575

    entryScale = 0.045
    entryBorderWidth = 0.01

    logPadding = 0.005
    logTextScale = 0.04

    centerSpacing = 0.015

    def __init__(self, chatMgr, **kwargs):
        FSM.__init__(self, "TTChatWhiteList")
        DirectFrame.__init__(self, **kwargs)
        self.calculateDimensions()

        self.receiverId = None
        self.activeSubmenu = None
        self.active = False

        self.storedText = ""

        self.chatFrame = DirectFrame(
            parent=self,
            relief=DirectGuiGlobals.RIDGE,
            frameColor=(0.45, 0.45, 0.7, 1),
            borderWidth=(self.borderWidth, self.borderWidth),
            state=DirectGuiGlobals.NORMAL,
        )

        gui = loader.loadModel("phase_3.5/models/gui/chat_input_gui")
        chatButtonImage = (
            gui.find("**/ChtBx_ChtBtn_UP"),
            gui.find("**/ChtBx_ChtBtn_DN"),
            gui.find("**/ChtBx_ChtBtn_RLVR"),
        )

        self.chatLog = ChatLog.ChatLog(chatMgr, self, parent=self.chatFrame)

        self.cancelButton = DirectButton(
            parent=self.chatFrame,
            image=(
                gui.find("**/CloseBtn_UP"),
                gui.find("**/CloseBtn_DN"),
                gui.find("**/CloseBtn_Rllvr"),
            ),
            pos=(self.iconEdgeDist, 0, -self.iconEdgeDist),
            relief=None,
            command=self.cancelButtonPressed,
        )

        self.chatEntry = DirectEntry(
            parent=self.chatFrame,
            relief=DirectGuiGlobals.SUNKEN,
            frameColor=(0.75, 0.75, 0.75, 1.0),
            borderWidth=(self.entryBorderWidth, self.entryBorderWidth),
            entryFont=getInterfaceFont(),
            width=self.entryWidth,
            numLines=1,
            cursorKeys=0,
            backgroundFocus=0,
            suppressMouse=1,
            command=self.sendChat,
            focus=0,
            text="",
            text_shadow=(0.2, 0.2, 0.2, 0.5),
            text_pos=(0, -self.entryHeight + self.entryScale * 0.4 + self.entryBorderWidth),
            text_scale=self.entryScale,
            overflow=1,
            focusInCommand=base.hotkeyManager.disableAlphanumerics,
            focusOutCommand=base.hotkeyManager.enableAlphanumerics,
        )

        self.chatInputUnites = chatMgr.chatInputUnites
        self.uniteButton = DirectButton(
            parent=self.chatFrame,
            image=loader.loadModel("phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist").find("**/*fistIcon*"),
            image_scale=0.179,
            relief=None,
            text=("", TTLocalizer.GlobalUniteName, TTLocalizer.GlobalUniteName, ""),
            text_align=TextNode.ARight,
            text_scale=0.045,
            text_pos=(-(0.06 + self.iconEdgeDist * 0.2), 0.2),
            text_fg=(1, 1, 1, 1),
            text_bg=(0.5, 0.5, 0.5, 0.5),
            text_shadow=(0.1, 0.1, 0.1, 1),
            text_shadowOffset=(0.07, 0.07),
            sortOrder=DirectGuiGlobals.FOREGROUND_SORT_INDEX,
            command=self.uniteButtonPressed,
            clickSound=chatMgr.openScSfx,
        )

        self.chatInputSpeedChat = chatMgr.chatInputSpeedChat
        self.scButton = DirectButton(
            parent=self.chatFrame,
            image=chatButtonImage,
            relief=None,
            image_color=Vec4(0.75, 1, 0.6, 1),
            text=("", TTLocalizer.GlobalSpeedChatName, TTLocalizer.GlobalSpeedChatName),
            text_align=TextNode.ALeft,
            text_scale=0.045,
            text_pos=(0.06 + self.iconEdgeDist * 0.2, 0),
            text_fg=(1, 1, 1, 1),
            text_bg=(0.5, 0.5, 0.5, 0.5),
            text_shadow=(0.1, 0.1, 0.1, 1),
            text_shadowOffset=(0.07, 0.07),
            sortOrder=DirectGuiGlobals.FOREGROUND_SORT_INDEX,
            command=self.scButtonPressed,
            clickSound=chatMgr.openScSfx,
        )

        self.chatButton = DirectButton(
            parent=self.chatFrame, image=chatButtonImage, relief=None, command=self.chatButtonPressed
        )

        self.whisperLabel = DirectLabel(
            parent=self.chatEntry,
            pos=(-0.005, 0, self.entryScale * 0.5),
            relief=DirectGuiGlobals.RAISED,
            frameColor=(0.9, 0.8, 0.2, 1),
            borderWidth=(0.005, 0.005),
            text=TTLocalizer.ChatInputNormalWhisper,
            text_scale=self.entryScale,
            text_align=TextNode.ALeft,
            text_fg=Vec4(0, 0, 0, 1),
            textMayChange=1,
            sortOrder=5,
        )
        self.updateTransforms(True)
        self.acceptInput()
        self.deactivate()

    def activate(self):
        self.chatEntry["focus"] = 1
        self.show()
        self.active = True
        self.checkUniteButton()

        def unfocus():
            self.chatEntry["focus"] = 0

        def focus():
            self.chatEntry["focus"] = 1

        self.accept("mouse1", unfocus)
        self.accept("escape", self.unfocusExit)
        self.accept(base.CHAT, focus)
        self.accept("dropdownClosed", self.hideSubmenu)
        self.accept("resistanceMessagesChanged", self.checkUniteButton)

    def deactivate(self):
        self.chatEntry.set("")
        self.chatEntry["focus"] = 0
        if self.activeSubmenu is not None:
            self.hideSubmenu()
        self.hide()
        self.active = False
        self.ignore("mouse1")
        self.ignore("dropdownClosed")

    def refreshEntry(self):
        self.chatEntry.set("")
        self.chatEntry["focus"] = 1

    def unfocusExit(self):
        if self.chatEntry["focus"] == 1:
            self.chatEntry["focus"] = 0
        else:
            base.localAvatar.chatMgr.fsm.request("mainMenu")

    def acceptInput(self):
        self.chatEntry.bind(DirectGuiGlobals.OVERFLOW, self.chatOverflow)
        self.chatEntry.bind(DirectGuiGlobals.TYPE, self.typeCallback)

    def typeCallback(self, _extraArgs=None):
        messenger.send("wakeup")
        messenger.send("enterWhiteListChat")

    def destroy(self):
        self.chatEntry.unbind(DirectGuiGlobals.OVERFLOW)
        self.chatEntry.unbind(DirectGuiGlobals.TYPE)
        self.chatEntry.unbind(DirectGuiGlobals.ERASE)
        self.chatEntry.destroy()
        self.chatFrame.destroy()
        self.ignoreAll()
        DirectFrame.destroy(self)

    def chatOverflow(self, _overflow):
        self.sendChat()

    def sendChat(self, text=None):
        text = self.chatEntry.get(plain=True)
        base.talkAssistant.sendMessage(text, self.receiverId)
        self.refreshEntry()

    def chatButtonPressed(self):
        self.sendChat()

    def hideSubmenu(self):
        self.activeSubmenu.hide()
        self.activeSubmenu = None

    def scButtonPressed(self):
        if self.activeSubmenu != self.chatInputSpeedChat:
            if self.activeSubmenu is not None:
                self.hideSubmenu()
            self.chatInputSpeedChat.show(
                self.receiverId, pos=(self.iconEdgeDist + 0.065, -self.frameHeight + self.iconEdgeDist + 0.025)
            )
            self.activeSubmenu = self.chatInputSpeedChat
        else:
            self.hideSubmenu()

    def uniteButtonPressed(self):
        if self.activeSubmenu != self.chatInputUnites:
            if self.activeSubmenu is not None:
                self.hideSubmenu()
            self.chatInputUnites.show(pos=(self.frameWidth, -0.045))
            self.activeSubmenu = self.chatInputUnites
        else:
            self.hideSubmenu()

    def cancelButtonPressed(self):
        self.request("Off")
        base.localAvatar.chatMgr.fsm.request("mainMenu")

    def enterAllChat(self):
        self.activate()
        self.whisperLabel.hide()

    def enterAvatarWhisper(self):
        self.storedText = self.chatEntry.get()
        self.activate()
        self.whisperLabel.hide()
        if self.receiverId:
            whisperName = base.talkAssistant.resolveAvatarName(self.receiverId)
            self.whisperLabel["text"] = TTLocalizer.ChatInputWhisperLabel % whisperName
            self.whisperLabel.resetFrameSize()
            self.whisperLabel.show()

    def exitAvatarWhisper(self):
        self.chatEntry.set(self.storedText)
        self.whisperLabel.hide()

    def activateByData(self, receiverId=None):
        self.receiverId = receiverId
        return self.request("AllChat" if not self.receiverId else "AvatarWhisper")

    def checkUniteButton(self):
        if any(base.localAvatar.resistanceMessages):
            self.uniteButton.show()
        else:
            self.uniteButton.hide()

    def calculateDimensions(self):
        self.iconEdgeDist = self.halfIcon + self.borderWidth
        self.centerEdgeDist = self.centerSpacing + self.borderWidth
        self.centerX = self.halfIcon * 2 + self.borderWidth

        self.entryOffset = self.entryBorderWidth + self.entryScale * 0.1
        self.entryHeight = self.entryScale * 1.2 + self.entryBorderWidth * 2

        self.logHeight = self.logLines * self.logTextScale + self.logPadding * 2
        self.logWordwrap = self.entryWidth * self.entryScale / self.logTextScale

        self.centerWidth = self.entryScale * self.entryWidth + self.entryBorderWidth * 2

        self.frameWidth = self.centerWidth + self.centerX * 2
        self.frameHeight = self.logHeight + self.centerSpacing * 3 + self.borderWidth * 2 + self.entryHeight

    def updateTransforms(self, refresh=False):
        self.chatFrame["frameSize"] = (0, self.frameWidth, -self.frameHeight, 0)
        self.chatFrame.resetFrameSize()

        self.chatEntry["frameSize"] = (-self.entryOffset, self.centerWidth - self.entryOffset, -self.entryHeight, 0)
        self.chatEntry.resetFrameSize()
        self.chatEntry.setPos(
            self.centerX + self.entryOffset, 0, -self.frameHeight + self.centerEdgeDist + self.entryHeight
        )

        self.uniteButton.setPos(self.frameWidth - self.iconEdgeDist, 0, -self.iconEdgeDist - 0.2075)
        self.scButton.setPos(self.iconEdgeDist, 0, -self.frameHeight + self.iconEdgeDist)
        self.chatButton.setPos(self.frameWidth - self.iconEdgeDist, 0, -self.frameHeight + self.iconEdgeDist)

        self.chatLog.chatLogNode.setPos(self.centerX, 0, -self.centerEdgeDist)
        self.chatLog.chatLogNode["frameSize"] = (0, self.centerWidth, -self.logHeight, 0)
        self.chatLog.chatLogNode.resetFrameSize()
        if refresh:
            self.chatLog.unload()
            self.chatLog.generateTabs(self, self.chatLog.currentTab)
            self.chatLog.openChatlog()
