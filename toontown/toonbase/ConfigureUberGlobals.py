import builtins
import os

from direct.directnotify import DirectNotifyGlobal
from panda3d.core import ConfigVariableBool, loadPrcFile

builtins.directNotify = DirectNotifyGlobal.directNotify

if ConfigVariableBool("enable-config-loading", True):
    loadPrcFile("etc/Configrc.prc")

    localPrc = "etc/local.prc"

    if os.path.exists(localPrc):
        loadPrcFile(localPrc)
