from direct.gui import DirectGui
from pandac.PandaModules import DecalEffect

from toontown.toonbase.globals.TTGlobalsGUI import getSuitFont
from toontown.toonbase.globals.TTGlobalsWorld import ZoneIDs
from toontown.world.coghq import CashbotHQExterior, CogHQLoader


class CashbotCogHQLoader(CogHQLoader.CogHQLoader):
    notify = directNotify.newCategory("CashbotCogHQLoader")

    def __init__(self, hood, parentFSMState, doneEvent):
        CogHQLoader.CogHQLoader.__init__(self, hood, parentFSMState, doneEvent)
        self.musicFile = "phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg"

        self.cogHQExteriorModelPath = "phase_10/models/cogHQ/CashBotShippingStation"
        self.cogHQLobbyModelPath = "phase_10/models/cogHQ/VaultLobby"
        self.geom = None

    def unloadPlaceGeom(self):
        if self.geom:
            self.geom.removeNode()
            self.geom = None
        CogHQLoader.CogHQLoader.unloadPlaceGeom(self)

    def loadPlaceGeom(self, zoneId):
        self.notify.info("loadPlaceGeom: %s" % zoneId)

        zoneId = zoneId - (zoneId % 100)

        if zoneId == ZoneIDs.CashbotHQ:
            self.geom = loader.loadModel(self.cogHQExteriorModelPath)

            locator = self.geom.find("**/sign_origin")
            backgroundGeom = self.geom.find("**/EntranceFrameFront")
            backgroundGeom.node().setEffect(DecalEffect.make())
            signText = DirectGui.OnscreenText(
                text="To Nowhere",
                font=getSuitFont(),
                scale=3,
                fg=(0.87, 0.87, 0.87, 1),
                mayChange=False,
                parent=backgroundGeom,
            )
            signText.setPosHpr(locator, 0, 0, 0, 0, 0, 0)
            signText.setDepthWrite(0)

        elif zoneId == ZoneIDs.CashbotHQLobby:
            self.geom = loader.loadModel(self.cogHQLobbyModelPath)

        else:
            self.notify.warning("loadPlaceGeom: unclassified zone %s" % zoneId)

        CogHQLoader.CogHQLoader.loadPlaceGeom(self, zoneId)

    def getExteriorPlaceClass(self):
        return CashbotHQExterior.CashbotHQExterior

    def getBossPlaceClass(self):
        from toontown.world.coghq import CashbotHQBossBattle

        return CashbotHQBossBattle.CashbotHQBossBattle
