from panda3d.otp import CFSpeech, CFThought, CFTimeout, WhisperPopup

from otp.speedchat import SCDecoders
from toontown.toonbase.globals import TTGlobalsChat


class ChatMessage:
    NORMAL = 0
    WHISPER = 1
    SYSTEM = 2

    def __init__(self, content, senderData=(None, None), receiverData=(None, None), messageType=NORMAL):
        self.messageType = messageType
        self.senderAvId, self.senderName = senderData
        self.receiverAvId, self.receiverName = receiverData
        self.content = content


class TalkAssistantV2:
    wizardName = "Magic Minnie"

    @staticmethod
    def addMessage(message):
        messenger.send("ChatLogMessage", [message])

    @staticmethod
    def parseMessage(message):
        if message.startswith("."):
            return message[1:], CFThought
        return message, CFSpeech | CFTimeout

    @staticmethod
    def resolveAvatarName(avId, avName=None):
        if avName:
            return avName

        info = base.cr.identifyAvatar(avId)
        return info.getName() if info else ""

    def receiveSCMessage(self, mode, avId, msgId, avName=None):
        if avName is None:
            receiverData = (None, None)
            messageType = ChatMessage.NORMAL
        else:
            receiverData = (base.localAvatar.doId, base.localAvatar.getName())
            messageType = ChatMessage.WHISPER
        avName = self.resolveAvatarName(avId, avName)
        text = SCDecoders.decodeMessageFlexible(mode, msgId, avName)
        self.addMessage(ChatMessage(text, (avId, avName), receiverData, messageType=messageType))

    def receiveMessage(self, avId, text, avName=None):
        if avName is None:
            receiverData = (None, None)
            messageType = ChatMessage.NORMAL
        else:
            receiverData = (base.localAvatar.doId, base.localAvatar.getName())
            messageType = ChatMessage.WHISPER
        text = self.parseMessage(text)[0]
        avName = self.resolveAvatarName(avId, avName)
        self.addMessage(ChatMessage(text, (avId, avName), receiverData, messageType=messageType))

    def sendSCMessage(self, mode, msgId, avId=None):
        if avId is None:
            callbacks = {
                TTGlobalsChat.SPEEDCHAT_NORMAL: base.localAvatar.b_setSC,
                TTGlobalsChat.SPEEDCHAT_EMOTE: base.localAvatar.b_setSCEmote,
                TTGlobalsChat.SPEEDCHAT_CUSTOM: base.localAvatar.b_setSCCustom,
            }
            callbacks[mode](msgId)
            return

        callbacks = {
            TTGlobalsChat.SPEEDCHAT_NORMAL: base.localAvatar.whisperSCTo,
            TTGlobalsChat.SPEEDCHAT_EMOTE: base.localAvatar.whisperSCEmoteTo,
            TTGlobalsChat.SPEEDCHAT_CUSTOM: base.localAvatar.whisperSCCustomTo,
        }
        callbacks[mode](msgId, avId)
        avName = base.localAvatar.getName()
        decodedMessage = SCDecoders.decodeMessageFlexible(mode, msgId, avName)
        self.addMessage(
            ChatMessage(
                decodedMessage,
                (base.localAvatar.doId, avName),
                (avId, self.resolveAvatarName(avId)),
                messageType=ChatMessage.WHISPER,
            )
        )

    def sendMessage(self, text, avId=None):
        if not text:
            return

        if text.startswith("/"):
            messenger.send("magicWord", [text])
            self.addMessage(ChatMessage(f"Issued magic word: {text}", messageType=ChatMessage.SYSTEM))
            return

        if avId is not None:
            base.cr.chatRouter.sendWhisperMessage(text, avId)

            self.addMessage(
                ChatMessage(
                    text,
                    (base.localAvatar.doId, base.localAvatar.getName()),
                    (avId, self.resolveAvatarName(avId)),
                    messageType=ChatMessage.WHISPER,
                )
            )
        else:
            base.cr.chatRouter.sendChatMessage(text)

    def addMagicWordResponse(self, response):
        response = f"{self.wizardName}: {response}"
        self.addMessage(
            ChatMessage(
                response,
                (0, self.wizardName),
                (base.localAvatar.doId, base.localAvatar.getName()),
                ChatMessage.SYSTEM,
            )
        )
        base.localAvatar.setSystemMessage(0, response, WhisperPopup.WTSystem)
