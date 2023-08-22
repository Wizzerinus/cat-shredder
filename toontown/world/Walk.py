from direct.fsm import ClassicFSM, State
from direct.fsm import StateData
from direct.task.Task import Task


class Walk(StateData.StateData):
    notify = directNotify.newCategory("Walk")

    def __init__(self, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.fsm = ClassicFSM.ClassicFSM(
            "Walk",
            [
                State.State("off", self.enterOff, self.exitOff, ["walking", "swimming", "slowWalking"]),
                State.State("walking", self.enterWalking, self.exitWalking, ["swimming", "slowWalking"]),
                State.State("swimming", self.enterSwimming, self.exitSwimming, ["walking", "slowWalking"]),
                State.State("slowWalking", self.enterSlowWalking, self.exitSlowWalking, ["walking", "swimming"]),
            ],
            "off",
            "off",
        )
        self.fsm.enterInitialState()
        self.IsSwimSoundAudible = 0
        self.swimSoundPlaying = 0

    def load(self):
        pass

    def unload(self):
        del self.fsm

    def enter(self, slowWalk=0):
        base.localAvatar.startPosHprBroadcast()
        base.localAvatar.startBlink()
        base.localAvatar.cmod.enable()
        base.localAvatar.showName()
        base.localAvatar.collisionsOn()
        base.localAvatar.enableAvatarControls()

    def exit(self):
        self.fsm.request("off")
        self.ignore("control")
        base.localAvatar.disableAvatarControls()
        base.localAvatar.stopPosHprBroadcast()
        base.localAvatar.stopBlink()
        base.localAvatar.cmod.disable()
        base.localAvatar.collisionsOff()
        base.localAvatar.controlManager.placeOnFloor()

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterWalking(self):
        if base.localAvatar.hp > 0:
            base.localAvatar.startTrackAnimToSpeed()
            base.localAvatar.setWalkSpeedNormal()
        else:
            self.fsm.request("slowWalking")

    def exitWalking(self):
        base.localAvatar.stopTrackAnimToSpeed()

    def setSwimSoundAudible(self, IsSwimSoundAudible):
        self.IsSwimSoundAudible = IsSwimSoundAudible
        if IsSwimSoundAudible == 0 and self.swimSoundPlaying:
            self.swimSound.stop()
            self.swimSoundPlaying = 0

    def enterSwimming(self, swimSound):
        base.localAvatar.setWalkSpeedNormal()
        self.swimSound = swimSound
        self.swimSoundPlaying = 0
        base.localAvatar.b_setAnimState("swim", base.localAvatar.animMultiplier)
        base.localAvatar.startSleepSwimTest()
        taskMgr.add(self.__swim, "localToonSwimming")

    def exitSwimming(self):
        taskMgr.remove("localToonSwimming")
        self.swimSound.stop()
        del self.swimSound
        self.swimSoundPlaying = 0
        base.localAvatar.stopSleepSwimTest()

    def __swim(self, task):
        speed = base.mouseInterfaceNode.getSpeed()
        if speed == 0 and self.swimSoundPlaying:
            self.swimSoundPlaying = 0
            self.swimSound.stop()
        elif speed > 0 and self.swimSoundPlaying == 0 and self.IsSwimSoundAudible:
            self.swimSoundPlaying = 1
            base.playSfx(self.swimSound, looping=1)
        return Task.cont

    def enterSlowWalking(self):
        self.accept(base.localAvatar.uniqueName("positiveHP"), self.__handlePositiveHP)
        base.localAvatar.startTrackAnimToSpeed()
        base.localAvatar.setWalkSpeedSlow()

    def __handlePositiveHP(self):
        self.fsm.request("walking")

    def exitSlowWalking(self):
        base.localAvatar.stopTrackAnimToSpeed()
        self.ignore(base.localAvatar.uniqueName("positiveHP"))
