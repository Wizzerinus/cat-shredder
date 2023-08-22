import builtins
import sys

from direct.gui import DirectGuiGlobals
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *

from toontown.toonbase import ToontownPreconfigure  # noqa: F401
from toontown.chat.magic import MagicWordImports  # noqa: F401
from toontown.distributed import ToontownClientRepository

if base.win is None:
    print("Unable to open window; aborting.")
    sys.exit()

mainBackground = OnscreenImage("phase_3/maps/background.png")
mainBackground.setScale(2, 1, 1)
gameLogo = OnscreenImage(parent=mainBackground, image="phase_3/maps/toontown-logo.png", scale=(1.2, 0.6, 0.6))
gameLogo.setTransparency(TransparencyAttrib.MAlpha)
gameLogo.reparentTo(aspect2d)
base.graphicsEngine.renderFrame()

DirectGuiGlobals.setDefaultRolloverSound(base.loader.loadSfx("phase_3/audio/sfx/GUI_rollover.ogg"))
DirectGuiGlobals.setDefaultClickSound(base.loader.loadSfx("phase_3/audio/sfx/GUI_create_toon_fwd.ogg"))
DirectGuiGlobals.setDefaultDialogGeom(loader.loadModel("phase_3/models/gui/dialog_box_gui"))


# Play music at startup
# This is a bit strange because the music is created here, then
# handed off to the cr to control. This is done so keep the music
# from skipping (if we stopped it and restarted it).
if base.musicManagerIsValid:
    music = base.musicManager.getSound("phase_3/audio/bgm/tt_theme.ogg")
    if music:
        music.setLoop(1)
        music.setVolume(0.9)
        music.play()
    print("ToontownStart: Loading default gui sounds")
    DirectGuiGlobals.setDefaultRolloverSound(base.loader.loadSfx("phase_3/audio/sfx/GUI_rollover.ogg"))
    DirectGuiGlobals.setDefaultClickSound(base.loader.loadSfx("phase_3/audio/sfx/GUI_create_toon_fwd.ogg"))
else:
    music = None

serverVersion = ConfigVariableString("server-version", "no_version_set").getValue()
print("ToontownStart: serverVersion: ", serverVersion)
version = OnscreenText(
    serverVersion, pos=(-1.3, -0.975), scale=0.06, fg=Vec4(1, 1, 1, 1), shadow=(0.5, 0.5, 0.5, 1), align=TextNode.ALeft
)

base.cr = ToontownClientRepository.ToontownClientRepository(serverVersion)
base.cr.music = music

base.initNametagGlobals()

base.startShow(base.cr)

mainBackground.reparentTo(hidden)
mainBackground.removeNode()
del mainBackground
gameLogo.reparentTo(hidden)
gameLogo.removeNode()
del gameLogo
version.cleanup()
del version

builtins.loader = base.loader

base.run()
