"""DelayDelete module: contains the DelayDelete class"""
from direct.interval.FunctionInterval import Func
from direct.interval.MetaInterval import Sequence


class DelayDelete:
    """
    The DelayDelete class is a special class whose sole purpose is
    management of the DistributedObject.delayDelete() counter.

    Normally, a DistributedObject has a delayDelete count of 0.  When
    we need to bracket a region of code that cannot tolerate a
    DistributedObject being deleted, we call do.delayDelete(1) to
    increment the delayDelete count by 1.  While the count is nonzero,
    the object will not be deleted.  Outside of our critical code, we
    call do.delayDelete(0) to decrement the delayDelete count and
    allow the object to be deleted once again.

    Explicit management of this counter is tedious and risky.  This
    class implicitly manages the counter by incrementing the count in
    the constructor, and decrementing it in the destructor.  This
    guarantees that every increment is matched up by a corresponding
    decrement.

    Thus, to temporarily protect a DistributedObject from deletion,
    simply create a DelayDelete object.  While the DelayDelete object
    exists, the DistributedObject will not be deleted; when the
    DelayDelete object ceases to exist, it may be deleted.
    """

    def __init__(self, distObj, name):
        self._distObj = distObj
        self._name = name
        self._token = self._distObj.acquireDelayDelete(name)

    def getObject(self):
        return self._distObj

    def getName(self):
        return self._name

    def destroy(self):
        if not hasattr(self, "_token"):
            return
        token = self._token
        del self._token
        self._distObj.releaseDelayDelete(token)
        del self._distObj
        del self._name


def cleanupDelayDeletes(interval):
    if hasattr(interval, "delayDelete"):
        delayDelete = interval.delayDelete
        if isinstance(delayDelete, list):
            for i in delayDelete:
                i.destroy()
        elif delayDelete:
            delayDelete.destroy()
        interval.delayDelete = None
    if hasattr(interval, "delayDeletes"):
        delayDeletes = interval.delayDeletes
        if isinstance(delayDeletes, type([])):
            for i in delayDeletes:
                i.destroy()
        elif delayDeletes:
            delayDeletes.destroy()
        interval.delayDeletes = None


def addDelayDeletes(interval, *avatars):
    interval.delayDeletes = [DelayDelete(av, "addDelayDelete") for av in avatars]
    return Sequence(
        interval,
        Func(cleanupDelayDeletes, interval),
    )
