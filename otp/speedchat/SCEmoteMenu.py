from otp.speedchat.SCEmoteTerminal import SCEmoteTerminal
from otp.speedchat.SCMenu import SCMenu
from toontown.toonbase.globals.TTGlobalsChat import EmoteDict


class SCEmoteMenu(SCMenu):
    """SCEmoteMenu represents a menu of SCEmoteTerminals."""

    def __init__(self):
        SCMenu.__init__(self)
        self.accept("emotesChanged", self.__emoteAccessChanged)
        self.__emoteAccessChanged()

    def destroy(self):
        SCMenu.destroy(self)

    def __emoteAccessChanged(self):
        self.clearMenu()

        lt = base.localAvatar
        if not lt:
            return

        for i in lt.emoteAccess:
            if i in EmoteDict:
                self.append(SCEmoteTerminal(i))
