import time

from direct.showbase.ShowBase import ShowBase

from toontown.toonbase.globals.TTGlobalsRender import EnviroCameraBitmask, MainCameraBitmask


class OTPBase(ShowBase):
    def __init__(self, windowType=None):
        ShowBase.__init__(self, windowType=windowType)

        self.wantNametags = self.config.GetBool("want-nametags", 1)

        self.slowCloseShard = self.config.GetBool("slow-close-shard", 0)
        self.slowCloseShardDelay = self.config.GetFloat("slow-close-shard-delay", 10.0)

        self.fillShardsToIdealPop = self.config.GetBool("fill-shards-to-ideal-pop", 1)

        self.wantDynamicShadows = 1

        self.stereoEnabled = False
        self.enviroDR = None
        self.enviroCam = None
        self.pixelZoomSetup = False

        self.gameOptionsCode = ""
        self.locationCode = ""
        self.locationCodeChanged = time.time()

        if base.cam:
            base.cam.node().setCameraMask(MainCameraBitmask | EnviroCameraBitmask)

        taskMgr.setupTaskChain("net")
