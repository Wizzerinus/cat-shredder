from direct.controls import ControlManager
from direct.showbase.InputStateGlobal import inputState


class ToonControlManager(ControlManager.ControlManager):
    def __init__(self, enable=True):
        self.inputStateTokens = []
        self.WASDTurnTokens = []
        self.__WASDTurn = True
        self.controls = {}
        self.currentControls = None
        self.currentControlsName = None
        self.isEnabled = 0

        self.forceAvJumpToken = None
        self.inputToDisable = []
        self.istWASD = []
        self.istNormal = []
        if enable:
            self.enable()

    def enable(self):
        if self.isEnabled:
            self.notify.debug("already isEnabled")
            return

        self.isEnabled = 1

        ist = self.inputStateTokens
        ist.append(inputState.watch("run", "runningEvent", "running-on", "running-off"))

        ist.append(inputState.watch("forward", "force-forward", "force-forward-stop"))

        ist.append(inputState.watchWithModifiers("reverse", "mouse4", inputSource=inputState.Mouse))

        ist.append(inputState.watch("turnLeft", "mouse-look_left", "mouse-look_left-done"))
        ist.append(inputState.watch("turnLeft", "force-turnLeft", "force-turnLeft-stop"))

        ist.append(inputState.watch("turnRight", "mouse-look_right", "mouse-look_right-done"))
        ist.append(inputState.watch("turnRight", "force-turnRight", "force-turnRight-stop"))

        ist.append(inputState.watchWithModifiers("forward", base.MOVE_FORWARD, inputSource=inputState.WASD))
        ist.append(inputState.watchWithModifiers("reverse", base.MOVE_BACKWARDS, inputSource=inputState.WASD))

        self.setWASDTurn(self.__WASDTurn)
        ist.append(inputState.watchWithModifiers("jump", base.JUMP))

        if self.currentControls:
            self.currentControls.enableAvatarControls()

    def setWASDTurn(self, turn):
        self.__WASDTurn = turn

        if not self.isEnabled:
            return

        turnLeftWASDSet = inputState.isSet("turnLeft", inputSource=inputState.WASD)
        turnRightWASDSet = inputState.isSet("turnRight", inputSource=inputState.WASD)
        slideLeftWASDSet = inputState.isSet("slideLeft", inputSource=inputState.WASD)
        slideRightWASDSet = inputState.isSet("slideRight", inputSource=inputState.WASD)

        for token in self.WASDTurnTokens:
            token.release()

        if turn:
            self.WASDTurnTokens = (
                inputState.watchWithModifiers("turnLeft", base.MOVE_LEFT, inputSource=inputState.WASD),
                inputState.watchWithModifiers("turnRight", base.MOVE_RIGHT, inputSource=inputState.WASD),
            )

            inputState.set("turnLeft", slideLeftWASDSet, inputSource=inputState.WASD)
            inputState.set("turnRight", slideRightWASDSet, inputSource=inputState.WASD)

            inputState.set("slideLeft", False, inputSource=inputState.WASD)
            inputState.set("slideRight", False, inputSource=inputState.WASD)

        else:
            self.WASDTurnTokens = (
                inputState.watchWithModifiers("slideLeft", base.MOVE_LEFT, inputSource=inputState.WASD),
                inputState.watchWithModifiers("slideRight", base.MOVE_RIGHT, inputSource=inputState.WASD),
            )

            inputState.set("slideLeft", turnLeftWASDSet, inputSource=inputState.WASD)
            inputState.set("slideRight", turnRightWASDSet, inputSource=inputState.WASD)

            inputState.set("turnLeft", False, inputSource=inputState.WASD)
            inputState.set("turnRight", False, inputSource=inputState.WASD)

    def disable(self):
        self.isEnabled = 0

        for token in self.inputStateTokens:
            token.release()
        self.inputStateTokens = []

        for token in self.WASDTurnTokens:
            token.release()
        self.WASDTurnTokens = []

        if self.currentControls:
            self.currentControls.disableAvatarControls()

        self.notify.info("WASD support was enabled.")
        self.istWASD.append(inputState.watchWithModifiers("forward", base.MOVE_FORWARD, inputSource=inputState.WASD))
        self.istWASD.append(inputState.watchWithModifiers("reverse", base.MOVE_BACKWARDS, inputSource=inputState.WASD))
        self.istWASD.append(inputState.watchWithModifiers("turnLeft", base.MOVE_LEFT, inputSource=inputState.WASD))
        self.istWASD.append(inputState.watchWithModifiers("turnRight", base.MOVE_RIGHT, inputSource=inputState.WASD))

    def disableWASD(self):
        self.forceTokens = [
            inputState.force("jump", 0, "ControlManager.disableWASD"),
            inputState.force("forward", 0, "ControlManager.disableWASD"),
            inputState.force("turnLeft", 0, "ControlManager.disableWASD"),
            inputState.force("slideLeft", 0, "ControlManager.disableWASD"),
            inputState.force("reverse", 0, "ControlManager.disableWASD"),
            inputState.force("turnRight", 0, "ControlManager.disableWASD"),
            inputState.force("slideRight", 0, "ControlManager.disableWASD"),
        ]
        self.notify.info("disableWASD()")

    def enableWASD(self):
        if self.forceTokens:
            for token in self.forceTokens:
                token.release()
            self.forceTokens = []
            self.notify.info("enableWASD")

    def reload(self):
        """
        Reload the controlmanager in-game
        """

        for token in self.istNormal:
            token.release()
        self.istNormal = []
        self.inputStateTokens = []
        self.disable()
