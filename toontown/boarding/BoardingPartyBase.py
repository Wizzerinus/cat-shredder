import copy


BOARDCODE_OKAY = 1
BOARDCODE_MISSING = 0
BOARDCODE_SPACE = -1
BOARDCODE_DIFF_GROUP = -2
BOARDCODE_PENDING_INVITE = -3
BOARDCODE_IN_ELEVATOR = -4

INVITE_ACCEPT_FAIL_GROUP_FULL = -1


class BoardingPartyBase:
    def __init__(self):
        self.groupListDict = {}
        self.avIdDict = {}

    def cleanup(self):
        del self.groupListDict
        del self.avIdDict

    def getGroupSize(self):
        return self.maxSize

    def setGroupSize(self, groupSize):
        self.maxSize = groupSize

    def getGroupLeader(self, avatarId):
        if avatarId in self.avIdDict:
            return self.avIdDict[avatarId]

        return None

    def isGroupLeader(self, avatarId):
        leaderId = self.getGroupLeader(avatarId)
        return avatarId == leaderId

    def getGroupMemberList(self, avatarId):
        """
        returns the memberlist with the leader at index 0
        """
        if avatarId in self.avIdDict:
            leaderId = self.avIdDict[avatarId]
            group = self.groupListDict.get(leaderId)
            if group:
                returnList = copy.copy(group[0])
                if 0 in returnList:
                    returnList.remove(0)
                return returnList
        return []

    def getGroupInviteList(self, avatarId):
        if avatarId in self.avIdDict:
            leaderId = self.avIdDict[avatarId]
            group = self.groupListDict.get(leaderId)
            if group:
                returnList = copy.copy(group[1])
                if 0 in returnList:
                    returnList.remove(0)
                return returnList
        return []

    def getGroupKickList(self, avatarId):
        if avatarId in self.avIdDict:
            leaderId = self.avIdDict[avatarId]
            group = self.groupListDict.get(leaderId)
            if group:
                returnList = copy.copy(group[2])
                if 0 in returnList:
                    returnList.remove(0)
                return returnList
        return []

    def hasActiveGroup(self, avatarId):
        """
        Returns True if the avatar has an active boarding group.
        """
        memberList = self.getGroupMemberList(avatarId)
        if avatarId in memberList and len(memberList) > 1:
            return True
        return False

    def hasPendingInvite(self, avatarId):
        """
        This is a two-stage check:
        If the avatar is a leader just check if there is anyone in the leader's invite list.
        If the avatar is a non-leader just check if the avatar is there in it's leader's invite list.
        """
        pendingInvite = False
        if avatarId in self.avIdDict:
            leaderId = self.avIdDict[avatarId]
            leaderInviteList = self.getGroupInviteList(leaderId)
            pendingInvite = bool(len(leaderInviteList)) if leaderId == avatarId else avatarId in leaderInviteList
        return pendingInvite

    def isInGroup(self, memberId, leaderId):
        """
        Returns True if the member is in the leader's member list or invite list.
        Else returns False.
        """
        return (memberId in self.getGroupMemberList(leaderId)) or (memberId in self.getGroupInviteList(leaderId))
