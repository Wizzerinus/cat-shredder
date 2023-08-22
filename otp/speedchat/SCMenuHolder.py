from direct.gui import DirectGuiGlobals
from panda3d.core import Point3

from otp.speedchat import SCMenu
from otp.speedchat.SCElement import SCElement
from otp.speedchat.SCObject import SCObject


class SCMenuHolder(SCElement):
    """
    SCMenuHolder is an SCElement that owns an SCMenu and is
    responsible for displaying it.
    """

    N = 0.9
    DefaultFrameColor = (0, 0, 0, 1.0 - N)
    del N

    MenuColorScaleDown = 0.95

    def __init__(self, title, menu=None):
        SCElement.__init__(self)
        self.title = title

        scGui = loader.loadModel(SCMenu.SCMenu.GuiModelName)
        self.scArrow = scGui.find("**/chatArrow")

        self.menu = None
        self.setMenu(menu)

    def destroy(self):
        if self.menu is not None:
            self.menu.destroy()
            self.menu = None
        SCElement.destroy(self)

    def setTitle(self, title):
        self.title = title
        self.invalidate()

    def getTitle(self):
        return self.title

    def setMenu(self, menu):
        if self.menu is not None:
            self.menu.destroy()
        self.menu = menu
        if self.menu is not None:
            self.privAdoptSCObject(self.menu)
            self.menu.setHolder(self)
            self.menu.reparentTo(self, 1)
            self.menu.hide()
        self.updateViewability()

    def getMenu(self):
        return self.menu

    def showMenu(self):
        """use this if we go back to a sorted bin
        drawOrder = self.getNetState().getDrawOrder()
        self.menu.setBin('fixed', drawOrder + 1)
        """
        if self.menu is not None:
            cS = SCMenuHolder.MenuColorScaleDown
            self.menu.setColorScale(cS, cS, cS, 1)
            self.menu.enterVisible()
            self.menu.show()

    def hideMenu(self):
        if self.menu is not None:
            self.menu.hide()
            self.menu.exitVisible()

    def getMenuOverlap(self):
        """returns a value in 0..1 representing the percentage
        of our width that submenus should cover"""
        if self.parentMenu.isTopLevel():
            return self.getTopLevelOverlap()

        return self.getSubmenuOverlap()

    def getMenuOffset(self):
        """should return a Point3 offset at which the menu should be
        positioned relative to this element"""
        xOffset = self.width * (1.0 - self.getMenuOverlap())
        return Point3(xOffset, 0, 0)

    def onMouseClick(self, event):
        SCElement.enterActive(self)
        self.parentMenu.memberSelected(self)

    def enterActive(self):
        SCElement.enterActive(self)
        self.showMenu()

        if hasattr(self, "button"):
            r, g, b = self.getColorScheme().getMenuHolderActiveColor()
            a = self.getColorScheme().getAlpha()
            self.button.frameStyle[DirectGuiGlobals.BUTTON_READY_STATE].setColor(r, g, b, a)
            self.button.updateFrameStyle()
        else:
            self.notify.warning("SCMenuHolder has no button (has finalize been called?).")

    def exitActive(self):
        SCElement.exitActive(self)
        self.hideMenu()

        self.button.frameStyle[DirectGuiGlobals.BUTTON_READY_STATE].setColor(*SCMenuHolder.DefaultFrameColor)
        self.button.updateFrameStyle()

    def getDisplayText(self):
        return self.title

    def updateViewability(self):
        if self.menu is None:
            self.setViewable(0)
            return
        isViewable = False
        for child in self.menu:
            if child.isViewable():
                isViewable = True
                break
        self.setViewable(isViewable)

    def getMinSubmenuWidth(self):
        parentMenu = self.getParentMenu()
        if parentMenu is None:
            myWidth, myWeight = self.getMinDimensions()
        else:
            myWidth = parentMenu.getWidth()
        return 0.15 + (myWidth * self.getMenuOverlap())

    def getMinDimensions(self):
        width, height = SCElement.getMinDimensions(self)
        width += 1.0
        return width, height

    def invalidate(self):
        SCElement.invalidate(self)
        if self.menu is not None:
            self.menu.invalidate()

    def finalize(self, dbArgs=None):
        """catch this call and influence the appearance of our button"""
        if dbArgs is None:
            dbArgs = {}
        if not self.isDirty():
            return

        r, g, b = self.getColorScheme().getArrowColor()
        a = self.getColorScheme().getAlpha()
        self.scArrow.setColorScale(r, g, b, a)

        if self.menu is not None:
            self.menu.setPos(self.getMenuOffset())

        if self.isActive():
            r, g, b = self.getColorScheme().getMenuHolderActiveColor()
            a = self.getColorScheme().getAlpha()
            frameColor = (r, g, b, a)
        else:
            frameColor = SCMenuHolder.DefaultFrameColor

        args = {
            "image": self.scArrow,
            "image_pos": (self.width - 0.5, 0, -self.height * 0.5),
            "frameColor": frameColor,
        }

        args.update(dbArgs)
        SCElement.finalize(self, dbArgs=args)

    def hasStickyFocus(self):
        """menu holders have sticky focus. Once a menu holder gets
        activated, it stays active until a sibling becomes active."""
        return 1

    def privSetSettingsRef(self, settingsRef):
        SCObject.privSetSettingsRef(self, settingsRef)
        if self.menu is not None:
            self.menu.privSetSettingsRef(settingsRef)

    def invalidateAll(self):
        SCObject.invalidateAll(self)
        if self.menu is not None:
            self.menu.invalidateAll()

    def finalizeAll(self):
        SCObject.finalizeAll(self)
        if self.menu is not None:
            self.menu.finalizeAll()
