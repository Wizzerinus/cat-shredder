from toontown.chat.magic.MagicBase import MagicWordLocation, MagicWordParameter, MagicWordRegistry, MagicWordStub
from toontown.chat.magic.MagicWordTypes import MWTBool
from toontown.toonbase.globals.TTGlobalsCore import AccessLevels


@MagicWordRegistry.stub("fps", "fpsmeter", "togglefps", "togglefpsmeter")
class FPSMeterStub(MagicWordStub):
    description = "Toggles the FPS meter"

    location = MagicWordLocation.CLIENT
    permissionLevel = AccessLevels.USER


@MagicWordRegistry.stub("oobe", "toggleoobe")
class OOBEStub(MagicWordStub):
    description = "Toggles the OOBE camera mode, which allows moving the camera anywhere on the map"

    location = MagicWordLocation.CLIENT
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("run", "fast", "togglerun", "togglefast")
class RunStub(MagicWordStub):
    description = """
    Toggles increased movement speed (speed is multiplied by 4 in this mode). Can be enabled by using /god
    """
    signature = [
        MagicWordParameter(
            MWTBool(), "forceValue", "Force the value, by default flips the current run state", default=None
        ),
    ]

    location = MagicWordLocation.CLIENT
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("clip", "noclip", "collisions", "toggleclip", "togglecollisions")
class ClipStub(MagicWordStub):
    description = "Toggles noclip mode, disabling all ingame collisions with the player's toon"

    location = MagicWordLocation.CLIENT
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("limeade", "reload", "codereload")
class LimeadeStub(MagicWordStub):
    description = "Reloads the game code on the client and the server using Limeade"

    locations = [MagicWordLocation.CLIENT, MagicWordLocation.SERVER]
    permissionLevel = AccessLevels.DEVELOPER


@MagicWordRegistry.stub("logout", "logoff")
class LogoutStub(MagicWordStub):
    description = "Logs out of the game"

    location = MagicWordLocation.CLIENT
    permissionLevel = AccessLevels.USER
