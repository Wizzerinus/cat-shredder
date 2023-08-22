from direct.interval.IntervalGlobal import *
from panda3d.core import Point3

from toontown.coghq.cfo import CraneLeagueGlobals
from toontown.coghq.cfo.GeneralCFOGlobals import TreasureModels
from toontown.world import DistributedTreasure


class DistributedCashbotBossTreasure(DistributedTreasure.DistributedTreasure):
    def __init__(self, cr):
        DistributedTreasure.DistributedTreasure.__init__(self, cr)
        self.grabSoundPath = "phase_4/audio/sfx/SZ_DD_treasure.ogg"
        self.boss = None

    def setStyle(self, hoodId):
        newModel = TreasureModels[hoodId]
        if self.modelPath != newModel:
            if self.modelPath:
                self.loadModel(newModel)
            self.modelPath = newModel

    def setGoonId(self, goonId):
        self.goonId = goonId
        # lazy hacks xd set boss reference when we set goon id
        goon = self.cr.doId2do.get(goonId)
        if goon:
            self.boss = goon.boss

    def setFinalPosition(self, x, y, z):
        if not self.nodePath:
            self.makeNodePath()
        if self.treasureFlyTrack:
            self.treasureFlyTrack.finish()
            self.treasureFlyTrack = None
        startPos = None
        goon = self.cr.doId2do[self.goonId]
        if goon:
            startPos = goon.getPos()
        lerpTime = 1
        self.treasureFlyTrack = Sequence(
            Func(self.collNodePath.stash),
            Parallel(
                ProjectileInterval(
                    self.treasure, startPos=Point3(0, 0, 0), endPos=Point3(0, 0, 0), duration=lerpTime, gravityMult=2.0
                ),
                LerpPosInterval(self.nodePath, lerpTime, Point3(x, y, z), startPos=startPos),
            ),
            Func(self.collNodePath.unstash),
        )
        self.treasureFlyTrack.start()

    def deductScoreboardPoints(self, avId, amount):
        if self.boss:
            self.boss.scoreboard.addScore(avId, amount, CraneLeagueGlobals.PENALTY_TREASURE_TEXT)
