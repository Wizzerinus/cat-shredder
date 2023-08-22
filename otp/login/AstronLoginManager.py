from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal


class AstronLoginManager(DistributedObjectGlobal):
    notify = directNotify.newCategory("AstronLoginManager")

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self._callback = None

    def handleRequestLogin(self):
        playToken = self.cr.playToken or "dev"
        self.sendRequestLogin(playToken)

    def sendRequestLogin(self, playToken):
        self.sendUpdate("requestLogin", [playToken])

    def loginResponse(self, responseBlob):
        self.cr.handleLoginToontownResponse(responseBlob)

    def sendRequestAvatarList(self):
        self.sendUpdate("requestAvatarList")

    def avatarListResponse(self, avatarList):
        self.cr.handleAvatarListResponse(avatarList)

    def sendCreateAvatar(self, avDNA, avName, avPosition):
        self.sendUpdate("createAvatar", [avDNA.makeNetString(), avName, avPosition])

    def createAvatarResponse(self, avId):
        messenger.send("createAvatarDone", [avId])

    def sendRequestRemoveAvatar(self, avId):
        self.sendUpdate("requestRemoveAvatar", [avId])

    def sendRequestPlayAvatar(self, avId):
        self.sendUpdate("requestPlayAvatar", [avId])
