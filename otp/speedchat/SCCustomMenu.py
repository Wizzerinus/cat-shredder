from otp.speedchat.SCCustomTerminal import SCCustomTerminal
from otp.speedchat.SCMenu import SCMenu
from toontown.toonbase import TTLSpeedChat


class SCCustomMenu(SCMenu):
    """SCCustomMenu represents a menu of SCCustomTerminals."""

    def __init__(self):
        SCMenu.__init__(self)
        self.accept("customMessagesChanged", self.__customMessagesChanged)
        self.__customMessagesChanged()

    def destroy(self):
        SCMenu.destroy(self)

    def __customMessagesChanged(self):
        self.clearMenu()

        lt = base.localAvatar
        if not lt:
            return

        for msgIndex in lt.customMessages:
            if msgIndex in TTLSpeedChat.CustomSCStrings:
                self.append(SCCustomTerminal(msgIndex))
