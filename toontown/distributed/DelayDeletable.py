from direct.distributed import DistributedObject
from direct.distributed.DistributedObject import ESNum2Str
from direct.showbase.PythonUtil import SerialNumGen


class DelayDeletable(DistributedObject.DistributedObject):
    DelayDeleteSerialGen = SerialNumGen()

    def delayDelete(self):
        """
        Inheritors should redefine this to take appropriate action on delayDelete
        """

    def acquireDelayDelete(self, name):
        if (not self._delayDeleteForceAllow) and (
            self.activeState not in (DistributedObject.ESGenerating, DistributedObject.ESGenerated)
        ):
            self.notify.error(
                f'cannot acquire DelayDelete "{name}" on {self.__class__.__name__} '
                f"because it is in state {ESNum2Str[self.activeState]}"
            )

        if self.getDelayDeleteCount() == 0:
            self.cr._addDelayDeletedDO(self)

        token = DelayDeletable.DelayDeleteSerialGen.next()
        self._token2delayDeleteName[token] = name

        assert self.notify.debug(f"delayDelete count for doId {self.doId} now {len(self._token2delayDeleteName)}")

        return token

    def releaseDelayDelete(self, token):
        name = self._token2delayDeleteName.pop(token)
        assert self.notify.debug(f"releasing delayDelete '{name}'")
        if len(self._token2delayDeleteName) == 0:
            assert self.notify.debug(f"delayDelete count for doId {self.doId} now 0")
            self.cr._removeDelayDeletedDO(self)
            if self._delayDeleted:
                self.disableAnnounceAndDelete()

    def getDelayDeleteNames(self):
        return list(self._token2delayDeleteName.values())

    def forceAllowDelayDelete(self):
        self._delayDeleteForceAllow = True
