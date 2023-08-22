import builtins
import os


class Game:
    name = "toontown"
    process = "uberdog"


builtins.game = Game()

from panda3d.core import loadPrcFile, loadPrcFileData

loadPrcFile("etc/Configrc.prc")

if override := os.getenv("DIRECTNOTIFY_LEVEL_OVERRIDE", ""):
    loadPrcFileData("", f"notify-level {override}")
    loadPrcFileData("", f"default-directnotify-level {override}")

localPrc = "etc/local.prc"
if os.path.exists(localPrc):
    loadPrcFile(localPrc)

import otp.uberdog.UberDogGlobal  # noqa: F401
from toontown.uberdog.ToontownUDRepository import ToontownUDRepository

astronHost = os.getenv("ASTRON_HOST", "127.0.0.1")
uber.air = ToontownUDRepository(1000000, 4002)
uber.air.connect(astronHost, 7100)

uber.run()
