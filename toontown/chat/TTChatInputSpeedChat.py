from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *

from otp.speedchat import SpeedChatGlobals
from otp.speedchat.SCCustomMenu import SCCustomMenu
from otp.speedchat.SCEmoteMenu import SCEmoteMenu
from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from toontown.chat.TTChatInputDropdown import TTChatInputDropdown
from toontown.toonbase import TTLSpeedChat, TTLocalizer
from toontown.toonbase.globals.TTGlobalsChat import Emotes

scStructure = [
    [
        TTLSpeedChat.SCMenuHello,
        (100, Emotes.WAVE),
        (101, Emotes.WAVE),
        (102, Emotes.WAVE),
        (103, Emotes.WAVE),
        (104, Emotes.WAVE),
        (105, Emotes.WAVE),
        106,
        107,
        108,
        109,
    ],
    [
        TTLSpeedChat.SCMenuBye,
        (120, Emotes.WAVE),
        (121, Emotes.WAVE),
        (122, Emotes.WAVE),
        123,
        124,
        125,
        126,
        127,
        128,
        129,
    ],
    [
        TTLSpeedChat.SCMenuHappy,
        130,
        (131, Emotes.HAPPY),
        (132, Emotes.HAPPY),
        (133, Emotes.HAPPY),
        (134, Emotes.HAPPY),
        (135, Emotes.HAPPY),
        (136, Emotes.HAPPY),
        (137, Emotes.LAUGH),
        (138, Emotes.LAUGH),
        140,
        141,
        142,
        139,
        143,
        144,
        145,
        146,
    ],
    [
        TTLSpeedChat.SCMenuSad,
        (150, Emotes.SAD),
        (151, Emotes.SAD),
        (152, Emotes.SAD),
        153,
        154,
        155,
        156,
        157,
        158,
        159,
    ],
    [
        TTLSpeedChat.SCMenuFriendly,
        [TTLSpeedChat.SCMenuFriendlyCompliment, 180, 181, 182, 183, 184, 185],
        [TTLSpeedChat.SCMenuFriendlyOutfit, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199],
        [TTLSpeedChat.SCMenuFriendlyHelp, 170, 171, 172, 173, 174, 175],
        160,
        161,
        162,
        163,
        164,
        165,
        166,
        167,
        168,
        169,
    ],
    [
        TTLSpeedChat.SCMenuSorry,
        [
            TTLSpeedChat.SCMenuSorryImBusy,
            220,
        ],
        210,
        211,
        212,
        213,
        214,
        216,
        217,
        (218, Emotes.SHRUG),
        219,
    ],
    [
        TTLSpeedChat.SCMenuStinky,
        (230, Emotes.ANGRY),
        (231, Emotes.ANGRY),
        232,
        233,
        234,
        235,
        (236, Emotes.ANGRY),
        237,
    ],
    [TTLSpeedChat.SCMenuTesting, 240, 241, 242, 243, 244, 245],
    [
        TTLSpeedChat.SCMenuPlaces,
        [
            TTLSpeedChat.SCMenuPlacesCogHQ,
            281,
            293,
            294,
            5142,
        ],
        [TTLSpeedChat.SCMenuPlacesWait, 310, 311, 312, 313, 314, 315, 316],
        250,
        251,
        252,
        253,
        254,
        255,
        256,
        257,
        258,
        259,
    ],
    (1, Emotes.YES),  # Yes
    (2, Emotes.NO),  # No
    3,  # Ok
    4,  # Me too
]

cfoMenuStructure = [
    [TTLSpeedChat.SCMenuCFOBattleCranes, 2100, 2101, 2102, 2103, 2104, 2105, 2106, 2107, 2108, 2109, 2110],
    [TTLSpeedChat.SCMenuCFOBattleGoons, 2120, 2121, 2122, 2123, 2124, 2125, 2126],
    2130,
    2131,
    2132,
    2133,
    1410,
]


