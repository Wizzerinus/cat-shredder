from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *

# No buttons at all
NoButtons = 0
# just an OK button
Acknowledge = 1
# Just a CANCEL button
CancelOnly = 2
# OK and CANCEL buttons
TwoChoice = 3
# Yes and No buttons
YesNo = 4
# custom 2 buttons
TwoChoiceCustom = 5


class OTPDialog(DirectDialog):
    def __init__(self, parent=None, style=NoButtons, **kw):
        if parent is None:
            parent = aspect2d

        self.style = style

        buttons = None
        if self.style != NoButtons:
            assert self.path
            buttons = loader.loadModel(self.path)

        if self.style == TwoChoiceCustom:
            okImageList = (
                buttons.find("**/ChtBx_OKBtn_UP"),
                buttons.find("**/ChtBx_OKBtn_DN"),
                buttons.find("**/ChtBx_OKBtn_Rllvr"),
            )
            cancelImageList = (
                buttons.find("**/CloseBtn_UP"),
                buttons.find("**/CloseBtn_DN"),
                buttons.find("**/CloseBtn_Rllvr"),
            )
            buttonImage = [okImageList, cancelImageList]
            buttonValue = [DirectGuiGlobals.DIALOG_OK, DirectGuiGlobals.DIALOG_CANCEL]
            if "buttonText" in kw:
                buttonText = kw["buttonText"]
                del kw["buttonText"]
            else:
                buttonText = ["OK", "Cancel"]

        elif self.style == TwoChoice:
            okImageList = (
                buttons.find("**/ChtBx_OKBtn_UP"),
                buttons.find("**/ChtBx_OKBtn_DN"),
                buttons.find("**/ChtBx_OKBtn_Rllvr"),
            )
            cancelImageList = (
                buttons.find("**/CloseBtn_UP"),
                buttons.find("**/CloseBtn_DN"),
                buttons.find("**/CloseBtn_Rllvr"),
            )
            buttonImage = [okImageList, cancelImageList]
            buttonText = ["OK", "Cancel"]
            buttonValue = [DirectGuiGlobals.DIALOG_OK, DirectGuiGlobals.DIALOG_CANCEL]
        elif self.style == YesNo:
            okImageList = (
                buttons.find("**/ChtBx_OKBtn_UP"),
                buttons.find("**/ChtBx_OKBtn_DN"),
                buttons.find("**/ChtBx_OKBtn_Rllvr"),
            )
            cancelImageList = (
                buttons.find("**/CloseBtn_UP"),
                buttons.find("**/CloseBtn_DN"),
                buttons.find("**/CloseBtn_Rllvr"),
            )
            buttonImage = [okImageList, cancelImageList]
            buttonText = ["Yes", "No"]
            buttonValue = [DirectGuiGlobals.DIALOG_OK, DirectGuiGlobals.DIALOG_CANCEL]
        elif self.style == Acknowledge:
            okImageList = (
                buttons.find("**/ChtBx_OKBtn_UP"),
                buttons.find("**/ChtBx_OKBtn_DN"),
                buttons.find("**/ChtBx_OKBtn_Rllvr"),
            )
            buttonImage = [okImageList]
            buttonText = ["OK"]
            buttonValue = [DirectGuiGlobals.DIALOG_OK]
        elif self.style == CancelOnly:
            cancelImageList = (
                buttons.find("**/CloseBtn_UP"),
                buttons.find("**/CloseBtn_DN"),
                buttons.find("**/CloseBtn_Rllvr"),
            )
            buttonImage = [cancelImageList]
            buttonText = ["Cancel"]
            buttonValue = [DirectGuiGlobals.DIALOG_CANCEL]
        elif self.style == NoButtons:
            buttonImage = []
            buttonText = []
            buttonValue = []
        else:
            raise ValueError(f"No such style as: {self.style}")

        optiondefs = (
            ("buttonImageList", buttonImage, DirectGuiGlobals.INITOPT),
            ("buttonTextList", buttonText, DirectGuiGlobals.INITOPT),
            ("buttonValueList", buttonValue, DirectGuiGlobals.INITOPT),
            ("buttonPadSF", 2.2, DirectGuiGlobals.INITOPT),
            ("text_font", DirectGuiGlobals.getDefaultFont(), None),
            ("text_wordwrap", 12, None),
            ("text_scale", 0.07, None),
            ("buttonSize", (-0.05, 0.05, -0.05, 0.05), None),
            ("button_pad", (0, 0), None),
            ("button_relief", None, None),
            ("button_text_pos", (0, -0.1), None),
            ("fadeScreen", 0.5, None),
            ("image_color", (1, 1, 0.75, 1), None),
        )
        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(OTPDialog)

        if buttons is not None:
            buttons.removeNode()


class GlobalDialog(OTPDialog):
    notify = directNotify.newCategory("GlobalDialog")

    def __init__(
        self,
        message="",
        doneEvent=None,
        style=NoButtons,
        okButtonText="OK",
        cancelButtonText="Cancel",
        **kw,
    ):
        """
        ___init___(self, doneEvent, style, okButtonText, cancelButtonText, kw)
        """

        if not hasattr(self, "path"):
            self.path = "phase_3/models/gui/dialog_box_buttons_gui"

        if (doneEvent is None) and (style != NoButtons):
            self.notify.error("Boxes with buttons must specify a doneEvent.")

        self.__doneEvent = doneEvent

        if style == NoButtons:
            buttonText = []
        elif style == Acknowledge:
            buttonText = [okButtonText]
        elif style == CancelOnly:
            buttonText = [cancelButtonText]
        else:
            buttonText = [okButtonText, cancelButtonText]
        optiondefs = (
            ("dialogName", "globalDialog", DirectGuiGlobals.INITOPT),
            ("buttonTextList", buttonText, DirectGuiGlobals.INITOPT),
            ("text", message, None),
            ("command", self.handleButton, None),
        )
        self.defineoptions(kw, optiondefs)
        OTPDialog.__init__(self, style=style)
        self.initialiseoptions(GlobalDialog)

    def handleButton(self, value):
        assert self.style != NoButtons
        if value == DirectGuiGlobals.DIALOG_OK:
            self.doneStatus = "ok"
            messenger.send(self.__doneEvent)
        elif value == DirectGuiGlobals.DIALOG_CANCEL:
            self.doneStatus = "cancel"
            messenger.send(self.__doneEvent)
        elif value == DirectGuiGlobals.DIALOG_NO:
            self.doneStatus = "no"
            messenger.send(self.__doneEvent)
