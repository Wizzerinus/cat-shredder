import builtins

from direct.gui import DirectGuiGlobals

from otp.otpbase import PythonUtil
from toontown.toonbase import ConfigureUberGlobals  # noqa: F401
from toontown.toonbase import ToonBase
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont

# set up logging
PythonUtil.configureLogs("user", __debug__)


class Game:
    name = "toontown"
    process = "client"


builtins.game = Game()

DirectGuiGlobals.setDefaultFontFunc(getInterfaceFont)

ToonBase.ToonBase()
