from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

from toontown.toonbase.PropPool import globalPropPool


class DustCloud(NodePath):
    dustCloudCount = 0
    sounds = {}

    notify = directNotify.newCategory("DustCloud")

    def __init__(self, parent=hidden, fBillboard=1, wantSound=0):
        """__init()"""
        NodePath.__init__(self)
        self.assign(globalPropPool.getProp("suit_explosion_dust"))
        if fBillboard:
            self.setBillboardAxis()
        self.reparentTo(parent)
        self.seqNode = self.find("**/+SequenceNode").node()
        self.seqNode.setFrameRate(0)
        self.wantSound = wantSound
        if self.wantSound and not DustCloud.sounds:
            DustCloud.sound = loader.loadSfx("phase_4/audio/sfx/firework_distance_02.ogg")
        self.track = None
        self.trackId = DustCloud.dustCloudCount
        DustCloud.dustCloudCount += 1
        self.setBin("fixed", 100, 1)
        self.hide()

    def createTrack(self, rate=24):
        def getSoundFuncIfAble():
            sound = DustCloud.sound
            if self.wantSound and sound:
                return sound.play
            else:

                def dummy():
                    pass

                return dummy

        tflipDuration = self.seqNode.getNumChildren() / (float(rate))
        self.track = Sequence(
            Func(self.show),
            Func(self.messaging),
            Func(self.seqNode.play, 0, self.seqNode.getNumFrames() - 1),
            Func(self.seqNode.setFrameRate, rate),
            Func(getSoundFuncIfAble()),
            Wait(tflipDuration),
            Func(self.seqNode.setFrameRate, 0),
            Func(self.hide),
            name="dustCloud-track-%d" % self.trackId,
        )

    def messaging(self):
        self.notify.debug("CREATING TRACK ID: %s" % self.trackId)

    def play(self, rate=24):
        self.stop()
        self.createTrack(rate)
        self.track.start()

    def loop(self, rate=24):
        self.stop()
        self.createTrack(rate)
        self.track.loop()

    def stop(self):
        if self.track:
            self.track.finish()

    def destroy(self):
        self.notify.debug("DESTROYING TRACK ID: %s" % self.trackId)
        self.stop()
        del self.track
        del self.seqNode
        self.removeNode()
