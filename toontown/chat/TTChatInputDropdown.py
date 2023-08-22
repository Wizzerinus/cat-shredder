from direct.fsm import ClassicFSM, State
from direct.gui import DirectGuiGlobals
from direct.showbase.DirectObject import DirectObject

from otp.speedchat import SpeedChatGlobals
from otp.speedchat.SCColorScheme import SCColorScheme
from otp.speedchat.SpeedChat import SpeedChat


class TTChatInputDropdown(DirectObject):
    DefaultSCColorScheme = SCColorScheme()

    def __init__(self, chatMgr, pos):
        self.chatMgr = chatMgr
        self.pos = pos

        self.fsm = ClassicFSM.ClassicFSM(
            "SpeedChat",
            [
                State.State("off", None, None, ["active"]),
                State.State("active", self.enterActive, self.exitActive, ["off"]),
            ],
            "off",
            "off",
        )
        self.fsm.enterInitialState()

    def show(self, whisperAvatarId=None):
        self.whisperAvatarId = whisperAvatarId
        self.fsm.request("active")

    def hide(self):
        self.fsm.request("off")

    def createChatMenus(self):
        structure = self.getChatMenuStructure()
        self.createChatMenuObject(structure)

    def getChatMenuStructure(self):
        return []

    def createChatMenuObject(self, structure):
        if hasattr(self, "speedChat"):
            self.speedChat.exit()
            self.speedChat.destroy()
            del self.speedChat

        self.chatPanel = SpeedChat(
            structure=structure,
            backgroundModelName="phase_3/models/gui/ChatPanel",
            guiModelName="phase_3.5/models/gui/speedChatGui",
        )
        self.chatPanel.setScale(0.055)
        self.chatPanel.setBin("gui-popup", 0)
        self.chatPanel.setTopLevelOverlap(0)
        self.chatPanel.setColorScheme(self.DefaultSCColorScheme)
        self.chatPanel.finalizeAll()

    def enterActive(self):
        def handleCancel():
            messenger.send("dropdownClosed")

        self.accept("mouse1", handleCancel)

        def selectionMade():
            messenger.send("dropdownClosed")

        self.terminalSelectedEvent = self.chatPanel.getEventName(SpeedChatGlobals.SCTerminalSelectedEvent)
        self.accept(self.terminalSelectedEvent, selectionMade)

        self.chatPanel.reparentTo(base.a2dpTopLeft, DirectGuiGlobals.FOREGROUND_SORT_INDEX)
        self.chatPanel.setPos(self.pos[0], 0, self.pos[1])
        self.chatPanel.setWhisperMode(self.whisperAvatarId is not None)
        self.chatPanel.enter()

    def exitActive(self):
        self.ignore("mouse1")
        self.ignore(self.terminalSelectedEvent)

        self.chatPanel.exit()
        self.chatPanel.reparentTo(hidden)
