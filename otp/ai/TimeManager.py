from direct.distributed import DistributedObject
from direct.distributed.ClockDelta import globalClockDelta
from panda3d.otp import CFSpeech, CFTimeout

from toontown.toonbase.globals.TTGlobalsCore import SynchronizeHotkey


class TimeManager(DistributedObject.DistributedObject):
    """
    This DistributedObject lives on the AI and on the client side, and
    serves to synchronize the time between them so they both agree, to
    within a few hundred milliseconds at least, what time it is.

    This used to use a push model where the AI side would push the
    time down to the client periodically, but now it uses a pull model
    where the client can request a synchronization check from time to
    time.  It also employs a round-trip measurement to minimize the
    effect of latency.
    """

    notify = directNotify.newCategory("TimeManager")

    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

        self.updateFreq = 1800
        self.minWait = 10
        self.maxUncertainty = 1
        self.maxAttempts = 5

        self.talkResult = 0
        self.thisContext = -1
        self.nextContext = 0
        self.attemptCount = 0
        self.start = 0
        self.lastAttempt = -self.minWait * 2

    def generate(self):
        if self.cr.timeManager is not None:
            self.cr.timeManager.delete()
        self.cr.timeManager = self
        DistributedObject.DistributedObject.generate(self)

        self.accept(SynchronizeHotkey, self.handleHotkey)
        self.accept("clock_error", self.handleClockError)

        if self.updateFreq > 0:
            self.startTask()

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.synchronize("TimeManager.announceGenerate")

    def disable(self):
        self.ignore(SynchronizeHotkey)
        self.ignore("clock_error")
        self.stopTask()
        taskMgr.remove("frameRateMonitor")
        if self.cr.timeManager == self:
            self.cr.timeManager = None
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        self.ignore(SynchronizeHotkey)
        self.ignore("clock_error")
        self.stopTask()
        taskMgr.remove("frameRateMonitor")
        if self.cr.timeManager == self:
            self.cr.timeManager = None
        DistributedObject.DistributedObject.delete(self)

    def startTask(self):
        self.stopTask()
        taskMgr.doMethodLater(self.updateFreq, self.doUpdate, "timeMgrTask")

    @staticmethod
    def stopTask():
        taskMgr.remove("timeMgrTask")

    def doUpdate(self, task):
        self.synchronize("timer")
        taskMgr.doMethodLater(self.updateFreq, self.doUpdate, "timeMgrTask")
        return task.done

    def handleHotkey(self):
        self.lastAttempt = -self.minWait * 2

        if self.synchronize("user hotkey"):
            self.talkResult = 1
        else:
            base.localAvatar.setChatAbsolute("Too soon.", CFSpeech | CFTimeout)

    def handleClockError(self):
        self.synchronize("clock error")

    def synchronize(self, description):
        """synchronize(self, string description)

        Call this function from time to time to synchronize watches
        with the server.  This initiates a round-trip transaction;
        when the transaction completes, the time will be synced.

        The description is the string that will be written to the log
        file regarding the reason for this synchronization attempt.

        The return value is true if the attempt is made, or false if
        it is too soon since the last attempt.
        """
        now = globalClock.getRealTime()

        if now - self.lastAttempt < self.minWait:
            self.notify.debug(f"Not resyncing (too soon): {description}")
            return 0

        self.talkResult = 0
        self.thisContext = self.nextContext
        self.attemptCount = 0
        self.nextContext = (self.nextContext + 1) & 255
        self.notify.info(f"Clock sync: {description}")
        self.start = now
        self.lastAttempt = now
        self.sendUpdate("requestServerTime", [self.thisContext])

        return 1

    def serverTime(self, context, timestamp):
        """serverTime(self, int8 context, int32 timestamp)

        This message is sent from the AI to the client in response to
        a previous requestServerTime.  It contains the time of day as
        observed by the AI.

        The client should use this, in conjunction with the time
        measurement taken before calling requestServerTime (above), to
        determine the clock delta between the AI and the client
        machines.
        """
        end = globalClock.getRealTime()

        if context != self.thisContext:
            self.notify.info(f"Ignoring TimeManager response for old context {int(context)}")
            return

        elapsed = end - self.start
        self.attemptCount += 1
        self.notify.info(f"Clock sync roundtrip took {elapsed * 1000.0:0.3f} ms")

        average = (self.start + end) / 2.0
        uncertainty = (end - self.start) / 2.0

        globalClockDelta.resynchronize(average, timestamp, uncertainty)

        self.notify.info(f"Local clock uncertainty +/- {globalClockDelta.getUncertainty():.3f} s")

        if globalClockDelta.getUncertainty() > self.maxUncertainty:
            if self.attemptCount < self.maxAttempts:
                self.notify.info("Uncertainty is too high, trying again.")
                self.start = globalClock.getRealTime()
                self.sendUpdate("requestServerTime", [self.thisContext])
                return
            self.notify.info("Giving up on uncertainty requirement.")

        if self.talkResult:
            base.localAvatar.setChatAbsolute(
                f"latency {elapsed * 1000.0:0.0f} ms, sync ±{globalClockDelta.getUncertainty() * 1000.0:0.0f} ms",
                CFSpeech | CFTimeout,
            )

        messenger.send("gotTimeSync")

    def setDisconnectReason(self, disconnectCode):
        """setDisconnectReason(self, uint8 disconnectCode)

        This method is called by the client just before it leaves a
        shard to alert the AI as to the reason it's going.  If the AI
        doesn't get this message, it can assume the client aborted
        messily or its internet connection was dropped.
        """
        self.notify.info(f"Client disconnect reason {disconnectCode}.")
        self.sendUpdate("setDisconnectReason", [disconnectCode])

    def d_setSignature(self, signatureHash):
        """
        This method is called by the client at startup time, to send
        the xrc signature and the prc hash to the AI for logging in
        case the client does anything suspicious.
        """
        self.sendUpdate("setSignature", [signatureHash])
