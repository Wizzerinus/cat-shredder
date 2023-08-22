import random

from direct.fsm import StateData
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals.TTGlobalsGUI import getSignFont
from . import AvatarChoice

MAX_AVATARS = 6
POSITIONS = (
    Vec3(-0.840167, 0, 0.359333),
    Vec3(0.00933349, 0, 0.306533),
    Vec3(0.862, 0, 0.3293),
    Vec3(-0.863554, 0, -0.445659),
    Vec3(0.00999999, 0, -0.5181),
    Vec3(0.864907, 0, -0.445659),
)

COLORS = (
    Vec4(0.917, 0.164, 0.164, 1),
    Vec4(0.152, 0.750, 0.258, 1),
    Vec4(0.598, 0.402, 0.875, 1),
    Vec4(0.133, 0.590, 0.977, 1),
    Vec4(0.895, 0.348, 0.602, 1),
    Vec4(0.977, 0.816, 0.133, 1),
)

chooser_notify = directNotify.newCategory("AvatarChooser")


class AvatarChooser(StateData.StateData):
    """
    AvatarChooser class: display a list of avatars and return the user's
    choice or let the user make a new avatar
    """

    def __init__(self, avatarList, parentFSM, doneEvent):
        """
        Set-up the login screen interface and prompt for a user name
        """
        StateData.StateData.__init__(self, doneEvent)

        self.choice = None
        self.avatarList = avatarList

        if __debug__:
            base.avChooser = self

    def enter(self):
        assert chooser_notify.debug("enter()")
        self.notify.info("AvatarChooser.enter")

        if self.isLoaded == 0:
            self.load()

        base.disableMouse()

        self.title.reparentTo(aspect2d)
        self.quitButton.show()

        self.pickAToonBG.setBin("background", 1)
        base.setBackgroundColor(Vec4(0.145, 0.368, 0.78, 1))

        for panel in self.panelList:
            panel.show()
            self.accept(panel.doneEvent, self.__handlePanelDone)

    def exit(self):
        """
        Remove event hooks and restore display
        """
        assert chooser_notify.debug("enter()")
        if self.isLoaded == 0:
            return

        for panel in self.panelList:
            panel.hide()

        self.ignoreAll()

        self.title.reparentTo(hidden)
        self.quitButton.hide()
        base.setBackgroundColor((0, 0, 0, 1))

        self.pickAToonBG.reparentTo(hidden)

    def load(self):
        assert chooser_notify.debug("load()")
        if self.isLoaded == 1:
            return

        gui = loader.loadModel("phase_3/models/gui/pick_a_toon_gui")
        gui2 = loader.loadModel("phase_3/models/gui/quit_button")
        newGui = loader.loadModel("phase_3/models/gui/tt_m_gui_pat_mainGui")
        self.pickAToonBG = OnscreenImage("phase_3/maps/tt_t_gui_pat_background.png")
        self.pickAToonBG.reparentTo(hidden)
        self.pickAToonBG.setScale(1, 1, 1)

        self.title = OnscreenText(
            TTLocalizer.AvatarChooserPickAToon,
            scale=0.15,
            parent=hidden,
            font=getSignFont(),
            fg=(1, 0.9, 0.1, 1),
            pos=(0.0, 0.82),
        )

        quitHover = gui.find("**/QuitBtn_RLVR")

        self.quitButton = DirectButton(
            image=(quitHover, quitHover, quitHover),
            relief=None,
            text=TTLocalizer.AvatarChooserQuit,
            text_font=getSignFont(),
            text_fg=(0.977, 0.816, 0.133, 1),
            text_pos=(0, -0.035),
            text_scale=0.1,
            image_scale=1,
            image1_scale=1.05,
            image2_scale=1.05,
            scale=1.05,
            pos=(1.08, 0, -0.907),
            command=self.__handleQuit,
        )

        gui.removeNode()
        gui2.removeNode()
        newGui.removeNode()

        self.panelList = []
        used_position_indexs = []

        for av in self.avatarList:
            okToLockout = 0

            panel = AvatarChoice.AvatarChoice(av, position=av.position, paid=True, okToLockout=okToLockout)
            panel.setPos(POSITIONS[av.position])
            used_position_indexs.append(av.position)
            self.panelList.append(panel)

        for panelNum in range(0, MAX_AVATARS):
            if panelNum not in used_position_indexs:
                panel = AvatarChoice.AvatarChoice(position=panelNum, paid=True)
                panel.setPos(POSITIONS[panelNum])
                self.panelList.append(panel)

        if len(self.avatarList) > 0:
            self.initLookAtInfo()
        self.isLoaded = 1

    def getLookAtPosition(self, toonHead, toonidx):
        lookAtChoice = random.random()

        if len(self.used_panel_indexs) == 1:
            lookFwdPercent = 0.33
            lookAtOthersPercent = 0
        else:
            lookFwdPercent = 0.20

            lookAtOthersPercent = 0.4 if len(self.used_panel_indexs) == 2 else 0.65

        lookRandomPercent = 1.0 - lookFwdPercent - lookAtOthersPercent

        if lookAtChoice < lookFwdPercent:
            self.IsLookingAt[toonidx] = "f"
            return Vec3(0, 1.5, 0)
        if lookAtChoice < (lookRandomPercent + lookFwdPercent) or (len(self.used_panel_indexs) == 1):
            self.IsLookingAt[toonidx] = "r"
            return toonHead.getRandomForwardLookAtPoint()

        other_toon_idxs = []
        for i in range(len(self.IsLookingAt)):
            if self.IsLookingAt[i] == toonidx:
                other_toon_idxs.append(i)

        IgnoreStarersPercent = 0.4 if len(other_toon_idxs) == 1 else 0.2

        NoticeStarersPercent = 0.5
        bStareTargetTurnsToMe = 0

        if (len(other_toon_idxs) == 0) or (random.random() < IgnoreStarersPercent):
            other_toon_idxs = []
            for i in self.used_panel_indexs:
                if i != toonidx:
                    other_toon_idxs.append(i)

            if random.random() < NoticeStarersPercent:
                bStareTargetTurnsToMe = 1

        if len(other_toon_idxs) == 0:
            return toonHead.getRandomForwardLookAtPoint()

        lookingAtIdx = random.choice(other_toon_idxs)
        if bStareTargetTurnsToMe:
            self.IsLookingAt[lookingAtIdx] = toonidx
            otherToonHead = None
            for panel in self.panelList:
                if panel.position == lookingAtIdx:
                    otherToonHead = panel.headModel
            otherToonHead.doLookAroundToStareAt(otherToonHead, self.getLookAtToPosVec(lookingAtIdx, toonidx))

        self.IsLookingAt[toonidx] = lookingAtIdx
        return self.getLookAtToPosVec(toonidx, lookingAtIdx)

    def getLookAtToPosVec(self, fromIdx, toIdx):
        x = -(POSITIONS[toIdx][0] - POSITIONS[fromIdx][0])
        y = POSITIONS[toIdx][1] - POSITIONS[fromIdx][1]
        z = POSITIONS[toIdx][2] - POSITIONS[fromIdx][2]
        return Vec3(x, y, z)

    def initLookAtInfo(self):
        self.used_panel_indexs = []

        for panel in self.panelList:
            if panel.dna is not None:
                self.used_panel_indexs.append(panel.position)

        if len(self.used_panel_indexs) == 0:
            return

        self.IsLookingAt = []
        for _i in range(MAX_AVATARS):
            self.IsLookingAt.append("f")

        for panel in self.panelList:
            if panel.dna is not None:
                panel.headModel.setLookAtPositionCallbackArgs((self, panel.headModel, panel.position))

    def unload(self):
        assert chooser_notify.debug("unload()")
        if self.isLoaded == 0:
            return

        cleanupDialog("globalDialog")

        for panel in self.panelList:
            panel.destroy()
        del self.panelList

        self.title.removeNode()
        del self.title
        self.quitButton.destroy()
        del self.quitButton

        self.pickAToonBG.removeNode()
        del self.pickAToonBG

        del self.avatarList

        self.ignoreAll()
        self.isLoaded = 0

        ModelPool.garbageCollect()
        TexturePool.garbageCollect()
        base.setBackgroundColor((0, 0, 0, 1))

    def __handlePanelDone(self, panelDoneStatus, panelChoice=0):
        """
        Take appropriate action based on panel action (choose, delete,
        or create)
        """
        assert chooser_notify.debug(
            "__handlePanelDone(panelDoneStatus=%s, panelChoice=%s)" % (panelDoneStatus, panelChoice)
        )
        self.doneStatus = {}
        self.doneStatus["mode"] = panelDoneStatus
        self.choice = panelChoice
        if panelDoneStatus == "chose":
            self.__handleChoice()
        elif panelDoneStatus == "delete":
            self.__handleDelete()
        elif panelDoneStatus == "create":
            self.__handleCreate()

    def getChoice(self):
        return self.choice

    def __handleChoice(self):
        """
        Process the choice returned from the pick list
        """
        assert chooser_notify.debug("__handleChoice()")
        base.transitions.fadeOut(finishIval=EventInterval(self.doneEvent, [self.doneStatus]))

    def __handleCreate(self):
        base.transitions.fadeOut(finishIval=EventInterval(self.doneEvent, [self.doneStatus]))

    def __handleDelete(self):
        """
        Handle create or delete buttons
        """
        messenger.send(self.doneEvent, [self.doneStatus])

    def __handleQuit(self):
        cleanupDialog("globalDialog")
        self.doneStatus = {"mode": "exit"}
        messenger.send(self.doneEvent, [self.doneStatus])

    def enterChoose(self):
        pass

    def exitChoose(self):
        pass
