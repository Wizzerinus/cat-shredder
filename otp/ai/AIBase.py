import builtins
import time

from direct.interval.IntervalManager import ivalMgr
from direct.showbase.EventManagerGlobal import eventMgr
from direct.showbase.JobManagerGlobal import jobMgr
from direct.showbase.MessengerGlobal import messenger
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import (
    ClockObject,
    ConfigVariableBool,
    GraphicsEngine,
    NodePath,
    PandaNode,
    TrueClock,
    VirtualFileSystem,
)
from pandac.PandaModules import getConfigShowbase


class AIBase:
    notify = directNotify.newCategory("AIBase")

    def __init__(self):
        self.config = getConfigShowbase()
        builtins.__dev__ = ConfigVariableBool("want-dev", __debug__).value
        vfs = VirtualFileSystem.getGlobalPtr()

        self.AISleep = 0.04
        self.eventMgr = eventMgr
        self.messenger = messenger

        self.taskMgr = taskMgr

        self.sfxManagerList = None
        self.musicManager = None
        self.jobMgr = jobMgr

        self.hidden = NodePath("hidden")

        self.graphicsEngine = GraphicsEngine()

        clock = ClockObject.getGlobalClock()

        self.trueClock = TrueClock.getGlobalPtr()
        clock.setRealTime(self.trueClock.getShortTime())
        clock.setAverageFrameRateInterval(30.0)
        clock.tick()

        taskMgr.globalClock = clock

        builtins.globalClock = clock
        builtins.vfs = vfs
        builtins.hidden = self.hidden

        self.restart()

    def __sleepCycleTask(self, task):
        time.sleep(self.AISleep)
        return task.cont

    @staticmethod
    def __resetPrevTransform(task):
        PandaNode.resetAllPrevTransform()
        return task.cont

    @staticmethod
    def __ivalLoop(task):
        ivalMgr.step()
        return task.cont

    def __igLoop(self, task):
        self.graphicsEngine.renderFrame()
        return task.cont

    def shutdown(self):
        self.taskMgr.remove("ivalLoop")
        self.taskMgr.remove("igLoop")
        self.taskMgr.remove("aiSleep")
        self.eventMgr.shutdown()

    def restart(self):
        self.shutdown()
        self.taskMgr.add(self.__resetPrevTransform, "resetPrevTransform", priority=-51)
        self.taskMgr.add(self.__ivalLoop, "ivalLoop", priority=20)
        self.taskMgr.add(self.__igLoop, "igLoop", priority=50)
        if self.AISleep >= 0:
            self.taskMgr.add(self.__sleepCycleTask, "aiSleep", priority=55)

        self.eventMgr.restart()

    def run(self):
        self.taskMgr.run()
