from direct.distributed.DistributedObject import DistributedObject

from toontown.chat.magic.MagicBase import MagicWordLocation
from toontown.chat.magic.MagicWordErrors import DefaultError, ErrorDescriptions, MagicWordError
from toontown.chat.magic.MagicWordRunner import MagicWordRunner


class DistributedMagicWordManager(DistributedObject):
    notify = directNotify.newCategory("DistributedMagicWordManager")
    # NOTE to self in the future: if you don't add this then you get the cr is not set error <- Wizz
    neverDisable = 1

    def __init__(self, cr):
        super().__init__(cr)
        self.accept("magicWord", self.processMagicWord)
        self.runner = MagicWordRunner()

    def disable(self):
        super().disable()
        self.ignore("magicWord")

    def processMagicWord(self, chatString):
        wordName, args, errno, errargs = self.runner.parseArgs(chatString)

        if errno:
            self.sendError(errno, **errargs)
            return

        # This check is done once again on the AI, but it's nice not having to make a network request first
        accessLevel = base.localAvatar.staffAccess
        if not self.runner.sufficientAccessLevel(accessLevel, wordName):
            self.sendError(MagicWordError.INSUFFICIENT_ACCESS, name=wordName)
            return

        # We can technically immediately issue the word on the client
        # if it's clientside, but we have to make a injector check through the AI first
        # in case the user memory edited their own access level. get banned nerd
        self.sendUpdate("runMagicWord", [wordName, args])

    @staticmethod
    def sendError(error, **kwargs):
        message = ErrorDescriptions.get(error, DefaultError) % kwargs
        base.talkAssistant.addMagicWordResponse(message)

    # distributed
    def runMagicWordClient(self, wordName, args):
        accessLevel = base.localAvatar.staffAccess
        err, msg, mwo = self.runner.run(accessLevel, wordName, args, MagicWordLocation.CLIENT, base.localAvatar)
        self.receiveResult(err, wordName, msg)

    def receiveResult(self, error, wordName, status):
        if error == 0:
            base.talkAssistant.addMagicWordResponse(status)
            return
        self.sendError(error, name=wordName, status=status)
