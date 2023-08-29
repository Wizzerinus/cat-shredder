from . import Walk
from toontown.toonbase.globals.TTGlobalsMovement import *
from toontown.toonbase.globals.TTGlobalsRender import *


class PublicWalk(Walk.Walk):
    notify = directNotify.newCategory("PublicWalk")

    def __init__(self, parentFSM, doneEvent):
        Walk.Walk.__init__(self, doneEvent)
        self.parentFSM = parentFSM
        self.isSprinting = 0

    def load(self):
        Walk.Walk.load(self)

    def unload(self):
        Walk.Walk.unload(self)
        del self.parentFSM

    def enter(self, slowWalk=0):
        Walk.Walk.enter(self, slowWalk)
        base.localAvatar.laffMeter.start()
        self.accept(base.SPRINT, self.sprintHeld)
        self.accept(f"{base.SPRINT}-up", self.sprintReleased)

    def exit(self):
        Walk.Walk.exit(self)
        base.localAvatar.laffMeter.stop()
        self.stopSprint()
        self.ignoreAll()

    @property
    def sprintMode(self):
        return base.settings.getOption("sprintMode", "Toggle")

    @property
    def sprintFOVChanges(self):
        return base.settings.getBool("sprintFOVChanges", False)

    def sprintHeld(self):
        if self.sprintMode != "Auto":
            if not self.isSprinting:
                self.startSprint()
            elif self.sprintMode == "Toggle" and self.isSprinting:
                self.stopSprint()

    def sprintReleased(self):
        if self.sprintMode != "Auto":
            if self.sprintMode == "Hold" and self.isSprinting:
                self.stopSprint()

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
            if self.sprintFOVChanges:
                base.changeFov(SprintCameraFov)

    def stopSprint(self, forceImmediate=False):
        if not self.isSprinting:
            return
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
            if self.sprintFOVChanges:
                base.changeFov(DefaultCameraFov, forceImmediate=forceImmediate)
