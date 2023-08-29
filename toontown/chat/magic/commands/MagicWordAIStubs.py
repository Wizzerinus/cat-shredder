from enum import Enum

from toontown.chat.magic.MagicBase import MagicWordLocation, MagicWordParameter, MagicWordRegistry, MagicWordStub
from toontown.chat.magic.MagicWordTypes import MWTInteger
from toontown.toonbase.globals.TTGlobalsCore import AccessLevels


class InstanceArguments(Enum):
    seed = "seed"


@MagicWordRegistry.stub("sethp", "hp", "setlaff", "laff")
class SetHPStub(MagicWordStub):
    description = "Sets the health/laff points of target toon"

    signature = [
        MagicWordParameter(MWTInteger(minValue=0), "hp", "The target HP of the toon"),
    ]
    location = MagicWordLocation.SERVER
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("setmaxhp", "maxhp", "setmaxlaff", "maxlaff")
class MaxHPStub(MagicWordStub):
    description = "Sets the max health/max laff points of target toon"

    signature = [
        MagicWordParameter(MWTInteger(minValue=15, maxValue=137), "maxhp", "The target Maximum HP of the toon"),
    ]
    location = MagicWordLocation.SERVER
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("toonup", "tu", "heal")
class ToonUpStub(MagicWordStub):
    description = "Fully heals the target toon"

    location = MagicWordLocation.SERVER
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("immortal")
class ImmortalStub(MagicWordStub):
    description = "The toon becomes immortal"

    location = MagicWordLocation.SERVER
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("god", "godmode")
class GodStub(MagicWordStub):
    description = "The toon becomes immortal and fast"

    location = MagicWordLocation.SERVER
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("rcr")
class RestartCraneRoundStub(MagicWordStub):
    description = "Restarts a crane round in CFO"

    location = MagicWordLocation.SERVER
    permissionLevel = AccessLevels.DEVELOPER
