"""ToonBase module: contains the ToonBase class"""
import os
import platform
import subprocess
import sys
from ctypes import cdll

from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.otp import *

from otp.otpbase import OTPBase
from toontown.toonbase.Hotkeys import HotkeyManager
from toontown.toonbase.Settings import Settings
from toontown.toonbase.ToonControlManager import ToonControlManager
from toontown.toonbase.globals.TTGlobalsCore import DisconnectCloseWindow, DisconnectGraphicsError
from toontown.toonbase.globals.TTGlobalsMovement import *
from toontown.toonbase.globals.TTGlobalsRender import DefaultCameraFar, DefaultCameraFov, DefaultCameraNear


class ToonBase(OTPBase.OTPBase):
    """ToonBase class"""

    notify = directNotify.newCategory("ToonBase")
    localAvatar = None

    def __init__(self):
        """__init__(self)
        ToonBase constructor: create a toon and launch it into the world
        """
        if not config.GetInt("ignore-user-options", 0):
            self.settings = Settings()
            self.loadFromSettings()
        else:
            self.settings = None
        OTPBase.OTPBase.__init__(self)

        if not self.isMainWindowOpen():
            try:
                launcher.setPandaErrorCode(7)
            except:
                pass
            sys.exit(1)

        self.disableShowbaseMouse()
        self.addCullBins()

        self.toonChatSounds = self.config.GetBool("toon-chat-sounds", 1)

        self.wantDynamicShadows = 0
        self.exitErrorCode = 0

        camera.setPosHpr(0, 0, 0, 0, 0, 0)
        self.camLens.setMinFov(DefaultCameraFov / (4.0 / 3.0))
        self.camLens.setNearFar(DefaultCameraNear, DefaultCameraFar)

        musicVolume = self.settings.getFloat("musicVolume", 1.0)
        sfxVolume = self.settings.getFloat("sfxVolume", 1.0)
        self.musicManager.setVolume(musicVolume)
        for sfm in self.sfxManagerList:
            sfm.setVolume(sfxVolume)
        self.sfxActive = sfxVolume > 0.0
        self.hotkeyManager = HotkeyManager()
        self.SCREENSHOT = None
        self.reloadControls()
        self.controlManager = ToonControlManager()
        self.setBackgroundColor((0, 0, 0, 1))

        tpm = TextPropertiesManager.getGlobalPtr()
        candidateActive = TextProperties()
        candidateActive.setTextColor(0, 0, 1, 1)
        tpm.setProperties("candidate_active", candidateActive)
        candidateInactive = TextProperties()
        candidateInactive.setTextColor(0.3, 0.3, 0.7, 1)
        tpm.setProperties("candidate_inactive", candidateInactive)

        self.transitions.IrisModelName = "phase_3/models/misc/iris"
        self.transitions.FadeModelName = "phase_3/models/misc/fade"

        self.exitFunc = self.userExit

        globalClock.setMaxDt(0.2)

        if self.config.GetBool("want-particles", 1) == 1:
            self.notify.debug("Enabling particles")
            self.enableParticles()

        self.accept("panda3d-render-error", self.panda3dRenderError)

        self.slowQuietZone = self.config.GetBool("slow-quiet-zone", 0)
        self.slowQuietZoneDelay = self.config.GetFloat("slow-quiet-zone-delay", 5)

        self.killInterestResponse = self.config.GetBool("kill-interest-response", 0)

        tpMgr = TextPropertiesManager.getGlobalPtr()

        WLDisplay = TextProperties()
        WLDisplay.setSlant(0.3)

        WLEnter = TextProperties()
        WLEnter.setTextColor(1.0, 0.0, 0.0, 1)

        tpMgr.setProperties("WLDisplay", WLDisplay)
        tpMgr.setProperties("WLEnter", WLEnter)
        cogGray = TextProperties()
        cogGray.setTextColor(0, 0.2, 0.2, 1)
        cogGray.setShadow(0.01)
        tpMgr.setProperties("cogGray", cogGray)
        self.lastScreenShotTime = globalClock.getRealTime()
        self.accept("InputState-forward", self.__walking)
        self.canScreenShot = 1
        self.glitchCount = 0
        self.walking = 0
        self.isSprinting = 0
        self.accept(self.SPRINT, self.startSprint)
        self.accept(f"{self.SPRINT}-up", self.stopSprint)
        if self.settings.getBool("frameRateMeter", False):
            base.setFrameRateMeter(True)
        else:
            base.setFrameRateMeter(False)

        self.wantWASD = (
            base.MOVE_FORWARD != "arrow_up"
            and base.MOVE_BACKWARDS != "arrow_down"
            and base.MOVE_LEFT != "arrow_left"
            and base.MOVE_RIGHT != "arrow_right"
        )
        self.accept("winow-event", self.windowEvent)

    def reloadControls(self):
        self.ignore(self.SCREENSHOT)
        self.MOVE_FORWARD = self.hotkeyManager.getKeyName("move_forward", "arrow_up")
        self.MOVE_BACKWARDS = self.hotkeyManager.getKeyName("move_backwards", "arrow_down")
        self.MOVE_LEFT = self.hotkeyManager.getKeyName("move_left", "arrow_left")
        self.MOVE_RIGHT = self.hotkeyManager.getKeyName("move_right", "arrow_right")
        self.JUMP = self.hotkeyManager.getKeyName("jump", "control")
        self.SPRINT = self.hotkeyManager.getKeyName("sprint", "shift")
        self.CHAT = self.hotkeyManager.getKeyName("open_chat", "t")
        self.SCREENSHOT = self.hotkeyManager.getKeyName("make_screenshot", "f12")
        self.accept(self.SCREENSHOT, self.takeScreenShot)

    def disableShowbaseMouse(self):
        self.useDrive()
        self.disableMouse()
        if self.mouseInterface:
            self.mouseInterface.detachNode()
        if base.mouse2cam:
            self.mouse2cam.detachNode()

    def addCullBins(self):
        cullBinMgr = CullBinManager.getGlobalPtr()
        cullBinMgr.addBin("gui-popup", CullBinManager.BTUnsorted, 60)
        cullBinMgr.addBin("shadow", CullBinManager.BTFixed, 15)
        cullBinMgr.addBin("ground", CullBinManager.BTFixed, 14)

    def __walking(self, pressed):
        self.walking = pressed

    def takeScreenShot(self):
        if not os.path.exists("user/screenshots/"):
            os.mkdir("user")
            os.mkdir("user/logs")
        namePrefix = "screenshot"
        namePrefix = "user/screenshots/" + namePrefix

        timedif = globalClock.getRealTime() - self.lastScreenShotTime
        if self.glitchCount > 10 and self.walking:
            return
        if timedif < 1.0 and self.walking:
            self.glitchCount += 1
            return
        if not hasattr(self, "localAvatar"):
            self.screenshot(namePrefix=namePrefix)
            self.lastScreenShotTime = globalClock.getRealTime()
            return
        coordOnScreen = self.config.GetBool("screenshot-coords", 0)

        self.localAvatar.stopThisFrame = 1

        ctext = self.localAvatar.getAvPosStr()

        self.screenshotStr = ""
        messenger.send("takingScreenshot")

        if coordOnScreen:
            coordTextLabel = DirectLabel(
                pos=(-0.81, 0.001, -0.87),
                text=ctext,
                text_scale=0.05,
                text_fg=VBase4(1.0, 1.0, 1.0, 1.0),
                text_bg=(0, 0, 0, 0),
                text_shadow=(0, 0, 0, 1),
                relief=None,
            )
            coordTextLabel.setBin("gui-popup", 0)
            strTextLabel = None
            if len(self.screenshotStr):
                strTextLabel = DirectLabel(
                    pos=(0.0, 0.001, 0.9),
                    text=self.screenshotStr,
                    text_scale=0.05,
                    text_fg=VBase4(1.0, 1.0, 1.0, 1.0),
                    text_bg=(0, 0, 0, 0),
                    text_shadow=(0, 0, 0, 1),
                    relief=None,
                )
                strTextLabel.setBin("gui-popup", 0)

        self.graphicsEngine.renderFrame()
        self.screenshot(namePrefix=namePrefix, imageComment=ctext + " " + self.screenshotStr)
        self.lastScreenShotTime = globalClock.getRealTime()

        if coordOnScreen:
            if strTextLabel is not None:
                strTextLabel.destroy()
            coordTextLabel.destroy()

    def addScreenshotString(self, str):
        if len(self.screenshotStr):
            self.screenshotStr += "\n"
        self.screenshotStr += str

    def initNametagGlobals(self):
        """
        Should be called once during startup to initialize a few
        defaults for the Nametags.
        """

        arrow = loader.loadModel("phase_3/models/props/arrow")
        card = loader.loadModel("phase_3/models/props/panel")
        speech3d = ChatBalloon(loader.loadModel("phase_3/models/props/chatbox").node())
        thought3d = ChatBalloon(loader.loadModel("phase_3/models/props/chatbox_thought_cutout").node())
        speech2d = ChatBalloon(loader.loadModel("phase_3/models/props/chatbox_noarrow").node())

        chatButtonGui = loader.loadModel("phase_3/models/gui/chat_button_gui")

        NametagGlobals.setCamera(self.cam)
        NametagGlobals.setArrowModel(arrow)
        NametagGlobals.setNametagCard(card, VBase4(-0.5, 0.5, -0.5, 0.5))
        if self.mouseWatcherNode:
            NametagGlobals.setMouseWatcher(self.mouseWatcherNode)
        NametagGlobals.setSpeechBalloon3d(speech3d)
        NametagGlobals.setThoughtBalloon3d(thought3d)
        NametagGlobals.setSpeechBalloon2d(speech2d)
        NametagGlobals.setThoughtBalloon2d(thought3d)
        NametagGlobals.setPageButton(PGButton.SReady, chatButtonGui.find("**/Horiz_Arrow_UP"))
        NametagGlobals.setPageButton(PGButton.SDepressed, chatButtonGui.find("**/Horiz_Arrow_DN"))
        NametagGlobals.setPageButton(PGButton.SRollover, chatButtonGui.find("**/Horiz_Arrow_Rllvr"))
        NametagGlobals.setQuitButton(PGButton.SReady, chatButtonGui.find("**/CloseBtn_UP"))
        NametagGlobals.setQuitButton(PGButton.SDepressed, chatButtonGui.find("**/CloseBtn_DN"))
        NametagGlobals.setQuitButton(PGButton.SRollover, chatButtonGui.find("**/CloseBtn_Rllvr"))

        rolloverSound = DirectGuiGlobals.getDefaultRolloverSound()
        if rolloverSound:
            NametagGlobals.setRolloverSound(rolloverSound)
        clickSound = DirectGuiGlobals.getDefaultClickSound()
        if clickSound:
            NametagGlobals.setClickSound(clickSound)

        NametagGlobals.setToon(self.cam)

        self.marginManager = MarginManager()
        self.margins = self.aspect2d.attachNewNode(self.marginManager, DirectGuiGlobals.MIDGROUND_SORT_INDEX + 1)

        mm = self.marginManager
        self.leftCells = [
            mm.addGridCell(0, 1, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(0, 2, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(0, 3, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
        ]
        self.bottomCells = [
            mm.addGridCell(0.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(1.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(2.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(3.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(4.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
        ]
        self.rightCells = [
            mm.addGridCell(5, 2, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(5, 1, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
        ]
        self.oldAspectRatio = self.get_aspect_ratio()

    def windowEvent(self, win):
        super().windowEvent(win)
        self.reloadNametagCells(win)

    def reloadNametagCells(self, win):
        if self.oldAspectRatio == self.get_aspect_ratio():
            return

        mm = self.marginManager
        for cell in self.leftCells:
            mm.setCellAvailable(cell, False)
        for cell in self.bottomCells:
            mm.setCellAvailable(cell, False)
        for cell in self.rightCells:
            mm.setCellAvailable(cell, False)
        self.leftCells = [
            mm.addGridCell(0, 1, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(0, 2, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(0, 3, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
        ]
        self.bottomCells = [
            mm.addGridCell(0.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(1.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(2.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(3.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(4.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
        ]
        self.rightCells = [
            mm.addGridCell(5, 2, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
            mm.addGridCell(5, 1, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
        ]
        self.oldAspectRatio = self.get_aspect_ratio()

    def setCellsAvailable(self, cell_list, available):
        """setCellsAvailable(self, cell_list, bool available)

        Activates (if available is true) or deactivates (if available
        is false) a list of cells that are to be used for displaying
        margin popups, like red arrows and offscreen chat messages.

        This can be called from time to time to free up real estate
        along the edges of the screen when necessary for special
        purposes.

        cell_list should be a list of cell index numbers.  Suitable
        values are base.leftCells, base.bottomCells, or
        base.rightCells.
        """
        for cell in cell_list:
            self.marginManager.setCellAvailable(cell, available)

    def startShow(self, cr, launcherServer=None):
        self.cr = cr
        base.graphicsEngine.renderFrame()

        gameServer = os.environ.get("TT_GAMESERVER", "127.0.0.1")

        serverPort = ConfigVariableInt("server-port", 6667).value

        serverList = []
        for name in gameServer.split(";"):
            url = URLSpec(name, 1)
            if config.GetBool("want-ssl", "False"):
                url.setScheme("s")
            if not url.hasPort():
                url.setPort(serverPort)
            serverList.append(url)

        cr.loginFSM.request("connect", [serverList])

    def removeGlitchMessage(self):
        self.ignore("InputState-forward")
        print("ignoring InputState-forward")

    def exitShow(self, errorCode=None):
        sys.exit()

    def userExit(self):
        try:
            self.localAvatar.d_setAnimState("TeleportOut", 1)
        except:
            pass

        if self.cr.timeManager:
            self.cr.timeManager.setDisconnectReason(DisconnectCloseWindow)

        base.cr._userLoggingOut = False
        messenger.send("clientLogout")
        self.cr.dumpAllSubShardObjects()

        self.cr.loginFSM.request("shutdown")

        self.notify.warning("Could not request shutdown; exiting anyway.")
        self.exitShow()

    def panda3dRenderError(self):
        launcher.setPandaErrorCode(14)

        if self.cr.timeManager:
            self.cr.timeManager.setDisconnectReason(DisconnectGraphicsError)

        self.cr.sendDisconnect()
        sys.exit()

    def playMusic(self, music, looping=0, interrupt=1, volume=1, time=0.0):
        OTPBase.OTPBase.playMusic(self, music, looping, interrupt, volume, time)

    def playSfx(self, sfx, looping=0, interrupt=1, volume=1, time=0.0, node=None, listener=None, cutoff=None):
        return self.sfxPlayer.playSfx(sfx, looping, interrupt, volume, time, node, listener, cutoff)

    def isMainWindowOpen(self):
        if self.win != None:
            return self.win.isValid()
        return 0

    def startSprint(self):
        if base.localAvatar:
            base.localAvatar.currentSpeed = ToonForwardSpeedSprint
            base.localAvatar.currentReverseSpeed = ToonReverseSpeedSprint
            base.localAvatar.controlManager.setSpeeds(
                ToonForwardSpeedSprint,
                ToonJumpForce,
                ToonReverseSpeedSprint,
                ToonRotateSpeed,
            )
            self.isSprinting = 1
        else:
            if self.isSprinting == 1:
                self.stopSprint()

    def stopSprint(self):
        if base.localAvatar:
            base.localAvatar.currentSpeed = ToonRunSpeed
            base.localAvatar.currentReverseSpeed = ToonReverseSpeed
            base.localAvatar.controlManager.setSpeeds(
                ToonRunSpeed,
                ToonJumpForce,
                ToonReverseSpeed,
                ToonRotateSpeed,
            )
            self.isSprinting = 0

    def getScreenResolution(self):
        platf = platform.system()
        try:
            if platf == "Windows":
                return cdll.user32.GetSystemMetrics(0), cdll.user32.GetSystemMetrics(1)
            elif platf == "Linux":
                sp = subprocess.Popen(
                    r'xrandr | grep "\*" | cut -d" " -f4', shell=True, stdout=subprocess.PIPE
                ).communicate()[0]
                return [int(x) for x in sp.decode("UTF-8").split()[0].split("x")]
            elif platf == "Darwin":
                sp = subprocess.Popen(
                    r"system_profiler SPDisplaysDataType | grep Resolution", shell=True, stdout=subprocess.PIPE
                ).communicate()[0]
                s1 = sp.decode("UTF-8").split(" x ")
                width = s1[0].split(": ")[-1]
                height = s1[1].split(" @ ")[0]
                return int(width), int(height)
        except (OSError, IndexError, ValueError):
            pass

        self.notify.warning(f"Unable to obtain system resolution, our platform: {platf}")
        return 1366, 768

    def loadFromSettings(self):
        if not config.GetInt("ignore-user-options", 0):
            fullscreen = self.settings.getBool("fullscreen", False)
            music = self.settings.getBool("music", True)
            sfx = self.settings.getBool("sfx", True)
            toonChatSounds = self.settings.getBool("toonChatSounds", True)
            musicVolume = self.settings.getFloat("musicVolume", 1.0)
            sfxVolume = self.settings.getFloat("sfxVolume", 1.0)
            width, height = self.getScreenResolution()
            res = self.settings.getList("resolution", [width * 5 / 6, height * 5 / 6], expectedLength=2)
            antialiasing = self.settings.getBool("antialiasing", 0)
            if antialiasing:
                loadPrcFileData("toonBase Settings Framebuffer MSAA", "framebuffer-multisample 1")
                loadPrcFileData("toonBase Settings MSAA Level", "multisamples %i" % antialiasing)
            else:
                loadPrcFileData("toonBase Settings Framebuffer MSAA", "framebuffer-multisample 0")
            loadPrcFileData("toonBase Settings Window Res", "win-size %s %s" % (res[0], res[1]))
            loadPrcFileData("toonBase Settings Window FullScreen", "fullscreen %s" % fullscreen)
            loadPrcFileData("toonBase Settings Music Active", "audio-music-active %s" % music)
            loadPrcFileData("toonBase Settings Sound Active", "audio-sfx-active %s" % sfx)
            loadPrcFileData("toonBase Settings Music Volume", "audio-master-music-volume %s" % musicVolume)
            loadPrcFileData("toonBase Settings Sfx Volume", "audio-master-sfx-volume %s" % sfxVolume)
            loadPrcFileData("toonBase Settings Toon Chat Sounds", "toon-chat-sounds %s" % toonChatSounds)
            loadPrcFileData(f"toonBase Settings Custom Controls", "customControls {wantCustomControls}")
            loadPrcFileData(f"toonBase Settings Controls", "controls {controls}")

            self.settings.loadFromSettings()

    def remakeControlManager(self):
        if not self.controlManager:
            self.controlManager = ToonControlManager()
            self.reloadControls()
