from otp.speedchat.SCTerminal import SCTerminal
from toontown.toonbase import TTLSpeedChat

SCStaticTextMsgEvent = "SCStaticTextMsg"


def decodeSCStaticTextMsg(textId):
    return TTLSpeedChat.SpeedChatStaticText.get(textId, None)


class SCStaticTextTerminal(SCTerminal):
    """SCStaticTextTerminal represents a terminal SpeedChat entry that
    contains a piece of static (never-changing/constant) text.

    When selected, generates a 'SCStaticTextMsg' event, with arguments:
    - textId (16-bit; use as index into OTPLocalizer.SpeedChatStaticText)
    """

    def __init__(self, textId):
        SCTerminal.__init__(self)
        self.textId = textId
        self.text = TTLSpeedChat.SpeedChatStaticText[self.textId]

    def handleSelect(self):
        SCTerminal.handleSelect(self)
        messenger.send(self.getEventName(SCStaticTextMsgEvent), [self.textId])
