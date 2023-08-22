from direct.gui import DirectGuiGlobals
from panda3d.core import TextNode

from otp.avatar import Emote
from otp.speedchat.SCTerminal import SCTerminal
from toontown.toonbase.globals.TTGlobalsChat import EmoteDict, EmoteWhispers

SCEmoteMsgEvent = "SCEmoteMsg"
SCEmoteNoAccessEvent = "SCEmoteNoAccess"


def decodeSCEmoteWhisperMsg(emoteId, avName):
    if emoteId >= len(EmoteWhispers):
        return None
    return EmoteWhispers[emoteId] % avName


class SCEmoteTerminal(SCTerminal):
    """SCEmoteTerminal represents a terminal SpeedChat node that
    contains an emotion."""

    def __init__(self, emoteId):
        SCTerminal.__init__(self)
        self.emoteId = emoteId
        if not self.__ltHasAccess():
            self.text = "?"
        else:
            self.text = EmoteDict[self.emoteId]

    def __ltHasAccess(self):
        if base.localAvatar:
            return self.emoteId in base.localAvatar.emoteAccess

        return 0

    def __emoteEnabled(self):
        if self.isWhispering():
            return 1
        assert Emote.globalEmote is not None
        return Emote.globalEmote.isEnabled(self.emoteId)

    def finalize(self, dbArgs=None):
        if dbArgs is None:
            dbArgs = {}
        if not self.isDirty():
            return

        args = {}

        if (not self.__ltHasAccess()) or (not self.__emoteEnabled()):
            args.update(
                {
                    "rolloverColor": (0, 0, 0, 0),
                    "pressedColor": (0, 0, 0, 0),
                    "rolloverSound": None,
                    "text_fg": (*self.getColorScheme().getTextDisabledColor(), 1),
                }
            )
        if not self.__ltHasAccess():
            args.update(
                {
                    "text_align": TextNode.ACenter,
                }
            )
        elif not self.__emoteEnabled():
            args.update(
                {
                    "clickSound": None,
                }
            )

        self.lastEmoteEnableState = self.__emoteEnabled()

        args.update(dbArgs)
        SCTerminal.finalize(self, dbArgs=args)

    def __emoteEnableStateChanged(self):
        if self.isDirty():
            self.notify.info("skipping __emoteEnableStateChanged; we're marked as dirty")
            return
        if not hasattr(self, "button"):
            raise RuntimeError("SCEmoteTerminal is not marked as dirty, but has no button!")

        btn = self.button
        if self.__emoteEnabled():
            rolloverColor = (*self.getColorScheme().getRolloverColor(), 1)
            pressedColor = (*self.getColorScheme().getPressedColor(), 1)
            btn.frameStyle[DirectGuiGlobals.BUTTON_ROLLOVER_STATE].setColor(*rolloverColor)
            btn.frameStyle[DirectGuiGlobals.BUTTON_DEPRESSED_STATE].setColor(*pressedColor)
            btn.updateFrameStyle()
            btn["text_fg"] = (*self.getColorScheme().getTextColor(), 1)
            btn["rolloverSound"] = DirectGuiGlobals.getDefaultRolloverSound()
            btn["clickSound"] = DirectGuiGlobals.getDefaultClickSound()
        else:
            btn.frameStyle[DirectGuiGlobals.BUTTON_ROLLOVER_STATE].setColor(0, 0, 0, 0)
            btn.frameStyle[DirectGuiGlobals.BUTTON_DEPRESSED_STATE].setColor(0, 0, 0, 0)
            btn.updateFrameStyle()
            btn["text_fg"] = (*self.getColorScheme().getTextDisabledColor(), 1)
            btn["rolloverSound"] = None
            btn["clickSound"] = None

    def enterVisible(self):
        SCTerminal.enterVisible(self)
        if self.__ltHasAccess():
            if hasattr(self, "lastEmoteEnableState") and self.lastEmoteEnableState != self.__emoteEnabled():
                self.invalidate()

            if not self.isWhispering():
                self.accept(Emote.globalEmote.EmoteEnableStateChanged, self.__emoteEnableStateChanged)

    def exitVisible(self):
        SCTerminal.exitVisible(self)
        self.ignore(Emote.globalEmote.EmoteEnableStateChanged)

    def handleSelect(self):
        if not self.__ltHasAccess():
            messenger.send(self.getEventName(SCEmoteNoAccessEvent))
        elif self.__emoteEnabled():
            SCTerminal.handleSelect(self)
            messenger.send(self.getEventName(SCEmoteMsgEvent), [self.emoteId])
