from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from toontown.toonbase.TTLocalizer import WhisperComingToVisit, WhisperFailedVisit


class TTFriendsManager(DistributedObjectGlobal):
    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.nextTeleportFail = 0

    def d_deleteFriend(self, friendId):
        self.sendUpdate("deleteFriend", [friendId])

    def d_requestFriends(self):
        self.sendUpdate("requestFriends", [])

    def d_getToonDetails(self, toonId):
        self.sendUpdate("getToonDetails", [toonId])

    def friendDetails(self, friendId, hp, maxHp, lastHood, dnaString):
        fields = [
            ["setHp", hp],
            ["setMaxHp", maxHp],
            ["setDefaultZone", lastHood],
            ["setDNAString", dnaString],
        ]
        base.cr.n_handleGetAvatarDetailsResp(friendId, fields=fields)

    def d_teleportQuery(self, id):
        self.sendUpdate("routeTeleportQuery", [id])

    def teleportQuery(self, id):
        if not base.localAvatar:
            self.sendUpdate("teleportResponse", [id, 0, 0, 0])
            return
        if not hasattr(base.localAvatar, "ghostMode" or hasattr(base.localAvatar, "getTeleportAvailable")):
            self.sendUpdate("teleportResponse", [id, 0, 0, 0])
            return

        avatar = base.cr.identifyFriend(id)

        if base.localAvatar.ghostMode or not base.localAvatar.getTeleportAvailable():
            if hasattr(avatar, "getName"):
                base.localAvatar.setSystemMessage(id, WhisperFailedVisit % avatar.getName())
            self.sendUpdate("teleportResponse", [id, 0, 0, 0])
            return

        hoodId = base.cr.playGame.getPlaceId()
        if hasattr(avatar, "getName"):
            base.localAvatar.setSystemMessage(id, WhisperComingToVisit % avatar.getName())
        self.sendUpdate(
            "teleportResponse",
            [
                id,
                base.localAvatar.getTeleportAvailable(),
                base.localAvatar.defaultShard,
                base.localAvatar.getZoneId(),
            ],
        )

    def d_teleportResponse(self, avId, available, shardId, zoneId):
        self.sendUpdate("teleportResponse", [avId, available, shardId, zoneId])

    def setTeleportResponse(self, avId, available, district, zoneId):
        base.localAvatar.teleportResponse(avId, available, district, zoneId)

    def d_whisperSCTo(self, avId, msgIndex):
        self.sendUpdate("whisperSCTo", [avId, msgIndex])

    def setWhisperSCFrom(self, avId, msgIndex):
        if not base.localAvatar:
            return
        if not hasattr(base.localAvatar, "setWhisperSCFrom"):
            return
        base.localAvatar.setWhisperSCFrom(avId, msgIndex)

    def d_whisperSCCustomTo(self, avId, msgIndex):
        self.sendUpdate("whisperSCCustomTo", [avId, msgIndex])

    def setWhisperSCCustomFrom(self, avId, msgIndex):
        if not base.localAvatar:
            return
        if not hasattr(base.localAvatar, "setWhisperSCCustomFrom"):
            return
        base.localAvatar.setWhisperSCCustomFrom(avId, msgIndex)

    def d_whisperSCEmoteTo(self, avId, emoteId):
        self.sendUpdate("whisperSCEmoteTo", [avId, emoteId])

    def setWhisperSCEmoteFrom(self, avId, emoteId):
        if not base.localAvatar:
            return
        if not hasattr(base.localAvatar, "setWhisperSCEmoteFrom"):
            return
        base.localAvatar.setWhisperSCEmoteFrom(avId, emoteId)

    def d_teleportGiveup(self, avId):
        self.sendUpdate("teleportGiveup", [avId])

    def setTeleportGiveup(self, avId):
        base.localAvatar.teleportGiveup(avId)

    def d_whisperSCToontaskTo(self, avId, taskId, toNpcId, toonProgress, msgIndex):
        self.sendUpdate("whisperSCToontaskTo", [avId, taskId, toNpcId, toonProgress, msgIndex])

    def setWhisperSCToontaskFrom(self, avId, taskId, toNpcId, toonProgress, msgIndex):
        base.localAvatar.setWhisperSCToontaskFrom(avId, taskId, toNpcId, toonProgress, msgIndex)

    def d_sleepAutoReply(self, avId):
        self.sendUpdate("sleepAutoReply", [avId])

    def setSleepAutoReply(self, avId):
        base.localAvatar.setSleepAutoReply(avId)
