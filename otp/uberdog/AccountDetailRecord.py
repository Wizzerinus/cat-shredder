class AccountDetailRecord:
    def __init__(self):
        self.createFriendsWithChat = False
        self.chatCodeCreation = False
        self.familyAccountId = 0
        self.playerAccountId = 0
        self.playerName = ""
        self.playerNameApproved = False
        self.maxAvatars = 0
        self.numFamilyMembers = 0
        self.familyMembers = []
        self.numSubs = 0
        self.maxAvatarSlots = 0
        self.WLChatEnabled = False

    def __str__(self):
        s = f"========== Account {self.playerAccountId} ==========\n"
        s += f"WLChatEnabled: {self.WLChatEnabled}\n"
        s += f"CreateFriendsWithChat: {self.createFriendsWithChat}\n"
        s += f"ChatCodeCreation: {self.chatCodeCreation}\n"
        s += f"FamilyAccountId: {int(self.familyAccountId)}\n"
        s += f"PlayerAccountId: {int(self.playerAccountId)}\n"
        s += f"PlayerName: {self.playerName}\n"
        s += f"AccountNameApproved: {int(self.playerNameApproved)}\n"
        s += f"MaxAvatars: {int(self.maxAvatars)}\n"
        s += f"MaxAvatarSlots: {int(self.maxAvatarSlots)}\n"
        s += f"NumFamilyMembers: {int(self.numFamilyMembers)}\n"
        s += f"FamilyMembers: {self.familyMembers}\n"
        s += f"NumSubs: {self.numSubs}\n"
        s += "================================\n"
        return s
