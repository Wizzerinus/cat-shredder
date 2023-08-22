from otp.avatar.DistributedAvatarUD import DistributedAvatarUD


class DistributedPlayerUD(DistributedAvatarUD):
    notify = directNotify.newCategory("DistributedPlayerUD")

    def arrivedOnDistrict(self, districtId):
        pass

    def setWLChat(self, chatString, chatFlags, accountId):
        pass

    def setSystemMessage(self, aboutId, chatString):
        pass

    def setChatFlag(self, chatFlag):
        pass

    def setSC(self, msgIndex):
        pass

    def setSCCustom(self, msgIndex):
        pass

    def setFriendsList(self, friendsList):
        pass

    def setAccountId(self, accountId):
        pass

    def setAccountName(self, name):
        pass

    def setStaffAccess(self, access):
        pass
