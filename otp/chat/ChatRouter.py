from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal


class ChatRouter(DistributedObjectGlobal):
    notify = directNotify.newCategory("ChatRouter")

    def sendChatMessage(self, message):
        self.sendUpdate("redirectMessage", [message])

    def sendWhisperMessage(self, message, receiverAvId):
        self.sendUpdate("whisperMessage", [message, receiverAvId])
