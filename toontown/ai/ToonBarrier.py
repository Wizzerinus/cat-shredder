""" ToonBarrier: utility class for AI objects that must wait for a message from each of a list of Toons """

import random

from direct.showbase import DirectObject
from direct.task.Task import Task


class ToonBarrier(DirectObject.DirectObject):
    notify = directNotify.newCategory("ToonBarrier")

    def __init__(self, name, uniqueName, avIdList, timeout, clearedFunc=None, timeoutFunc=None, doneFunc=None):
        """
        name: a context name that should be used in common with the
              client code.
        uniqueName: should be a unique name for this ToonBarrier, used
                    for timeout doLater
        avIdList: list of toons from which we'll expect responses
        timeout: how long to wait before giving up
        clearedFunc: func to call when all toons have cleared the barrier;
                     takes no arguments
        timeoutFunc: func to call when the timeout has expired;
                     takes list of avIds of toons that did not
                     clear the barrier
        doneFunc:    func to call when the the barrier is complete for
                     either reason; takes list of avIds of toons that
                     successfully cleared the barrier

        Call ToonBarrier.clear(avId) when you get a response from
        each toon.

        If you need to have additional parameters passed to your
        callback funcs, see PythonUtil.Functor
        """
        self.name = name
        self.uniqueName = f"{uniqueName}-Barrier"
        self.avIdList = avIdList[:]
        self.pendingAvatars = self.pendingToons = self.avIdList[:]
        self.timeout = timeout
        self.clearedFunc = clearedFunc
        self.timeoutFunc = timeoutFunc
        self.doneFunc = doneFunc

        if len(self.pendingToons) == 0:
            self.notify.debug(f"{self.uniqueName}: barrier with empty list")
            self.active = 0
            if self.clearedFunc:
                self.clearedFunc()
            if self.doneFunc:
                self.doneFunc(self.avIdList)
            return

        self.taskName = f"{self.uniqueName}-Timeout"
        origTaskName = self.taskName
        while taskMgr.hasTaskNamed(self.taskName):
            self.taskName = f"{origTaskName}-{str(random.randint(0, 10000))}"

        taskMgr.doMethodLater(self.timeout, self.__timerExpired, self.taskName)

        for avId in self.avIdList:
            event = simbase.air.getAvatarExitEvent(avId)
            self.acceptOnce(event, self.__handleUnexpectedExit, extraArgs=[avId])

        self.notify.debug(f"{self.uniqueName}: expecting responses from {self.avIdList} within {self.timeout} seconds")

        self.active = 1

    def cleanup(self):
        """
        call this if you're abandoning the barrier condition and
        discarding this object
        """
        if self.active:
            taskMgr.remove(self.taskName)
            self.active = 0
        self.ignoreAll()

    def clear(self, avId):
        if avId not in self.pendingToons:
            self.notify.warning(f"{self.uniqueName}: tried to clear {avId}, who was not listed.")
            return

        self.notify.debug(f"{self.uniqueName}: clearing avatar {avId}")
        self.pendingToons.remove(avId)
        if len(self.pendingToons) == 0:
            self.notify.debug(f"{self.uniqueName}: barrier cleared by {self.avIdList}")
            self.cleanup()
            if self.clearedFunc:
                self.clearedFunc()
            if self.doneFunc:
                self.doneFunc(self.avIdList)

    def isActive(self):
        return self.active

    def getPendingToons(self):
        return self.pendingToons[:]

    def __timerExpired(self, task):
        self.notify.warning(f"{self.uniqueName}: timeout expired; responses not received from {self.pendingToons}")
        self.cleanup()
        if self.timeoutFunc:
            self.timeoutFunc(self.pendingToons[:])
        if self.doneFunc:
            clearedAvIds = self.avIdList[:]
            for avId in self.pendingToons:
                clearedAvIds.remove(avId)
            self.doneFunc(clearedAvIds)

        return Task.done

    def __handleUnexpectedExit(self, avId):
        if avId not in self.avIdList:
            return

        self.avIdList.remove(avId)
        if avId in self.pendingToons:
            self.clear(avId)
