from . import ZoneUtil


class HoodDataAI:
    """

    A HoodDataAI object is created for each neighborhood; it owns the
    pointers to objects such as the suit planners and building
    managers, and can shut itself down cleanly on demand.

    """

    notify = directNotify.newCategory("HoodDataAI")

    def __init__(self, air, zoneId):
        self.air = air
        self.zoneId = zoneId
        self.treasurePlanner = None
        self.buildingManagers = []
        self.suitPlanners = []
        self.doId2do = {}

        self.replacementHood = None
        self.redirectingToMe = []
        self.hoodPopulation = 0
        self.pgPopulation = 0

    def startup(self):
        pass

    def shutdown(self):
        self.setRedirect(None)

        if self.treasurePlanner:
            self.treasurePlanner.stop()
            self.treasurePlanner.deleteAllTreasuresNow()
            self.treasurePlanner = None

        for suitPlanner in self.suitPlanners:
            suitPlanner.requestDelete()
            del self.air.suitPlanners[suitPlanner.zoneId]
        self.suitPlanners = []

        for buildingManager in self.buildingManagers:
            buildingManager.cleanup()
            del self.air.buildingManagers[buildingManager.branchID]
        self.buildingManagers = []

        for distObj in list(self.doId2do.values()):
            distObj.requestDelete()
        del self.doId2do

        del self.air

    def addDistObj(self, distObj):
        self.doId2do[distObj.doId] = distObj

    def removeDistObj(self, distObj):
        del self.doId2do[distObj.doId]

    def setRedirect(self, replacementHood):
        if self.replacementHood:
            self.replacementHood[0].redirectingToMe.remove(self)
        self.replacementHood = replacementHood
        if self.replacementHood:
            self.replacementHood[0].redirectingToMe.append(self)

    def hasRedirect(self):
        return self.replacementHood != None

    def getRedirect(self):
        if self.replacementHood == None:
            return self
        else:
            return self.replacementHood[0].getRedirect()

    def incrementPopulation(self, zoneId, increment):
        self.hoodPopulation += increment
        if ZoneUtil.isPlayground(zoneId):
            self.pgPopulation += increment

    def getHoodPopulation(self):
        population = self.hoodPopulation
        for hood in self.redirectingToMe:
            population += hood.getHoodPopulation()
        return population

    def getPgPopulation(self):
        population = self.pgPopulation
        for pg in self.redirectingToMe:
            population += pg.getPgPopulation()
        return population
