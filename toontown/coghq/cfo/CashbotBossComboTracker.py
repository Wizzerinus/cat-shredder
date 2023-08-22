import math


class CashbotBossComboTracker:
    def __init__(self, boss, avId):
        self.boss = boss
        self.avId = avId
        self.combo = 0
        self.pointBonus = 0

    def __getTaskName(self):
        return "cashbotBossComboTrackerTask" + str(self.avId)

    def __expireComboLater(self):
        taskMgr.remove(self.__getTaskName())  # cancel the task if it already exists
        taskMgr.doMethodLater(self.boss.ruleset.COMBO_DURATION, self.__expireCombo, self.__getTaskName())

    def __expireCombo(self, task):
        if self.combo >= 2:
            self.__awardCombo()
        else:
            self.resetCombo()

    def incrementCombo(self, amount):
        amount = round(amount)
        self.combo += 1
        self.pointBonus += amount
        self.__expireComboLater()
        self.boss.d_updateCombo(self.avId, self.combo)

    def resetCombo(self):
        taskMgr.remove(self.__getTaskName())
        self.combo = 0
        self.pointBonus = 0
        self.boss.d_updateCombo(self.avId, self.combo)

    def __awardCombo(self):
        self.boss.d_awardCombo(self.avId, self.combo, int(math.ceil(self.pointBonus)))
        self.resetCombo()

    def cleanup(self):
        taskMgr.remove(self.__getTaskName())
