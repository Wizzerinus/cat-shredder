"""QuietZoneState module: contains the quiet state which is used by
   multiple FSMs"""
from direct.distributed.MsgTypes import MsgName2Id, QUIET_ZONE_IGNORED_LIST
from direct.fsm import ClassicFSM, State
from direct.fsm import StateData
from direct.task import Task

from . import ZoneUtil


class QuietZoneState(StateData.StateData):
    """QuietZoneState state class"""

    notify = directNotify.newCategory("QuietZoneState")

    Disable = False

    def __init__(self, doneEvent):
        """__init__(self, string)
        QuietZoneState state constructor
        """
        StateData.StateData.__init__(self, doneEvent)
        self.fsm = ClassicFSM.ClassicFSM(
            "QuietZoneState",
            [
                State.State("off", self.enterOff, self.exitOff, ["waitForQuietZoneResponse"]),
                State.State(
                    "waitForQuietZoneResponse",
                    self.enterWaitForQuietZoneResponse,
                    self.exitWaitForQuietZoneResponse,
                    ["waitForZoneRedirect"],
                ),
                State.State(
                    "waitForZoneRedirect",
                    self.enterWaitForZoneRedirect,
                    self.exitWaitForZoneRedirect,
                    ["waitForSetZoneResponse"],
                ),
                State.State(
                    "waitForSetZoneResponse",
                    self.enterWaitForSetZoneResponse,
                    self.exitWaitForSetZoneResponse,
                    ["waitForSetZoneComplete"],
                ),
                State.State(
                    "waitForSetZoneComplete",
                    self.enterWaitForSetZoneComplete,
                    self.exitWaitForSetZoneComplete,
                    ["waitForLocalAvatarOnShard"],
                ),
                State.State(
                    "waitForLocalAvatarOnShard",
                    self.enterWaitForLocalAvatarOnShard,
                    self.exitWaitForLocalAvatarOnShard,
                    ["off"],
                ),
            ],
            "off",
            "off",
        )
        self.fsm.enterInitialState()

    def load(self):
        self.notify.debug("load()")

    def unload(self):
        self.notify.debug("unload()")
        del self.fsm

    def enter(self, requestStatus):
        self.notify.debug("enter(requestStatus=" + str(requestStatus) + ")")
        base.transitions.fadeScreen(1.0)
        self._requestStatus = requestStatus
        self.fsm.request("waitForQuietZoneResponse")

    def getRequestStatus(self):
        return self._requestStatus

    def exit(self):
        self.notify.debug("exit()")
        del self._requestStatus
        base.transitions.noFade()
        self.fsm.request("off")

    def waitForDatabase(self, description):
        base.cr.waitForDatabaseTimeout(requestName="quietZoneState-%s" % description)

    def clearWaitForDatabase(self):
        base.cr.cleanupWaitingForDatabase()

    def handleWaitForQuietZoneResponse(self, msgType, di):
        if msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED"]:
            base.cr.handleQuietZoneGenerateWithRequired(di)
        elif msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED_OTHER"]:
            base.cr.handleQuietZoneGenerateWithRequiredOther(di)
        elif msgType == MsgName2Id["CLIENT_OBJECT_SET_FIELD"]:
            base.cr.handleQuietZoneUpdateField(di)
        elif msgType in QUIET_ZONE_IGNORED_LIST:
            self.notify.debug("ignoring unwanted message from previous zone")
        else:
            base.cr.handlePlayGame(msgType, di)

    def handleWaitForZoneRedirect(self, msgType, di):
        if msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED"]:
            base.cr.handleQuietZoneGenerateWithRequired(di)
        elif msgType == MsgName2Id["CLIENT_ENTER_OBJECT_REQUIRED_OTHER"]:
            base.cr.handleQuietZoneGenerateWithRequiredOther(di)
        elif msgType == MsgName2Id["CLIENT_OBJECT_SET_FIELD"]:
            base.cr.handleQuietZoneUpdateField(di)
        else:
            base.cr.handlePlayGame(msgType, di)

    def enterOff(self):
        self.notify.debug("enterOff()")

    def exitOff(self):
        self.notify.debug("exitOff()")

    def enterWaitForQuietZoneResponse(self):
        self.notify.debug("enterWaitForQuietZoneResponse(doneStatus=" + str(self._requestStatus) + ")")
        if not self.Disable:
            base.cr.handler = self.handleWaitForQuietZoneResponse
            base.cr.handlerArgs = self._requestStatus
            base.cr.setInQuietZone(True)
        self.setZoneDoneEvent = base.cr.getNextSetZoneDoneEvent()
        self.acceptOnce(self.setZoneDoneEvent, self._handleQuietZoneComplete)
        self.waitForDatabase("WaitForQuietZoneResponse")
        if base.slowQuietZone:

            def sQZR(task):
                base.cr.sendQuietZoneRequest()
                return Task.done

            taskMgr.doMethodLater(base.slowQuietZoneDelay, sQZR, "slowQuietZone-sendQuietZoneRequest")
        else:
            base.cr.sendQuietZoneRequest()

    def _handleQuietZoneComplete(self):
        self.fsm.request("waitForZoneRedirect")

    def exitWaitForQuietZoneResponse(self):
        self.notify.debug("exitWaitForQuietZoneResponse()")
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        base.cr.setInQuietZone(False)
        self.ignore(self.setZoneDoneEvent)
        del self.setZoneDoneEvent

    def enterWaitForZoneRedirect(self):
        self.notify.debug("enterWaitForZoneRedirect(requestStatus=" + str(self._requestStatus) + ")")
        if not self.Disable:
            base.cr.handler = self.handleWaitForZoneRedirect
            base.cr.handlerArgs = self._requestStatus
            base.cr.setInQuietZone(True)

        self.waitForDatabase("WaitForZoneRedirect")
        self.fsm.request("waitForSetZoneResponse")

    def gotZoneRedirect(self, zoneId):
        self.notify.info("Redirecting to zone %s." % (zoneId))
        base.cr.handlerArgs["zoneId"] = zoneId
        base.cr.handlerArgs["hoodId"] = ZoneUtil.getHoodId(zoneId)

        self.fsm.request("waitForSetZoneResponse")

    def exitWaitForZoneRedirect(self):
        self.notify.debug("exitWaitForZoneRedirect()")
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        base.cr.setInQuietZone(False)

    def enterWaitForSetZoneResponse(self):
        self.notify.debug("enterWaitForSetZoneResponse(requestStatus=" + str(self._requestStatus) + ")")
        if not self.Disable:
            messenger.send("enterWaitForSetZoneResponse", [self._requestStatus])
            base.cr.handlerArgs = self._requestStatus
            zoneId = self._requestStatus["zoneId"]
            base.cr.dumpAllSubShardObjects()
            base.cr.resetDeletedSubShardDoIds()
            base.cr.sendSetZoneMsg(zoneId)
            self.waitForDatabase("WaitForSetZoneResponse")
            self.fsm.request("waitForSetZoneComplete")

    def exitWaitForSetZoneResponse(self):
        self.notify.debug("exitWaitForSetZoneResponse()")
        self.clearWaitForDatabase()
        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None

    def enterWaitForSetZoneComplete(self):
        self.notify.debug("enterWaitForSetZoneComplete(requestStatus=" + str(self._requestStatus) + ")")
        if not self.Disable:
            base.cr.handlerArgs = self._requestStatus
            if base.slowQuietZone:

                def delayFunc(self=self):
                    def hSZC(task):
                        self._handleSetZoneComplete()
                        return Task.done

                    taskMgr.doMethodLater(base.slowQuietZoneDelay, hSZC, "slowQuietZone-sendSetZoneComplete")

                nextFunc = delayFunc
            else:
                nextFunc = self._handleSetZoneComplete
            self.waitForDatabase("WaitForSetZoneComplete")
            self.setZoneDoneEvent = base.cr.getLastSetZoneDoneEvent()
            self.acceptOnce(self.setZoneDoneEvent, nextFunc)

    def _handleSetZoneComplete(self):
        self.fsm.request("waitForLocalAvatarOnShard")

    def exitWaitForSetZoneComplete(self):
        self.notify.debug("exitWaitForSetZoneComplete()")
        self.clearWaitForDatabase()

        base.cr.handler = base.cr.handlePlayGame
        base.cr.handlerArgs = None
        self.ignore(self.setZoneDoneEvent)
        del self.setZoneDoneEvent

    def enterWaitForLocalAvatarOnShard(self):
        self.notify.debug("enterWaitForLocalAvatarOnShard()")
        if not self.Disable:
            base.cr.handlerArgs = self._requestStatus
            self._onShardEvent = base.localAvatar.getArrivedOnDistrictEvent()
            self.waitForDatabase("WaitForLocalAvatarOnShard")
            if base.localAvatar.isGeneratedOnDistrict(base.localAvatar.defaultShard):
                self._announceDone()
            else:
                self.acceptOnce(self._onShardEvent, self._announceDone)

    def _announceDone(self):
        base.localAvatar.startChat()
        messenger.send("setZoneComplete", self._requestStatus)
        messenger.send(self.doneEvent)

    def exitWaitForLocalAvatarOnShard(self):
        self.notify.debug("exitWaitForLocalAvatarOnShard()")
        self.clearWaitForDatabase()
        self.ignore(self._onShardEvent)
        base.cr.handlerArgs = None
        del self._onShardEvent
