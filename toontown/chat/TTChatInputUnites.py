from toontown.chat import TTSCResistanceTerminal
from toontown.chat.TTChatInputDropdown import TTChatInputDropdown
from toontown.chat.TTSCResistanceMenu import TTSCResistanceMenu
from toontown.toonbase import TTLocalizer


class TTChatInputUnites(TTChatInputDropdown):
    def __init__(self, chatMgr, pos=(0.41, -0.04)):
        super().__init__(chatMgr, pos)

        self.whisperAvatarId = None

        self.createChatMenus()

        def listenForSCEvent(eventBaseName, handler):
            eventName = self.chatPanel.getEventName(eventBaseName)
            self.accept(eventName, handler)

        listenForSCEvent(TTSCResistanceTerminal.TTSCResistanceMsgEvent, self.handleResistanceMsg)

    def delete(self):
        self.ignoreAll()
        self.chatPanel.destroy()
        del self.chatPanel
        del self.fsm
        del self.chatMgr

    def getChatMenuStructure(self):
        return [[TTSCResistanceMenu, TTLocalizer.SCMenuResistance]]

    def show(self, pos=None):
        if pos is not None:
            self.pos = pos
        self.fsm.request("active")

    def handleResistanceMsg(self, textId, prime):
        self.chatMgr.sendSCUnite(textId, prime)
