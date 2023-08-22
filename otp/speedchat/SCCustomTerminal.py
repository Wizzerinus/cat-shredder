from otp.speedchat.SCTerminal import SCTerminal
from toontown.toonbase import TTLSpeedChat

SCCustomMsgEvent = "SCCustomMsg"


def decodeSCCustomMsg(textId):
    return TTLSpeedChat.CustomSCStrings.get(textId, None)


class SCCustomTerminal(SCTerminal):
    """SCCustomTerminal represents a terminal SpeedChat entry that
    contains a phrase that was purchased from the catalog."""

    def __init__(self, textId):
        SCTerminal.__init__(self)
        self.textId = textId
        self.text = TTLSpeedChat.CustomSCStrings[self.textId]

    def handleSelect(self):
        SCTerminal.handleSelect(self)
        messenger.send(self.getEventName(SCCustomMsgEvent), [self.textId])
