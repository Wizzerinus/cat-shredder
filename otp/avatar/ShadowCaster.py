from direct.showbase.ShadowPlacer import ShadowPlacer
from panda3d.core import NodePath

from toontown.toonbase.globals.TTGlobalsRender import *


class ShadowCaster(NodePath):
    shadowJoint = None

    notify = directNotify.newCategory("ShadowCaster")

    def __init__(self, squareShadow=False):
        assert self.notify.debugStateCall(self)
        if squareShadow:
            self.shadowFileName = "phase_3/models/props/square_drop_shadow"
        else:
            self.shadowFileName = "phase_3/models/props/drop_shadow"

        self.dropShadow = None
        self.shadowPlacer = None
        self.activeShadow = 0
        self.wantsActive = 1
        self.storedActiveState = 0

    def delete(self):
        assert self.notify.debugStateCall(self)

        self.deleteDropShadow()
        self.shadowJoint = None

    def initializeDropShadow(self, hasGeomNode=True):
        """
        Load up and arrange the drop shadow
        """
        assert self.notify.debugStateCall(self)
        self.deleteDropShadow()

        if hasGeomNode:
            self.getGeomNode().setTag("cam", "caster")

        dropShadow = loader.loadModel(self.shadowFileName)
        dropShadow.setScale(0.4)

        dropShadow.flattenMedium()
        dropShadow.setBillboardAxis(2)
        dropShadow.setColor(0.0, 0.0, 0.0, 0.5, 1)
        self.shadowPlacer = ShadowPlacer(base.shadowTrav, dropShadow, WallBitmask, FloorBitmask)
        self.dropShadow = dropShadow
        if self.getShadowJoint():
            dropShadow.reparentTo(self.getShadowJoint())
        else:
            self.dropShadow.hide()

        self.setActiveShadow(self.wantsActive)

        self.__globalDropShadowFlagChanged()
        self.__globalDropShadowGrayLevelChanged()

    def update(self):
        """This method is meant to be overriden."""

    def deleteDropShadow(self):
        """
        Lose the drop shadows
        """
        assert self.notify.debugStateCall(self)
        if self.shadowPlacer:
            self.shadowPlacer.delete()
            self.shadowPlacer = None

        if self.dropShadow:
            self.dropShadow.removeNode()
            self.dropShadow = None

    def setActiveShadow(self, isActive=1):
        """
        Turn the shadow placement on or off.
        """
        assert self.notify.debugStateCall(self)

        isActive = isActive and self.wantsActive
        if self.shadowPlacer is not None and self.activeShadow != isActive:
            self.activeShadow = isActive
            if isActive:
                self.shadowPlacer.on()
            else:
                self.shadowPlacer.off()

    def setShadowHeight(self, shadowHeight):
        """
        Places the shadow at a particular height below the avatar (in
        effect, asserting that the avatar is shadowHeight feet above
        the ground).

        This is only useful when the active shadow is disabled via
        setActiveShadow(0).
        """
        assert self.notify.debugStateCall(self)
        if self.dropShadow:
            self.dropShadow.setZ(-shadowHeight)

    def getShadowJoint(self):
        assert self.notify.debugStateCall(self)
        if not self.shadowJoint:
            shadowJoint = self.find("**/attachShadow")
            if shadowJoint.isEmpty():
                self.shadowJoint = NodePath(self)
            else:
                self.shadowJoint = shadowJoint
        return self.shadowJoint

    def hideShadow(self):
        assert self.notify.debugStateCall(self)
        self.dropShadow.hide()

    def showShadow(self):
        assert self.notify.debugStateCall(self)

        self.dropShadow.show()

    def __globalDropShadowFlagChanged(self):
        if self.dropShadow is not None and self.activeShadow == 0:
            self.setActiveShadow(1)
            self.showShadow()

    def __globalDropShadowGrayLevelChanged(self):
        if self.dropShadow is not None:
            self.dropShadow.setColor(0.0, 0.0, 0.0, 0.5, 1)