class TTChatInputSpeedChat(TTChatInputDropdown):
    """TTChatInputSpeedChat class: controls the SpeedChat, and generates
    SpeedChat messages"""

    def __init__(self, chatMgr, pos=(0.28, -0.04)):
        super().__init__(chatMgr, pos)

        self.whisperAvatarId = None

        buttons = loader.loadModel("phase_3/models/gui/dialog_box_buttons_gui")
        okButtonImage = (
            buttons.find("**/ChtBx_OKBtn_UP"),
            buttons.find("**/ChtBx_OKBtn_DN"),
            buttons.find("**/ChtBx_OKBtn_Rllvr"),
        )
        self.emoteNoAccessPanel = DirectFrame(
            parent=hidden,
            relief=None,
            state="normal",
            text=TTLocalizer.SCEmoteNoAccessMsg,
            frameSize=(-1, 1, -1, 1),
            geom=DirectGuiGlobals.getDefaultDialogGeom(),
            geom_color=(1, 1, 0.75, 1),
            geom_scale=(0.92, 1, 0.6),
            geom_pos=(0, 0, -0.08),
            text_scale=0.08,
        )
        self.okButton = DirectButton(
            parent=self.emoteNoAccessPanel,
            image=okButtonImage,
            relief=None,
            text="OK",
            text_scale=0.05,
            text_pos=(0.0, -0.1),
            textMayChange=0,
            pos=(0.0, 0.0, -0.2),
            command=self.handleEmoteNoAccessDone,
        )

        self.createChatMenus()
        self.kartRacingMenu = None
        self.cogMenu = None
        self.cfoMenu = None
        self.cjMenu = None
        self.ceoMenu = None
        self.golfMenu = None

    def delete(self):
        self.ignoreAll()
        self.okButton.destroy()
        self.emoteNoAccessPanel.destroy()
        del self.emoteNoAccessPanel
        self.chatPanel.destroy()
        del self.chatPanel
        del self.fsm
        del self.chatMgr

    def acceptSCEvents(self):
        def listenForSCEvent(eventBaseName, handler):
            eventName = self.chatPanel.getEventName(eventBaseName)
            self.accept(eventName, handler)

        listenForSCEvent(SpeedChatGlobals.SCTerminalLinkedEmoteEvent, self.handleLinkedEmote)
        listenForSCEvent(SpeedChatGlobals.SCStaticTextMsgEvent, self.handleStaticTextMsg)
        listenForSCEvent(SpeedChatGlobals.SCCustomMsgEvent, self.handleCustomMsg)
        listenForSCEvent(SpeedChatGlobals.SCEmoteMsgEvent, self.handleEmoteMsg)
        listenForSCEvent(SpeedChatGlobals.SCEmoteNoAccessEvent, self.handleEmoteNoAccess)

    def show(self, whisperAvatarId=None, pos=None):
        self.whisperAvatarId = whisperAvatarId
        if pos is not None:
            self.pos = pos
        self.fsm.request("active")

    def hide(self):
        self.fsm.request("off")

    def getChatMenuStructure(self):
        structure = []
        structure.append([SCEmoteMenu, TTLocalizer.SCMenuEmotions])
        structure.append([SCCustomMenu, TTLocalizer.SCMenuCustom])
        structure += scStructure
        return structure

    def exitActive(self):
        super().exitActive()
        self.emoteNoAccessPanel.reparentTo(hidden)

    def handleLinkedEmote(self, emoteId):
        if self.whisperAvatarId is None:
            lt = base.localAvatar
            lt.b_setEmoteState(emoteId, animMultiplier=lt.animMultiplier)

    def handleStaticTextMsg(self, textId):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCChatMessage(textId)
        else:
            self.chatMgr.sendSCWhisperMessage(textId, self.whisperAvatarId)

    def handleCustomMsg(self, textId):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCCustomChatMessage(textId)
        else:
            self.chatMgr.sendSCCustomWhisperMessage(textId, self.whisperAvatarId)

    def handleEmoteMsg(self, emoteId):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCEmoteChatMessage(emoteId)
        else:
            self.chatMgr.sendSCEmoteWhisperMessage(emoteId, self.whisperAvatarId)

    def handleEmoteNoAccess(self):
        if self.whisperAvatarId is None:
            self.emoteNoAccessPanel.setPos(0, 0, 0)
        else:
            self.emoteNoAccessPanel.setPos(0.37, 0, 0)
        self.emoteNoAccessPanel.reparentTo(aspect2d)

    def handleEmoteNoAccessDone(self):
        self.emoteNoAccessPanel.reparentTo(hidden)

    def handleToontaskMsg(self, taskId, toonProgress, msgIndex):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCToontaskChatMessage(taskId, toonProgress, msgIndex)
        else:
            self.chatMgr.sendSCToontaskWhisperMessage(taskId, toonProgress, msgIndex, self.whisperAvatarId)

    def addCFOMenu(self):
        if self.cfoMenu is None:
            menu = SCMenu()
            menu.rebuildFromStructure(cfoMenuStructure)
            self.cfoMenu = SCMenuHolder(TTLSpeedChat.SCMenuCFOBattle, menu=menu)
            self.chatPanel[2:2] = [self.cfoMenu]

    def removeCFOMenu(self):
        if self.cfoMenu:
            i = self.chatPanel.index(self.cfoMenu)
            del self.chatPanel[i]
            self.cfoMenu.destroy()
            self.cfoMenu = None
