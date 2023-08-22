import builtins

from direct.showbase import Loader
from panda3d.core import loadPrcFileData

from toontown.toonbase import ConfigureUberGlobals  # noqa: F401
from otp.ai.AIBase import AIBase

if not __debug__:
    loadPrcFileData("", "want-dev false")


builtins.simbase = AIBase()
builtins.taskMgr = simbase.taskMgr
builtins.jobMgr = simbase.jobMgr
builtins.eventMgr = simbase.eventMgr
builtins.messenger = simbase.messenger

simbase.loader = Loader.Loader(simbase)
builtins.loader = simbase.loader

directNotify.setDconfigLevels()


if (not __debug__) and __dev__:
    notify = directNotify.newCategory("ShowBaseGlobal")
    notify.error("You must set 'want-dev' to false in non-debug mode.")


taskMgr.finalInit()
