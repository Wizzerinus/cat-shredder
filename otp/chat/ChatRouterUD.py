from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD


class ChatRouterUD(DistributedObjectGlobalUD):
    notify = directNotify.newCategory("ChatRouterUD")

    def redirectMessage(self, message):
        avId = self.air.getAvatarIdFromSender()
        do = self.air.dclassesByName["DistributedPlayerUD"]
        datagram = do.aiFormatUpdate("setTalk", avId, avId, self.air.ourChannel, [avId, message, []])
        self.air.send(datagram)

    def whisperMessageUber(self, avId, message, receiverAvId, avatarName):
        do = self.air.dclassesByName["DistributedPlayerUD"]
        args = [avId, avatarName, message, []]
        datagram = do.aiFormatUpdate("setTalkWhisper", receiverAvId, receiverAvId, self.air.ourChannel, args)
        self.air.send(datagram)
