from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder
from toontown.chat import ResistanceChat
from .TTSCResistanceTerminal import TTSCResistanceTerminal


class TTSCResistanceMenu(SCMenu):
    def __init__(self):
        SCMenu.__init__(self)
        self.accept("resistanceMessagesChanged", self.__resistanceMessagesChanged)
        self.__resistanceMessagesChanged()

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __resistanceMessagesChanged(self):
        self.clearMenu()
        lt = base.localAvatar
        if not lt:
            return

        for menuIndex in ResistanceChat.resistanceMenu:
            menu = SCMenu()
            for itemIndex in ResistanceChat.getItems(menuIndex):
                textId = ResistanceChat.encodeId(menuIndex, itemIndex)
                charges = lt.getResistanceMessageCharges(textId)
                if charges > 0:
                    menu.append(TTSCResistanceTerminal(textId, charges))

            textId = ResistanceChat.encodeId(menuIndex, 0)
            menuName = ResistanceChat.getMenuName(textId)
            self.append(SCMenuHolder(menuName, menu))
