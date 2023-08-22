from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from direct.showbase.PythonUtil import boolEqual
from direct.task import Task
from pandac.PandaModules import *

from otp.speedchat.SCConstants import *
from otp.speedchat.SCObject import SCObject
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont


class SCElement(SCObject, NodePath):
    """SCElement is the base class for all entities that can appear
    as entries in a SpeedChat menu."""

    font = getInterfaceFont()

    SerialNum = 0

    def __init__(self, parentMenu=None):
        SCObject.__init__(self)

        self.SerialNum = SCElement.SerialNum
        SCElement.SerialNum += 1
        node = hidden.attachNewNode(f"SCElement{self.SerialNum}")
        NodePath.__init__(self, node)

        self.FinalizeTaskName = f"SCElement{self.SerialNum}_Finalize"

        self.parentMenu = parentMenu
        self.__active = 0
        self.__viewable = 1

        self.lastWidth = 0
        self.lastHeight = 0

        self.setDimensions(0, 0)

        self.padX = 0.25
        self.padZ = 0.1

    def destroy(self):
        if self.isActive():
            self.exitActive()
        SCObject.destroy(self)
        if hasattr(self, "button"):
            self.button.destroy()
            del self.button
        self.parentMenu = None
        self.detachNode()

    def setParentMenu(self, parentMenu):
        self.parentMenu = parentMenu

    def getParentMenu(self):
        return self.parentMenu

    def getDisplayText(self):
        """derived classes should override and return the text that
        should be visually displayed on this item. Note that elements
        that must do non-trivial processing to produce this text
        should cache the text when they can."""
        self.notify.error("getDisplayText is pure virtual, derived class must override")

    def onMouseEnter(self, event):
        """the mouse has just entered this entity"""
        if self.parentMenu is not None:
            self.parentMenu.memberGainedInputFocus(self)

    def onMouseLeave(self, event):
        """the mouse has just left this entity"""
        if self.parentMenu is not None:
            self.parentMenu.memberLostInputFocus(self)

    def onMouseClick(self, event):
        """the user just clicked on this entity"""

    """ inheritors should override these methods and perform whatever
    actions are appropriate when this element becomes 'active' and
    'inactive' (for example, menu holders should show/hide their menu;
    other element types might play some sort of animation on activation).
    'active' generally corresponds to having the input focus, but not
    always; see 'hasStickyFocus' below. """

    def enterActive(self):
        self.__active = 1

    def exitActive(self):
        self.__active = 0

    def isActive(self):
        return self.__active

    def hasStickyFocus(self):
        """Inheritors should override and return non-zero if they
        should remain active until a sibling becomes active, even
        if they lose the input focus. For example, menu holders should
        remain open until a sibling becomes active, even if the user
        moves the mouse out of the menu holder, or even completely away
        from the SpeedChat menus."""
        return 0

    """ If this element is marked as 'not viewable', it will disappear from
    its parent menu, and it will not be possible for the user to
    interact with this element. """

    def setViewable(self, viewable):
        if not boolEqual(self.__viewable, viewable):
            self.__viewable = viewable

            if self.parentMenu is not None:
                self.parentMenu.memberViewabilityChanged(self)

    def isViewable(self):
        return self.__viewable

    def getMinDimensions(self):
        """Should return the width/height that this element would
        ideally like to be. We may be asked to display ourselves
        larger than this, never smaller.
        returns (width, height)
        """
        text = TextNode("SCTemp")
        text.setFont(SCElement.font)
        dText = self.getDisplayText()
        text.setText(dText)
        bounds = text.getCardActual()
        width = abs(bounds[1] - bounds[0]) + self.padX
        height = abs(bounds[3] - bounds[2]) + 2.0 * self.padZ
        return width, height

    def setDimensions(self, width, height):
        """Call this to tell this element how big it should be. Must be
        called before calling finalize."""
        self.width = float(width)
        self.height = float(height)
        if (self.lastWidth, self.lastHeight) != (self.width, self.height):
            self.invalidate()

    def invalidate(self):
        """call this if something about our appearance has changed and
        we need to re-create our button"""
        SCObject.invalidate(self)
        parentMenu = self.getParentMenu()
        if parentMenu is not None and not parentMenu.isFinalizing():
            parentMenu.invalidate()

    def enterVisible(self):
        SCObject.enterVisible(self)
        self.privScheduleFinalize()

    def exitVisible(self):
        SCObject.exitVisible(self)
        self.privCancelFinalize()

    def privScheduleFinalize(self):
        def finalizeElement(task):
            if self.parentMenu is not None and self.parentMenu.isDirty():
                return Task.done
            self.finalize()
            return Task.done

        taskMgr.remove(self.FinalizeTaskName)
        taskMgr.add(finalizeElement, self.FinalizeTaskName, priority=SCElementFinalizePriority)

    def privCancelFinalize(self):
        taskMgr.remove(self.FinalizeTaskName)

    def finalize(self, dbArgs=None):
        """'dbArgs' can contain parameters (and parameter overrides) for
        the DirectButton.
        """
        if dbArgs is None:
            dbArgs = {}
        if not self.isDirty():
            return

        SCObject.finalize(self)

        if hasattr(self, "button"):
            self.button.destroy()
            del self.button

        halfHeight = self.height / 2.0

        textX = 0
        if "text_align" in dbArgs and dbArgs["text_align"] == TextNode.ACenter:
            textX = self.width / 2.0

        args = {
            "text": self.getDisplayText(),
            "frameColor": (0, 0, 0, 0),
            "rolloverColor": (*self.getColorScheme().getRolloverColor(), 1),
            "pressedColor": (*self.getColorScheme().getPressedColor(), 1),
            "text_font": getInterfaceFont(),
            "text_align": TextNode.ALeft,
            "text_fg": (*self.getColorScheme().getTextColor(), 1),
            "text_pos": (textX, -0.25 - halfHeight, 0),
            "relief": DirectGuiGlobals.FLAT,
            "pressEffect": 0,
        }
        args.update(dbArgs)

        rolloverColor = args["rolloverColor"]
        pressedColor = args["pressedColor"]
        del args["rolloverColor"]
        del args["pressedColor"]

        btn = DirectButton(
            parent=self,
            frameSize=(0, self.width, -self.height, 0),
            **args,
        )

        btn.frameStyle[DirectGuiGlobals.BUTTON_ROLLOVER_STATE].setColor(*rolloverColor)
        btn.frameStyle[DirectGuiGlobals.BUTTON_DEPRESSED_STATE].setColor(*pressedColor)
        btn.updateFrameStyle()

        btn.bind(DirectGuiGlobals.ENTER, self.onMouseEnter)
        btn.bind(DirectGuiGlobals.EXIT, self.onMouseLeave)
        btn.bind(DirectGuiGlobals.B1PRESS, self.onMouseClick)
        self.button = btn

        self.lastWidth = self.width
        self.lastHeight = self.height

        self.validate()

    def __str__(self):
        return f"{self.__class__.__name__}: {self.getDisplayText()}"
