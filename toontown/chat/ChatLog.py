from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from panda3d.core import CompassEffect, TextNode

from otp.chat.TalkAssistantV2 import ChatMessage
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals.TTGlobalsGUI import getToonFont


class ChatLog(DirectFrame):
    notify = directNotify.newCategory("ChatLog")
    logs = [[] for _ in range(3)]

    def __init__(self, chatMgr, menu, **kwargs):
        self.chatMgr = chatMgr
        circle = loader.loadModel("phase_3.5/models/gui/matching_game_gui").find("**/minnieCircle")
        DirectFrame.__init__(self, relief=None, **kwargs)
        self.initialiseoptions(ChatLog)
        self.logLines = menu.logLines

        self.chatLogNode = DirectButton(
            parent=self,
            relief=DirectGuiGlobals.FLAT,
            frameColor=(0.8, 0.775, 1, 1),
            pressEffect=0,
        )

        buttonRowOffset = -0.07
        self.currentTab = 0
        tabParent = DirectFrame(
            parent=self,
            pos=(menu.iconEdgeDist * 1.2, 0.0, -menu.halfIcon * 2.5 - menu.borderWidth),
        )
        ce = CompassEffect.make(base.aspect2d, CompassEffect.PScale)
        tabParent.setEffect(ce)
        mainTab = DirectButton(
            parent=tabParent,
            relief=None,
            geom=circle,
            geom_scale=0.324562,
            text=("", TTLocalizer.ChatLogTabMain, TTLocalizer.ChatLogTabMain),
            text_align=TextNode.ALeft,
            text_scale=0.045,
            text_pos=(0.06, 0),
            text_fg=(1, 1, 1, 1),
            text_bg=(0.5, 0.5, 0.5, 0.5),
            text_shadow=(0.1, 0.1, 0.1, 1),
            text_shadowOffset=(0.07, 0.07),
            command=self.__toggleButton,
            clickSound=chatMgr.openScSfx,
            extraArgs=[0],
        )
        whisperTab = DirectButton(
            parent=tabParent,
            relief=None,
            geom=circle,
            geom_scale=0.324562,
            text=("", TTLocalizer.ChatLogTabWhispers, TTLocalizer.ChatLogTabWhispers),
            text_align=TextNode.ALeft,
            text_scale=0.045,
            text_pos=(0.06, 0),
            text_fg=(1, 1, 1, 1),
            text_bg=(0.5, 0.5, 0.5, 0.5),
            text_shadow=(0.1, 0.1, 0.1, 1),
            text_shadowOffset=(0.07, 0.07),
            pos=(0.0, 0.0, buttonRowOffset),
            command=self.__toggleButton,
            clickSound=chatMgr.openScSfx,
            extraArgs=[1],
        )
        systemTab = DirectButton(
            parent=tabParent,
            relief=None,
            geom=circle,
            geom_scale=0.324562,
            text=("", TTLocalizer.ChatLogTabSystem, TTLocalizer.ChatLogTabSystem),
            text_align=TextNode.ALeft,
            text_scale=0.045,
            text_pos=(0.06, 0),
            text_fg=(1, 1, 1, 1),
            text_bg=(0.5, 0.5, 0.5, 0.5),
            text_shadow=(0.1, 0.1, 0.1, 1),
            text_shadowOffset=(0.07, 0.07),
            pos=(0.0, 0.0, buttonRowOffset * 2),
            command=self.__toggleButton,
            clickSound=chatMgr.openScSfx,
            extraArgs=[2],
        )

        self.chatTabs = [mainTab, whisperTab, systemTab]
        self.tabIndices = {"main": 0, "whisper": 1, "system": 2}

        self.autoScroll = True
        self.closed = False

        self.generateTabs(menu)

        self.accept("ChatLogMessage", self.__addChatHistory)

        self.chatLogNode.bind(DirectGuiGlobals.WHEELUP, self.__wheel, [-1])
        self.chatLogNode.bind(DirectGuiGlobals.WHEELDOWN, self.__wheel, [1])

    def generateTabs(self, menu, tab=0):
        self.realLogs = []
        self.currents = []
        self.texts = []
        self.textNodes = []
        self.notifications = []

        for x in range(len(self.chatTabs)):
            chatTab = self.chatTabs[x]
            chatTab.wrtReparentTo(self)
            realLog = []
            current = 0
            text = TextNode("text")
            text.setWordwrap(menu.logWordwrap)
            text.setAlign(TextNode.ALeft)
            text.setTextColor(0, 0, 0, 1)
            text.setShadow(0.05, 0.05)
            text.setShadowColor(0.2, 0.2, 0.2, 0.5)
            text.setFont(getToonFont())
            textNode = self.chatLogNode.attachNewNode(text, 0)
            textNode.setPos(menu.logPadding, 0, -menu.logTextScale + menu.logPadding)
            textNode.setScale(menu.logTextScale)
            notificationBubble = DirectFrame(
                chatTab,
                relief=None,
                text="",
                text_scale=0.04,
                text_pos=(-0.00375, -0.0075),
                text_fg=(1, 1, 1, 1),
                text_shadow=(0.1, 0.1, 0.1, 1),
            )
            self.realLogs.append(realLog)
            self.currents.append(current)
            self.texts.append(text)
            self.textNodes.append(textNode)
            self.notifications.append((notificationBubble, 0))

        self.__toggleButton(0)
        self.closeChatlog()
        self.computeRealLog(tab, opening=True)

    def destroy(self):
        self.unload()
        self.ignoreAll()
        DirectButton.destroy(self)

    def unload(self):
        del self.texts
        for textNode in self.textNodes:
            textNode.removeNode()
        del self.textNodes

    def openChatlog(self):
        if not self.closed:
            return
        self.closed = False
        self.show()

    def closeChatlog(self):
        self.closed = True
        self.hide()

    def scrollToCurrent(self, tab):
        minimum = max(0, self.currents[tab] - self.logLines)
        self.texts[tab].setText("\n".join(self.realLogs[tab][minimum : self.currents[tab]]))

    def computeRealLog(self, tab, opening=False, forcePush=False):
        oldText = self.texts[tab].getText()
        self.texts[tab].setText("\n".join(self.logs[tab]))
        self.realLogs[tab] = self.texts[tab].getWordwrappedText().split("\n")
        bubble, notifCount = self.notifications[tab]
        if not opening and not forcePush:
            self.notify.debug(f"forcepush: {forcePush}")
            if tab != self.currentTab:
                notifCount = min(notifCount + 1, 99)
                self.notifications[tab] = (bubble, notifCount)
                bubble.setText(f"{notifCount if notifCount else ''}")

        if self.autoScroll:
            self.currents[tab] = len(self.realLogs[tab])
            self.scrollToCurrent(tab)
        else:
            self.texts[tab].setText(oldText)

    def __addChatHistory(self, chatMessage):
        name, chat = chatMessage.senderName, chatMessage.content
        if chatMessage.messageType == ChatMessage.SYSTEM:
            tab = self.tabIndices["system"]
        elif chatMessage.messageType == ChatMessage.WHISPER:
            tab = self.tabIndices["whisper"]
            receiverName = chatMessage.receiverName
            chat = f"{name} > {receiverName}: {chat}"
        else:
            tab = self.tabIndices["main"]
            chat = f"{name}: {chat}" if name is not None else chat

        self.logs[tab].append(chat)
        self.logs[tab] = self.logs[tab][-250:]
        self.computeRealLog(tab)

    def __wheel(self, amount, bind=None):
        oldCurrent = self.currents[self.currentTab]
        minimum = min(self.logLines, len(self.realLogs[self.currentTab]))
        self.currents[self.currentTab] += amount
        self.autoScroll = self.currents[self.currentTab] >= len(self.realLogs[self.currentTab])

        if self.autoScroll:
            self.currents[self.currentTab] = len(self.realLogs[self.currentTab])
        if self.currents[self.currentTab] < minimum:
            self.currents[self.currentTab] = minimum

        if oldCurrent != self.currents[self.currentTab]:
            self.scrollToCurrent(self.currentTab)

    def __toggleButton(self, index):
        self.currentTab = index
        for tab, text in zip(self.chatTabs, self.textNodes):
            tab.setColor(0.9, 0.3, 0.4, 1)
            text.hide()
        self.chatTabs[index].setColor(0.6, 0.2, 0.35, 1)
        self.textNodes[index].show()
        self.scrollToCurrent(index)
        bubble, notifCount = self.notifications[index]
        bubble.setText(f"{notifCount if notifCount else ''}")
