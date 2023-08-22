from direct.showbase.DirectObject import DirectObject


def isAlphanumeric(value):
    return any(letter in "abcdefghijklmnopqrstuvwxyz" for letter in value.lower().split("-"))


class ControlToken(DirectObject):
    def __init__(self, name, defaultKey):
        self.name = name
        self.listeningTo = None
        self.key = None
        self.active = True
        self.lastMods = False
        self.startAccepting(defaultKey)

    def startAccepting(self, key=None):
        if key is None and self.key is None:
            raise ValueError("Accepting to None is invalid before the token is initialized!")
        if key is None and self.active:
            return
        self.stopAccepting()
        if key is not None:
            self.key = key
        self.accept(self.key, self.emit)
        self.accept(f"{self.key}-up", self.emit, ["up"])
        self.active = True

    @property
    def isAlphanumeric(self):
        return self.key and isAlphanumeric(self.key)

    def stopAccepting(self):
        if self.lastMods is None:
            self.emit("up")
        self.ignoreAll()
        self.active = False

    def emit(self, modifiers=None):
        self.lastMods = modifiers
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

    def __init__(self):
        self.tokens = {}

    @staticmethod
    def getKeyName(name, default):
        controlCategory = base.settings.getOption("controls", {})
        if controlCategory is None:
            controlCategory = {}

        return controlCategory.get(name, default).lower()

    def getKeyToken(self, name, default):
        if name in self.tokens:
            token = self.tokens[name]
            token.startAccepting(self.getKeyName(name, default))
        else:
            token = ControlToken(name, self.getKeyName(name, default))
            self.tokens[name] = token

        return token

    @property
    def chatCanAutoFocus(self):
        controls = base.settings.getOption("controls", {})
        controls = [value for key, value in controls.items() if key != self.chatKeyName]
        return not any(isAlphanumeric(control) for control in controls)

    def disableAlphanumerics(self):
        if self.chatCanAutoFocus:
            return
        for token in self.tokens.values():
            if token.isAlphanumeric:
                token.stopAccepting()

    def enableAlphanumerics(self):
        if self.chatCanAutoFocus:
            return
        for token in self.tokens.values():
            if token.isAlphanumeric:
                token.startAccepting()
