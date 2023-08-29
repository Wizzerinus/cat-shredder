from typing import Tuple

from toontown.chat.magic.MagicBase import MagicWord, formatBool
from toontown.chat.magic.commands.MagicWordAIStubs import *
from toontown.chat.magic.commands.MagicWordClientStubs import LimeadeStub
from toontown.coghq.cfo.DistributedCashbotBossAI import DistributedCashbotBossAI


@MagicWordRegistry.command
class Limeade(MagicWord, LimeadeStub):
    def invoke(self) -> Tuple[bool, str]:
        try:
            import limeade
        except ImportError:
            return False, "Limeade not installed on the server."
        limeade.refresh()
        return True, "Successfully reloaded code on the server!"


@MagicWordRegistry.command
class SetHP(MagicWord, SetHPStub):
    def invoke(self) -> Tuple[bool, str]:
        if self.args["hp"] <= 0 and self.toon.getImmortalMode():
            return False, "Cannot lower an immortal toon below 1!"

        if self.args["hp"] > self.toon.getMaxHp():
            return False, f"Cannot set the maximum laff of the toon over {self.toon.getMaxHp()}!"

        self.toon.b_setHp(self.args["hp"])
        return True, "Successfully changed the health!"


@MagicWordRegistry.command
class SetMaxHP(MagicWord, MaxHPStub):
    def invoke(self) -> Tuple[bool, str]:
        self.toon.b_setMaxHp(self.args["maxhp"])
        self.toon.toonUp(self.args["maxhp"])
        return True, "Successfully changed the maximum health!"


@MagicWordRegistry.command
class ToonUp(MagicWord, ToonUpStub):
    def invoke(self) -> Tuple[bool, str]:
        self.toon.toonUp(self.toon.getMaxHp())
        return True, "Successfully healed the toon!"


@MagicWordRegistry.command
class Immortal(MagicWord, ImmortalStub):
    def invoke(self) -> Tuple[bool, str]:
        self.toon.setImmortalMode(not self.toon.getImmortalMode())
        return True, formatBool("Immortal mode", self.toon.getImmortalMode())


@MagicWordRegistry.command
class God(MagicWord, GodStub):
    def invoke(self) -> Tuple[bool, str]:
        self.toon.setImmortalMode(not self.toon.getImmortalMode())
        self.addClientsideCommand("run", [bytes(self.toon.getImmortalMode())])
        return True, formatBool("God mode", self.toon.getImmortalMode())


@MagicWordRegistry.command
class RestartCraneRound(MagicWord, RestartCraneRoundStub):
    def invoke(self) -> Tuple[bool, str]:
        for boss in simbase.air.doFindAllInstances(DistributedCashbotBossAI):
            if self.toon.doId in boss.involvedToons:
                break
        else:
            return False, "You aren't in a CFO!"

        boss.b_setState("Off")
        boss.b_setState("BattleThree")
        return True, "Successfully restarted the crane round"
