from typing import Tuple

from direct.showbase.InputStateGlobal import inputState

from toontown.chat.magic.MagicBase import MagicWord, formatBool
from toontown.chat.magic.commands.MagicWordClientStubs import *
from toontown.coghq.DistributedLobbyManager import DistributedLobbyManager


@MagicWordRegistry.command
class FPSMeter(MagicWord, FPSMeterStub):
    def invoke(self) -> Tuple[bool, str]:
        base.setFrameRateMeter(not base.frameRateMeter)
        return True, formatBool("FPS Meter", base.frameRateMeter)


@MagicWordRegistry.command
class OOBE(MagicWord, OOBEStub):
    def invoke(self) -> Tuple[bool, str]:
        base.oobe()
        return True, formatBool("OOBE Mode", base.oobeMode)


@MagicWordRegistry.command
class Run(MagicWord, RunStub):
    def invoke(self) -> Tuple[bool, str]:
        currentValue = inputState.isSet("debugRunning")
        newValue = self.args["forceValue"] if self.args["forceValue"] is not None else not currentValue
        inputState.set("debugRunning", newValue)
        return True, formatBool("Sprint mode", newValue)


@MagicWordRegistry.command
class Clip(MagicWord, ClipStub):
    def invoke(self) -> Tuple[bool, str]:
        value = self.toon.toggleCollisions()
        if value is None:
            return False, "The toon does not have current controls!"
        return True, formatBool("Noclip mode", value)


@MagicWordRegistry.command
class Limeade(MagicWord, LimeadeStub):
    def invoke(self) -> Tuple[bool, str]:
        try:
            import limeade
        except ImportError:
            return False, "Limeade not installed on the client."
        limeade.refresh()
        return True, "Successfully reloaded code on the client!"


@MagicWordRegistry.command
class Logout(MagicWord, LogoutStub):
    def invoke(self) -> Tuple[bool, str]:
        base.cr._userLoggingOut = True
        base.localAvatar.b_setAnimState("TeleportOut", 1, callback=lambda: base.cr.gameFSM.request("closeShard"))
        return True, "Successfully logged out!"


@MagicWordRegistry.command
class StartBoss(MagicWord, StartBossStub):
    def invoke(self) -> Tuple[bool, str]:
        for item in base.cr.doId2do.values():
            if isinstance(item, DistributedLobbyManager):
                break
        else:
            return False, "Lobby manager not found in this area!"

        item.d_requestSoloBoss()
        return True, "Successfully started a new boss run!"
