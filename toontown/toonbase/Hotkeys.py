from direct.showbase.DirectObject import DirectObject


class ControlToken(DirectObject):
    def __init__(self, name, defaultKey):
        self.name = name
        self.listeningTo = None
        self.startAccepting(defaultKey)

    def startAccepting(self, key):
        self.stopAccepting()
        self.listeningTo = {key, f"{key}-up"}
        self.accept(key, self.emit)
        self.accept(f"{key}-up", self.emit, ["up"])

    def stopAccepting(self):
        if self.listeningTo:
            for key in self.listeningTo:
                self.ignore(key)

    def emit(self, modifiers=None):
        if modifiers:
            messenger.send(f"{self.event}-{modifiers}")
        else:
            messenger.send(self.event)

    def destroy(self):
        self.stopAccepting()

    @property
    def event(self):
        return f"ct:{self.name}"


class HotkeyManager:
    notify = directNotify.getCategory("HotkeyManager")
    chatKeyName = "open_chat"

    def getKeyName(self, name, default):
        controlCategory = base.settings.getOption("controls", {})
        if controlCategory is None:
            controlCategory = {}

        return controlCategory.get(name, default).lower()

    def getKeyToken(self, name, default):
        return ControlToken(name, self.getKeyName(name, default))

    @property
    def chatCanAutoFocus(self):
        controls = base.settings.getOption("controls", {})
        controls = [value for key, value in controls if key != self.chatKeyName]
        return not any(self.isAlphanumeric(control) for control in controls)

    @staticmethod
    def isAlphanumeric(value):
        return any(letter in "abcdefghijklmnopqrstuvwxyz" for letter in value.lower().split("-"))
