import json
import os

from panda3d.core import *


class Settings(object):
    notify = directNotify.newCategory("Settings")

    def __init__(self, fileName="user/settings.json"):
        self.fileName = fileName
        if os.path.dirname(self.fileName) and not os.path.exists(os.path.dirname(self.fileName)):
            os.makedirs(os.path.dirname(self.fileName))
        try:
            with open(self.fileName, "r") as f:
                self.settings = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.settings = {}

    def getOption(self, attribute, default):
        return self.settings.get(attribute, default)

    def getFloat(self, attribute, default=1):
        value = self.getOption(attribute, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def getBool(self, attribute, default=False):
        value = self.getOption(attribute, default)
        return bool(value)

    def getInt(self, attribute, default=0):
        value = self.getOption(attribute, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def getList(self, attribute, default=(), expectedLength=None):
        value = self.getOption(attribute, default)
        if isinstance(value, list) and (len(value) == expectedLength or expectedLength is None):
            return value

        return default

    def doSavedSettingsExist(self):
        return os.path.exists(self.fileName)

    def writeSettings(self):
        with open(self.fileName, "w+") as f:
            json.dump(self.settings, f, indent=4)

    def updateSetting(self, attribute, value):
        self.settings[attribute] = value
        self.writeSettings()

    def loadFromSettings(self):
        stretchedScreen = self.getBool("stretched-screen", False)
        if stretchedScreen:
            loadPrcFileData("toonBase Settings Stretched Screen", "aspect-ratio 1.333")
        else:
            self.updateSetting("stretched-screen", stretchedScreen)
