from direct.showbase import GarbageReport

from otp.avatar import DistributedAvatarAI
from otp.avatar import PlayerBase


class DistributedPlayerAI(DistributedAvatarAI.DistributedAvatarAI, PlayerBase.PlayerBase):
    DISLid = None

    def __init__(self, air):
        DistributedAvatarAI.DistributedAvatarAI.__init__(self, air)
        PlayerBase.PlayerBase.__init__(self)
        self.friendsList = []
        self.staffAccess = 0

    def announceGenerate(self):
        DistributedAvatarAI.DistributedAvatarAI.announceGenerate(self)
        self._doPlayerEnter()

    def _announceArrival(self):
        self.sendUpdate("arrivedOnDistrict", [self.air.districtId])

    def _announceExit(self):
        self.sendUpdate("arrivedOnDistrict", [0])

    def _sendExitServerEvent(self):
        """call this in your delete() function. This would be an
        override of delete(), but player classes typically use
        multiple inheritance, and some other base class gets to
        call down the chain to DistributedObjectAI before this
        class gets a chance, and self.air & self.doId are removed
        in the first call to DistributedObjectAI.delete(). Better
        would be reference counting calls to generate() and delete()
        in base classes that appear more than once in a class'
        inheritance heirarchy"""
        self.air.writeServerEvent("avatarExit", self.doId, "")

    def delete(self):
        self._doPlayerExit()
        if __dev__:
            GarbageReport.checkForGarbageLeaks()
        DistributedAvatarAI.DistributedAvatarAI.delete(self)

    def isPlayerControlled(self):
        return True

    def setLocation(self, parentId, zoneId, teleport=0):
        DistributedAvatarAI.DistributedAvatarAI.setLocation(self, parentId, zoneId, teleport)
        if self.isPlayerControlled():
            if not self.air.isValidPlayerLocation(parentId, zoneId):
                self.notify.info(f"booting player {self.doId} for doing setLocation to ({parentId}, {zoneId})")
                self.air.writeServerEvent("suspicious", self.doId, f"invalid setLocation: ({parentId}, {zoneId})")
                self.requestDelete()
                return False

        return True

    def _doPlayerEnter(self):
        self.incrementPopulation()
        self._announceArrival()

    def _doPlayerExit(self):
        self._announceExit()
        self.decrementPopulation()

    def incrementPopulation(self):
        self.air.incrementPopulation()

    def decrementPopulation(self):
        simbase.air.decrementPopulation()

    def d_setSystemMessage(self, aboutId, chatString):
        self.sendUpdate("setSystemMessage", [aboutId, chatString])

    def setAccountName(self, accountName):
        self.accountName = accountName

    def getAccountName(self):
        return self.accountName

    def setDISLid(self, accountId):
        self.DISLid = accountId

    def d_setFriendsList(self, friendsList):
        self.sendUpdate("setFriendsList", [friendsList])

    def setFriendsList(self, friendsList):
        self.friendsList = friendsList
        self.notify.debug(f"setting friends list to {self.friendsList}")

    def getFriendsList(self):
        return self.friendsList

    def extendFriendsList(self, friendId, flag=0):
        self.notify.warning(f"extendFriendsList called on parent DistributedPlayerAI!")

    def setStaffAccess(self, staffAccess):
        self.staffAccess = staffAccess

    def getStaffAccess(self):
        return self.staffAccess
