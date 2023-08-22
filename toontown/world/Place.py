"""Place module: contains the Place class"""

from direct.fsm import StateData
from direct.showbase.PythonUtil import PriorityCallbacks
from panda3d.otp import *

from toontown.toon import TTEmote as Emote
from toontown.toon.Toon import teleportDebug
from toontown.toonbase import TTLocalizer
from . import PublicWalk, ZoneUtil
from . import QuietZoneState
from toontown.toonbase.globals.TTGlobalsCore import SPRender


class Place(StateData.StateData):
    """
    This class is the parent of Playground, Street, Estate, etc., and defines
    functionality common to all. It defines implementations of various
    localToon states, but does not itself define an ClassicFSM.
    """

    notify = directNotify.newCategory("Place")

    def __init__(self, loader, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.loader = loader
        self.zoneId = None
        self._tiToken = None
        self._leftQuietZoneLocalCallbacks = PriorityCallbacks()
        self._leftQuietZoneSubframeCall = None
        self._setZoneCompleteLocalCallbacks = PriorityCallbacks()
        self._setZoneCompleteSubframeCall = None

    def load(self):
        assert self.notify.info("loading Place")
        StateData.StateData.load(self)
        self.walkDoneEvent = "walkDone"
        self.walkStateData = PublicWalk.PublicWalk(self.fsm, self.walkDoneEvent)
        self.walkStateData.load()

        self._tempFSM = self.fsm

    def unload(self):
        StateData.StateData.unload(self)
        self.notify.info("Unloading Place (%s). Fsm in %s" % (self.zoneId, self._tempFSM.getCurrentState().getName()))
        del self._tempFSM
        del self.walkDoneEvent
        self.walkStateData.unload()
        del self.walkStateData
        del self.loader

    def setState(self, state):
        assert self.notify.debug("setState(state=" + str(state) + ")")
        if hasattr(self, "fsm"):
            self.fsm.request(state)

    def getState(self):
        assert self.notify.debug("getState")
        if hasattr(self, "fsm"):
            return self.fsm.getCurrentState().getName()
        return None

    def getZoneId(self):
        """
        Returns the current zone ID.  This is either the same as the
        hoodID for a SafeZone class, or the current zoneId for a Street
        class.
        """
        return self.zoneId

    def getTaskZoneId(self):
        """
        subclasses can override this to fool the task system into thinking
        that we're in a different zone (i.e. you can return a hood id when
        we're actually in a dynamically-allocated zone)
        """
        return self.getZoneId()

    def handleTeleportQuery(self, fromAvatar, toAvatar):
        """
        Called when another avatar somewhere in the world wants to
        teleport to us, and we're available to be teleported to.
        """
        fromAvatar.d_teleportResponse(toAvatar.doId, 1, toAvatar.defaultShard, self.getZoneId())

    def detectedPhoneCollision(self):
        assert self.notify.debug("detectedPhoneCollision")
        self.fsm.request("phone")

    def detectedFishingCollision(self):
        assert self.notify.debug("detectedFishingCollision()")
        self.fsm.request("fishing")

    def enterStart(self):
        assert self.notify.debug("enterStart()")

    def exitStart(self):
        assert self.notify.debug("exitStart()")

    def enterFinal(self):
        assert self.notify.debug("enterFinal()")

    def exitFinal(self):
        assert self.notify.debug("exitFinal()")

    def enterWalk(self, teleportIn=0):
        assert self.notify.debugStateCall(self)
        """
        Allow the user to navigate and chat
        """

        self.walkStateData.enter()
        if teleportIn == 0:
            self.walkStateData.fsm.request("walking")
        self.acceptOnce(self.walkDoneEvent, self.handleWalkDone)
        self.accept("teleportQuery", self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        self.walkStateData.fsm.request("walking")

    def exitWalk(self):
        messenger.send("wakeup")
        self.walkStateData.exit()
        self.ignore(self.walkDoneEvent)
        base.localAvatar.setTeleportAvailable(0)
        self.ignore("teleportQuery")
        if base.cr.playGame.hood is not None:
            base.cr.playGame.hood.hideTitleText()

    def handleWalkDone(self, doneStatus):
        mode = doneStatus["mode"]
        if mode == "Sit":
            self.last = self.fsm.getCurrentState().getName()
            self.fsm.request("sit")
        else:
            Place.notify.error("Invalid mode: %s" % mode)

    def enterSit(self):
        base.localAvatar.laffMeter.start()
        self.accept("teleportQuery", self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.b_setAnimState("SitStart", 1)
        self.accept(base.MOVE_FORWARD, self.fsm.request, extraArgs=["walk"])

    def exitSit(self):
        base.localAvatar.laffMeter.stop()
        base.localAvatar.setTeleportAvailable(0)
        self.ignore("teleportQuery")
        self.ignore(base.MOVE_FORWARD)

    def enterPush(self):
        base.localAvatar.laffMeter.start()
        self.accept("teleportQuery", self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)

        base.localAvatar.startPosHprBroadcast()
        base.localAvatar.b_setAnimState("Push", 1)

    def exitPush(self):
        base.localAvatar.laffMeter.stop()
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.cmod.disable()
        base.localAvatar.stopPosHprBroadcast()
        self.ignore("teleportQuery")

    def requestLeave(self, requestStatus):
        raise RuntimeError("requestLeave should not be called")

    def enterDoorIn(self, requestStatus):
        NametagGlobals.setMasterArrowsOn(0)
        door = base.cr.doId2do.get(requestStatus["doorDoId"])
        door.readyToExit()

    def exitDoorIn(self):
        assert self.notify.debug("exitDoorIn()")

        NametagGlobals.setMasterArrowsOn(1)

    def enterDoorOut(self):
        assert self.notify.debug("enterDoorOut()")

    def exitDoorOut(self):
        assert self.notify.debug("exitDoorOut()")

    def handleDoorDoneEvent(self, requestStatus):
        assert self.notify.debug("handleDoorDoneEvent(requestStatus=" + str(requestStatus) + ")")
        self.doneStatus = requestStatus
        messenger.send(self.doneEvent)

    def handleDoorTrigger(self):
        assert self.notify.debug("handleDoorTrigger()")
        self.fsm.request("doorOut")

    def enterTeleportOut(self, requestStatus, callback):
        assert self.notify.debug("enterTeleportOut()")
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState("TeleportOut", 1, callback, [requestStatus])

    def exitTeleportOut(self):
        assert self.notify.debug("exitTeleportOut()")
        base.localAvatar.laffMeter.stop()

    def enterDied(self, requestStatus, callback=None):
        assert self.notify.debug("enterDied()")
        if callback is None:
            callback = self.__diedDone
        base.localAvatar.laffMeter.start()
        camera.wrtReparentTo(render)
        base.localAvatar.b_setAnimState("Died", 1, callback, [requestStatus])

    def __diedDone(self, requestStatus):
        self.doneStatus = requestStatus
        messenger.send(self.doneEvent)

    def exitDied(self):
        assert self.notify.debug("exitDied()")
        base.localAvatar.laffMeter.stop()

    def enterTeleportIn(self, requestStatus):
        self._tiToken = self.addSetZoneCompleteCallback(
            Functor(self._placeTeleportInPostZoneComplete, requestStatus), 100
        )

    def _placeTeleportInPostZoneComplete(self, requestStatus):
        teleportDebug(requestStatus, "_placeTeleportInPostZoneComplete(%s)" % (requestStatus,))
        NametagGlobals.setMasterArrowsOn(0)
        base.localAvatar.laffMeter.start()
        base.localAvatar.reconsiderCheesyEffect()
        avId = requestStatus.get("avId", -1)
        if avId != -1:
            if avId in base.cr.doId2do:
                teleportDebug(requestStatus, "teleport to avatar")
                avatar = base.cr.doId2do[avId]
                avatar.forceToTruePosition()
                base.localAvatar.gotoNode(avatar)
                base.localAvatar.b_teleportGreeting(avId)
            else:
                friend = base.cr.identifyAvatar(avId)
                if friend is not None:
                    teleportDebug(requestStatus, "friend not here, giving up")
                    base.localAvatar.setSystemMessage(avId, TTLocalizer.WhisperTargetLeftVisit % (friend.getName(),))
                    friend.d_teleportGiveup(base.localAvatar.doId)
        base.transitions.irisIn()
        self.nextState = requestStatus.get("nextState", "walk")
        base.localAvatar.cmod.enable()
        base.localAvatar.startPosHprBroadcast()
        globalClock.tick()
        base.localAvatar.b_setAnimState("TeleportIn", 1, callback=self.teleportInDone)
        base.localAvatar.d_broadcastPositionNow()
        base.localAvatar.b_setParent(SPRender)

    def teleportInDone(self):
        """
        Note: DDPlayground overrides this to go to swimming if it needs to.
        """
        assert self.notify.debug("teleportInDone()")
        if hasattr(self, "fsm") and self.fsm:
            self.fsm.request(self.nextState, [1])

    def exitTeleportIn(self):
        assert self.notify.debug("exitTeleportIn()")
        NametagGlobals.setMasterArrowsOn(1)
        base.localAvatar.laffMeter.stop()

        base.localAvatar.cmod.disable()
        base.localAvatar.stopPosHprBroadcast()

    def requestTeleport(self, hoodId, zoneId, shardId, avId):
        if base.localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            base.localAvatar.elevatorNotifier.showMeWithoutStopping(rejectText)
            return
        loaderId = ZoneUtil.getBranchLoaderName(zoneId)
        whereId = ZoneUtil.getToonWhereName(zoneId)

        self.requestLeave(
            {
                "loader": loaderId,
                "where": whereId,
                "how": "teleportIn",
                "hoodId": hoodId,
                "zoneId": zoneId,
                "shardId": shardId,
                "avId": avId,
            }
        )

    def enterStopped(self):
        base.localAvatar.b_setAnimState("neutral", 1)
        Emote.globalEmote.disableBody(base.localAvatar, "enterStopped")
        self.accept("teleportQuery", self.handleTeleportQuery)

        base.localAvatar.setTeleportAvailable(1)

        base.localAvatar.laffMeter.start()
        base.localAvatar.startSleepWatch(self.__handleFallingAsleepStopped)

    def __handleFallingAsleepStopped(self, arg):
        if hasattr(self, "fsm"):
            self.fsm.request("walk")
        base.localAvatar.forceGotoSleep()
        messenger.send("stoppedAsleep")

    def exitStopped(self):
        Emote.globalEmote.releaseBody(base.localAvatar, "exitStopped")
        base.localAvatar.setTeleportAvailable(0)
        self.ignore("teleportQuery")
        base.localAvatar.laffMeter.stop()
        base.localAvatar.stopSleepWatch()
        messenger.send("exitingStoppedState")

    def enterQuietZone(self, requestStatus):
        assert self.notify.debug("enterQuietZone()")
        self.quietZoneDoneEvent = "quietZoneDone"
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        assert self.notify.debug("exitQuietZone()")
        self.ignore(self.quietZoneDoneEvent)
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None

    def handleQuietZoneDone(self):
        assert self.notify.debug("handleQuietZoneDone()")
        how = base.cr.handlerArgs["how"]
        assert how == "teleportIn"
        self.fsm.request(how, [base.cr.handlerArgs])

    def addSetZoneCompleteCallback(self, callback, priority=None):
        qzsd = self._getQZState()
        if qzsd:
            return qzsd.addSetZoneCompleteCallback(callback, priority)

        token = self._setZoneCompleteLocalCallbacks.add(callback, priority=priority)
        if not self._setZoneCompleteSubframeCall:
            self._setZoneCompleteSubframeCall = SubframeCall(
                self._doSetZoneCompleteLocalCallbacks, taskMgr.getCurrentTask().getPriority() - 1
            )
        return token

    def removeSetZoneCompleteCallback(self, token):
        if token is not None:
            if any(token == x[1] for x in self._setZoneCompleteLocalCallbacks._callbacks):
                self._setZoneCompleteLocalCallbacks.remove(token)
            qzsd = self._getQZState()
            if qzsd:
                qzsd.removeSetZoneCompleteCallback(token)

    def _doSetZoneCompleteLocalCallbacks(self):
        self._setZoneCompleteSubframeCall = None
        localCallbacks = self._setZoneCompleteLocalCallbacks
        self._setZoneCompleteLocalCallbacks()
        localCallbacks.clear()

    def _getQZState(self):
        if (
            hasattr(base, "cr")
            and hasattr(base.cr, "playGame")
            and hasattr(base.cr.playGame, "quietZoneStateData")
            and base.cr.playGame.quietZoneStateData
        ):
            return base.cr.playGame.quietZoneStateData
        return None

    def addLeftQuietZoneCallback(self, callback, priority=None):
        qzsd = self._getQZState()
        if qzsd:
            return qzsd.addLeftQuietZoneCallback(callback, priority)

        token = self._leftQuietZoneLocalCallbacks.add(callback, priority=priority)
        if not self._leftQuietZoneSubframeCall:
            self._leftQuietZoneSubframeCall = SubframeCall(
                self._doLeftQuietZoneCallbacks, taskMgr.getCurrentTask().getPriority() - 1
            )
        return token

    def removeLeftQuietZoneCallback(self, token):
        if token is not None:
            if token in self._leftQuietZoneLocalCallbacks:
                self._leftQuietZoneLocalCallbacks.remove(token)
            qzsd = self._getQZState()
            if qzsd:
                qzsd.removeLeftQuietZoneCallback(token)

    def _doLeftQuietZoneCallbacks(self):
        self._leftQuietZoneLocalCallbacks()
        self._leftQuietZoneLocalCallbacks.clear()
        self._leftQuietZoneSubframeCall = None
