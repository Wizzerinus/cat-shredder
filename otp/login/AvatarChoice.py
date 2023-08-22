from direct.gui.DirectGui import *

from toontown.toon import ToonDNA
from toontown.toon import ToonHead
from toontown.toonbase import TTLocalizer
from toontown.toonbase.globals.TTGlobalsAvatars import ToonBodyScales
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont, getSignFont, getToonFont
from toontown.toontowngui import TTDialog

NAME_ROTATIONS = (7, -11, 1, -5, 3.5, -5)
NAME_POSITIONS = ((0, 0, 0.26), (-0.03, 0, 0.25), (0, 0, 0.27), (-0.03, 0, 0.25), (0.03, 0, 0.26), (0, 0, 0.26))
DELETE_POSITIONS = (
    (0.187, 0, -0.26),
    (0.31, 0, -0.167),
    (0.231, 0, -0.241),
    (0.314, 0, -0.186),
    (0.243, 0, -0.233),
    (0.28, 0, -0.207),
)


class AvatarChoice(DirectButton):
    """
    AvatarChoice class: display an avatar name and head on a panel
    """

    notify = directNotify.newCategory("AvatarChoice")

    NEW_TRIALER_OPEN_POS = (1,)
    OLD_TRIALER_OPEN_POS = (1, 4)

    MODE_CREATE = 0
    MODE_CHOOSE = 1

    def __init__(self, av=None, position=0, paid=0, okToLockout=1):
        """
        Set-up the avatar choice panel. If no av is passed in, offer the
        user the opportunity to create a new one
        """
        DirectButton.__init__(
            self,
            relief=None,
            text="",
            text_font=getSignFont(),
        )
        self.initialiseoptions(AvatarChoice)
        self.hasPaid = paid

        self.mode = None

        if not av:
            self.mode = AvatarChoice.MODE_CREATE
            self.name = ""
            self.dna = None
        else:
            self.mode = AvatarChoice.MODE_CHOOSE
            self.name = av.avName
            self.dna = ToonDNA.ToonDNA(av.dna)

        self.position = position
        self.doneEvent = "avChoicePanel-" + str(self.position)

        self.pickAToonGui = loader.loadModel("phase_3/models/gui/tt_m_gui_pat_mainGui")
        self.buttonBgs = []
        self.buttonBgs.append(self.pickAToonGui.find("**/tt_t_gui_pat_squareRed"))
        self.buttonBgs.append(self.pickAToonGui.find("**/tt_t_gui_pat_squareGreen"))
        self.buttonBgs.append(self.pickAToonGui.find("**/tt_t_gui_pat_squarePurple"))
        self.buttonBgs.append(self.pickAToonGui.find("**/tt_t_gui_pat_squareBlue"))
        self.buttonBgs.append(self.pickAToonGui.find("**/tt_t_gui_pat_squarePink"))
        self.buttonBgs.append(self.pickAToonGui.find("**/tt_t_gui_pat_squareYellow"))
        self["image"] = self.buttonBgs[position]

        self.setScale(1.01)

        if self.mode is AvatarChoice.MODE_CREATE:
            self["command"] = self.__handleCreate
            self["text"] = (TTLocalizer.AvatarChoiceMakeAToon,)
            self["text_pos"] = (0, 0)
            self["text0_scale"] = 0.1
            self["text1_scale"] = 0.12
            self["text2_scale"] = 0.12
            self["text0_fg"] = (0, 1, 0.8, 0.5)
            self["text1_fg"] = (0, 1, 0.8, 1)
            self["text2_fg"] = (0.3, 1, 0.9, 1)

        else:
            self["command"] = self.__handleChoice
            self["text"] = ("", TTLocalizer.AvatarChoicePlayThisToon, TTLocalizer.AvatarChoicePlayThisToon)
            self["text_scale"] = 0.12
            self["text_fg"] = (1, 0.9, 0.1, 1)

            self.nameText = DirectLabel(
                parent=self,
                relief=None,
                scale=0.08,
                pos=NAME_POSITIONS[position],
                text=self.name,
                hpr=(0, 0, NAME_ROTATIONS[position]),
                text_fg=(1, 1, 1, 1),
                text_shadow=(0, 0, 0, 1),
                text_wordwrap=8,
                text_font=getToonFont(),
                state=DGG.DISABLED,
            )

            self.head = hidden.attachNewNode("head")
            self.head.setPosHprScale(0, 5, -0.1, 180, 0, 0, 0.24, 0.24, 0.24)
            self.head.reparentTo(self.stateNodePath[0], 20)
            self.head.instanceTo(self.stateNodePath[1], 20)
            self.head.instanceTo(self.stateNodePath[2], 20)

            self.headModel = ToonHead.ToonHead()
            self.headModel.setupHead(self.dna, forGui=1)
            self.headModel.reparentTo(self.head)

            animalStyle = self.dna.getAnimal()
            bodyScale = ToonBodyScales[animalStyle]
            self.headModel.setScale(bodyScale / 0.75)

            self.headModel.startBlink()
            self.headModel.startLookAround()

            trashcanGui = loader.loadModel("phase_3/models/gui/trashcan_gui")
            self.deleteButton = DirectButton(
                parent=self,
                image=(
                    trashcanGui.find("**/TrashCan_CLSD"),
                    trashcanGui.find("**/TrashCan_OPEN"),
                    trashcanGui.find("**/TrashCan_RLVR"),
                ),
                text=("", TTLocalizer.AvatarChoiceDelete, TTLocalizer.AvatarChoiceDelete),
                text_fg=(1, 1, 1, 1),
                text_shadow=(0, 0, 0, 1),
                text_scale=0.15,
                text_pos=(0, -0.1),
                text_font=getInterfaceFont(),
                relief=None,
                pos=DELETE_POSITIONS[position],
                scale=0.45,
                command=self.__handleDelete,
            )
            trashcanGui.removeNode()

        self.resetFrameSize()

        self.avForLogging = None

        if av:
            self.avForLogging = str(av.id)
        else:
            self.avForLogging = None

        if __debug__:
            base.avChoice = self

    def destroy(self):
        loader.unloadModel("phase_3/models/gui/pick_a_toon_gui")

        self.pickAToonGui.removeNode()
        del self.pickAToonGui
        del self.dna
        if self.mode == AvatarChoice.MODE_CREATE:
            pass
        else:
            self.headModel.stopBlink()
            self.headModel.stopLookAroundNow()
            self.headModel.delete()
            self.head.removeNode()
            del self.head
            del self.headModel
            del self.nameText
            self.deleteButton.destroy()
            del self.deleteButton
            loader.unloadModel("phase_3/models/gui/trashcan_gui")
            loader.unloadModel("phase_3/models/gui/quit_button")
        DirectFrame.destroy(self)

    def __handleChoice(self):
        """
        Handle the 'play with this toon' button
        """
        cleanupDialog("globalDialog")
        messenger.send(self.doneEvent, ["chose", self.position])

    def __handleCreate(self):
        """
        Handle the Make-A-Toon button
        """
        cleanupDialog("globalDialog")
        messenger.send(self.doneEvent, ["create", self.position])

    def __handleDelete(self):
        """
        Handle the Avatar Delete button
        """
        cleanupDialog("globalDialog")
        self.verify = TTDialog.TTGlobalDialog(
            doneEvent="verifyDone", message=TTLocalizer.AvatarChoiceDeleteConfirm % self.name, style=TTDialog.TwoChoice
        )
        self.verify.show()
        self.accept("verifyDone", self.__handleVerifyDelete)

    def __handleVerifyDelete(self):
        status = self.verify.doneStatus
        self.ignore("verifyDone")
        self.verify.cleanup()
        del self.verify
