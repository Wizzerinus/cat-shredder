import builtins
import os
from panda3d.core import loadPrcFileData


class Game:
    name = "toontown"
    process = "ai"


builtins.game = Game()

if override := os.getenv("DIRECTNOTIFY_LEVEL_OVERRIDE", ""):
    loadPrcFileData("", f"default-directnotify-level {override}")

import otp.ai.AIBaseGlobal  # noqa: F401
from toontown.ai.ToontownAIRepository import ToontownAIRepository  # noqa: F401
from toontown.chat.magic import MagicWordImportsAI  # noqa: F401
from otp.otpbase import PythonUtil  # noqa: F401


PythonUtil.configureLogs("server")

astronHost = os.getenv("ASTRON_HOST", "127.0.0.1")
simbase.districtDoId = int(os.getenv("AIR_BASE_CHANNEL", 401000000))
simbase.air = ToontownAIRepository(simbase.districtDoId, 4002, os.getenv("DISTRICT_NAME", "Solar Summit"))
simbase.air.connect(astronHost, 7100)


simbase.run()
