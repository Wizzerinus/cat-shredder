from toontown.toonbase.globals.TTGlobalsRender import *
from toontown.world.coghq import CashbotCogHQLoader
from toontown.world.coghq import CogHood


class CashbotHQ(CogHood.CogHood):
    notify = directNotify.newCategory("CashbotHQ")

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        CogHood.CogHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.cogHQLoaderClass = CashbotCogHQLoader.CashbotCogHQLoader
        self.storageDNAFile = None

        self.skyFile = "phase_3.5/models/props/TT_sky"

        self.titleColor = (0.5, 0.5, 0.5, 1.0)

    def load(self):
        CogHood.CogHood.load(self)
        self.parentFSM.getStateNamed("CashbotHQ").addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed("CashbotHQ").removeChild(self.fsm)
        del self.cogHQLoaderClass
        CogHood.CogHood.unload(self)

    def enter(self, *args):
        CogHood.CogHood.enter(self, *args)
        base.localAvatar.setCameraFov(CogHQCameraFov)
        base.camLens.setNearFar(CashbotHQCameraNear, CashbotHQCameraFar)

    def exit(self):
        base.localAvatar.setCameraFov(DefaultCameraFov / (4.0 / 3.0))
        base.camLens.setNearFar(DefaultCameraNear, DefaultCameraFar)
        CogHood.CogHood.exit(self)

    def spawnTitleText(self, zoneId, floorNum=None):
        CogHood.CogHood.spawnTitleText(self, zoneId)
