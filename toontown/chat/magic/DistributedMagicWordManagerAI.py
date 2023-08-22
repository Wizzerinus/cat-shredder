from direct.distributed.DistributedObjectAI import DistributedObjectAI

from toontown.chat.magic.MagicBase import MagicWordLocation, MagicWordRegistry
from toontown.chat.magic.MagicWordErrors import MagicWordError
from toontown.chat.magic.MagicWordRunner import MagicWordRunner


class DistributedMagicWordManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory("DistributedMagicWordManagerAI")

    def __init__(self, air):
        super().__init__(air)
        self.runner = MagicWordRunner()

    # distributed
    def runMagicWord(self, wordName, args):
        avId = self.air.getAvatarIdFromSender()
        toon = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning(f"Invalid sender's avId: {avId}!")
            return

        accessLevel = toon.staffAccess
        err, msg, mwo = self.runner.run(accessLevel, wordName, args, MagicWordLocation.SERVER, toon, avId)
        if err != MagicWordError.MAGIC_WORD_NOT_ISSUED:
            self.sendUpdateToAvatarId(avId, "receiveResult", [err, wordName, msg])

        # try to run on the client if applicable
        mwCls = MagicWordRegistry.getWordClass(wordName)
        if mwCls and MagicWordLocation.CLIENT in mwCls.getLocations() and err != MagicWordError.INSUFFICIENT_ACCESS:
            self.sendUpdateToAvatarId(avId, "runMagicWordClient", [wordName, args])

        if mwo is not None:
            for mwn, clargs in mwo.clientsideCommands:
                self.sendUpdateToAvatarId(avId, "runMagicWordClient", [mwn, clargs])
