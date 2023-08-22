# From Disney's POTCO source code
from direct.interval.IntervalGlobal import *
from direct.showbase.InputStateGlobal import inputState
from direct.task import Task
from panda3d.core import *

from otp.otpbase.PythonUtil import ParamObj, lerp
from otp.otpbase.PythonUtil import clampScalar
from otp.otpbase.PythonUtil import fitSrcAngle2Dest, reduceAngle
from toontown.toon.camera import CameraMode
from toontown.toonbase.globals.TTGlobalsMovement import *
from toontown.toonbase.globals.TTGlobalsRender import *


class OrbitCamera(CameraMode.CameraMode, NodePath, ParamObj):
    notify = directNotify.newCategory("OrbitCamera")

    class ParamSet(ParamObj.ParamSet):
        Params = {
            "lookAtOffset": Vec3(0, 0, 0),
            "escapement": 10.0,
            "rotation": 0.0,
            "fadeGeom": False,
            "idealDistance": DefaultCameraFov,
            "minDistance": DefaultCameraFov,
            "maxDistance": 72.0,
            "minEsc": -20.0,
            "maxEsc": 25.0,
            "minDomeEsc": 0.0,
            "maxCamtiltEsc": 0.0,
            "autoFaceForward": True,
            "autoFaceForwardMaxDur": 14.0,
            "camOffset": Vec3(0, -9, 5.5),
        }

    UpdateTaskName = "OrbitCamUpdateTask"
    CollisionCheckTaskName = "OrbitCamCollisionTask"
    GeomFadeLerpDur = 1.0
    PullFwdDist = 2.0
    ReadMouseTaskName = "OrbitCamReadMouseTask"
    DistanceCheckTaskName = "OrbitCamDistanceTask"
    MinP = -50
    MaxP = 20
    baseH = None
    minH = None
    maxH = None
    # TODO add this to settings
    SensitivityH = ConfigVariableDouble("fps-cam-sensitivity-x", 0.2).getValue()
    SensitivityP = ConfigVariableDouble("fps-cam-sensitivity-y", 0.1).getValue()

    def __init__(self, subject, params=None):
        ParamObj.__init__(self)
        NodePath.__init__(self, self._getTopNodeName())
        CameraMode.CameraMode.__init__(self)
        self.setSubject(subject)
        self.lookAtNode = NodePath("orbitCamLookAt")
        self.escapementNode = self.attachNewNode("orbitCamEscapement")
        self.camParent = self.escapementNode.attachNewNode("orbitCamParent")
        self._paramStack = []
        self.setDefaultParams()

        self._isAtRear = True
        self._rotateToRearIval = None
        self.toggleFov = False
        self._lockAtRear = False
        self.forceMaxDistance = True
        self.avFacingScreen = False
        self.lastGeomH = 0
        self.collisionTaskCountNum = 0
        self.cTravOnFloor = CollisionTraverser("CamMode.cTravOnFloor")
        self.camFloorRayNode = self.attachNewNode("camFloorRayNode")
        self.ccRay2 = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRay2Node = CollisionNode("ccRay2Node")
        self.ccRay2Node.addSolid(self.ccRay2)
        self.ccRay2NodePath = self.camFloorRayNode.attachNewNode(self.ccRay2Node)
        self.ccRay2BitMask = FloorBitmask
        self.ccRay2Node.setFromCollideMask(self.ccRay2BitMask)
        self.ccRay2Node.setIntoCollideMask(BitMask32.allOff())
        self.ccRay2MoveNodePath = hidden.attachNewNode("ccRay2MoveNode")
        self.camFloorCollisionBroadcaster = CollisionHandlerFloor()
        self.camFloorCollisionBroadcaster.addInPattern("zone_on-floor")
        self.camFloorCollisionBroadcaster.addOutPattern("zone_off-floor")
        self.camFloorCollisionBroadcaster.addCollider(self.ccRay2NodePath, self.ccRay2MoveNodePath)
        self.cTravOnFloor.addCollider(self.ccRay2NodePath, self.camFloorCollisionBroadcaster)

        self.lodCenter = NodePath()
        self.lodCenterEnv = NodePath()
        self.accept("change_movement", self.change_movement)
        taskMgr.add(self.checkSubjectDist, self.DistanceCheckTaskName, priority=41)
        self.toonWasWalking = False
        self.usingOrbitalRun = False
        self.acceptingMovement = True

    def checkSubjectDist(self, task):
        distance = camera.getDistance(self)
        if distance < 1.8:
            self.subject.getGeomNode().hide()
        else:
            self.subject.getGeomNode().show()
        return task.cont

    def change_movement(self, action, speed_normal, speed_running, speed_sliding):
        run_angle = -45 if speed_sliding > 0 else 45

        angles = {
            STRAFE_LEFT_INDEX: 90,
            STRAFE_RIGHT_INDEX: -90,
            RUN_INDEX: run_angle if abs(speed_sliding) > RunCutOff else 0,
        }

        self.setGeomNodeH(angles.get(action, 0))

    def destroy(self):
        del self.cTravOnFloor
        del self.ccRay2
        del self.ccRay2Node
        self.ccRay2NodePath.remove_node()
        del self.ccRay2NodePath
        self.ccRay2MoveNodePath.remove_node()
        del self.ccRay2MoveNodePath
        self.camFloorRayNode.remove_node()
        del self.camFloorRayNode
        self._paramStack = None
        self.escapemntNode = None
        self.camParent = None
        self.lookAtNode.removeNode()
        del self.subject
        CameraMode.CameraMode.destroy(self)
        NodePath.removeNode(self)
        ParamObj.destroy(self)
        taskMgr.remove(self.DistanceCheckTaskName)

    def getName(self):
        return "Orbit"

    def _getTopNodeName(self):
        return "OrbitCam"

    def setSubject(self, subject=None):
        self.subject = subject

    def getSubject(self):
        return self.subject

    def pushParams(self):
        self._paramStack.append(self.ParamSet(self))

    def popParams(self):
        curParams = self.ParamSet(self)
        if len(self._paramStack):
            self._paramStack.pop().applyTo(self)
        else:
            OrbitCamera.notify.warning("param stack underflow")
        return curParams

    def getLookAtOffset(self):
        return self.lookAtOffset

    def setLookAtOffset(self, lookAtOffset):
        self.lookAtOffset = Vec3(lookAtOffset)

    def applyLookAtOffset(self):
        if self.isActive():
            self.lookAtNode.setPos(self.lookAtOffset)
            self.setFluidPos(render, self.lookAtNode.getPos(render))
            camera.lookAt(self.lookAtNode)

    def getEscapement(self):
        return self.escapement

    def setEscapement(self, escapement):
        self.escapement = escapement

    def applyEscapement(self):
        if self.isActive():
            if self.escapement >= self._minDomeEsc:
                domeEsc = self.escapement
                camEsc = 0.0
            elif self.escapement <= self._maxCamtiltEsc:
                domeEsc = self._minDomeEsc
                camEsc = self._maxCamtiltEsc - self.escapement
            else:
                domeEsc = self._minDomeEsc
                camEsc = 0.0
            self.escapementNode.setP(-domeEsc)
            self.camParent.setP(camEsc)

    def _lerpEscapement(self, escapement, duration=None):
        curEsc = self.getEscapement()
        escapement = clampScalar(escapement, self._minEsc, self._maxEsc)
        if duration is None:
            diff = abs(curEsc - escapement)
            speed = (max(curEsc, self._maxEsc) - min(curEsc, self._minEsc)) * 0.025
            duration = diff / speed
        self._stopEscapementLerp()
        self._escLerpIval = LerpFunctionInterval(
            self.setEscapement,
            fromData=curEsc,
            toData=escapement,
            duration=duration,
            blendType="easeOut",
            name="OrbitCamera.escapementLerp",
        )
        self._escLerpIval.start()
        return

    def _stopEscapementLerp(self):
        if self._escLerpIval is not None and self._escLerpIval.isPlaying():
            self._escLerpIval.pause()
            self._escLerpIval = None
        return

    def getRotation(self):
        return self.getH(self.subject)

    def setRotation(self, rotation):
        self._rotation = rotation
        if self.subject:
            self.setH(self.subject, rotation)

    def getFadeGeom(self):
        return self._fadeGeom

    def setFadeGeom(self, fadeGeom):
        self._fadeGeom = fadeGeom

    def applyFadeGeom(self):
        if self.isActive():
            if not self._fadeGeom and self.getPriorValue():
                if hasattr(self, "_hiddenGeoms"):
                    for np in self._hiddenGeoms.keys():
                        self._unfadeGeom(np)

                    self._hiddenGeoms = {}

    def getIdealDistance(self):
        return self.idealDistance

    def setIdealDistance(self, idealDistance):
        self.idealDistance = idealDistance

    def applyIdealDistance(self):
        if self.isActive():
            self.idealDistance = clampScalar(self.idealDistance, self._minDistance, self._maxDistance)
            if self._practicalDistance is None:
                self._zoomToDistance(self.idealDistance)

    def popToIdealDistance(self):
        self._setCurDistance(self.idealDistance)

    def setPracticalDistance(self, practicalDistance):
        if practicalDistance is not None and practicalDistance > self.idealDistance:
            practicalDistance = None
        if self._practicalDistance is None:
            if practicalDistance is None:
                return
            self._stopZoomIval()
            self._setCurDistance(practicalDistance)
        else:
            self._stopZoomIval()
            if practicalDistance is None:
                self._zoomToDistance(self.idealDistance)
            else:
                self._setCurDistance(practicalDistance)
        self._practicalDistance = practicalDistance
        return

    def getMinDistance(self):
        return self._minDistance

    def setMinDistance(self, minDistance):
        self._minDistance = minDistance

    def applyMinDistance(self):
        if self.isActive():
            self.setIdealDistance(self.idealDistance)

    def getMaxDistance(self):
        return self._maxDistance

    def setMaxDistance(self, maxDistance):
        self._maxDistance = maxDistance

    def applyMaxDistance(self):
        if self.isActive():
            self.setIdealDistance(self.idealDistance)
            if hasattr(self, "_collSolid"):
                self._collSolid.setPointB(0, -(self._maxDistance + OrbitCamera.PullFwdDist), 0)

    def getMinEsc(self):
        return self._minEsc

    def getMaxEsc(self):
        return self._maxEsc

    def getMinDomeEsc(self):
        return self._minDomeEsc

    def getMaxCamtiltEsc(self):
        return self._maxCamtiltEsc

    def setMinEsc(self, minEsc):
        self._minEsc = minEsc

    def setMaxEsc(self, maxEsc):
        self._maxEsc = maxEsc

    def setMinDomeEsc(self, minDomeEsc):
        self._minDomeEsc = minDomeEsc

    def setMaxCamtiltEsc(self, maxCamtiltEsc):
        self._maxCamtiltEsc = maxCamtiltEsc

    def enterActive(self):
        CameraMode.CameraMode.enterActive(self)

        self.reparentTo(render)
        # self.clearTransform()
        # self.setH(self.subject, self._rotation)
        # self.setP(0)
        # self.setR(0)
        # self.camParent.clearTransform()
        camera.reparentTo(self)
        # camera.clearTransform()
        self.lodCenter = base.camNode.getLodCenter()
        base.camNode.setLodCenter(self.subject)

        # self.lookAtNode.reparentTo(self.subject)
        # self.lookAtNode.clearTransform()
        # self.lookAtNode.setPos(self.lookAtOffset)
        #  self.setFluidPos(render, self.lookAtNode.getPos(render))
        # self.escapementNode.setP(-self.escapement)
        # self._setCurDistance(self.idealDistance)
        # camera.lookAt(self.lookAtNode)
        self._disableRotateToRear()
        self._isAtRear = True
        self._rotateToRearIval = None
        self._lockAtRear = False
        self._zoomIval = None
        self._escLerpIval = None
        self._practicalDistance = None
        self.acceptWheel()
        self.reparentTo(self.subject)
        self.setPos(0, 0, self.subject.getHeight())
        base.camera.reparentTo(self)
        camera.setPosHpr(self.camOffset[0], self.camOffset[1], 10, 0, 0, 0)
        self._initMaxDistance()
        # self._startUpdateTask()

        self._startCollisionCheck()
        # self.setCameraPos(-10, 0, 0)

    def exitActive(self):
        taskMgr.remove(OrbitCamera.UpdateTaskName)
        self._stopCollisionCheck()
        # self.ignoreAll()
        # self._stopRotateToRearIval()
        # self._stopCollisionCheck()
        # self.lookAtNode.detachNode()
        # self.detachNode()
        base.camNode.setLodCenter(self.lodCenter)
        self.ignoreWheel()

        base.cmod.disable()
        CameraMode.CameraMode.exitActive(self)

    def _initMaxDistance(self):
        self._maxDistance = abs(self.camOffset[1])

    def acceptWheel(self):
        self.accept("wheel_up", self._handleWheelUp)
        self.accept("wheel_down", self._handleWheelDown)
        self.accept("page_up", self._handleWheelUp)
        self.accept("page_down", self._handleWheelDown)
        self._resetWheel()

    def ignoreWheel(self):
        self.ignore("wheel_up")
        self.ignore("wheel_down")
        self.ignore("page_up")
        self.ignore("page_down")
        self._resetWheel()

    def _handleWheelUp(self):
        y = max(-30, min(-2, self.camOffset[1] + 1.0))
        self._collSolid.setPointB(0, y + 1, 0)
        self.camOffset.setY(y)
        inZ = self.subject.getHeight()
        t = (-15 - y) / -12
        z = lerp(inZ, inZ, t)
        self.setZ(z)

    def _handleWheelDown(self):
        y = max(-30, min(-2, self.camOffset[1] - 1.0))
        self._collSolid.setPointB(0, y + 1, 0)
        self.camOffset.setY(y)
        inZ = self.subject.getHeight()
        t = (-15 - y) / -12
        z = lerp(inZ, inZ, t)
        self.setZ(z)

    def _resetWheel(self):
        if not self.isActive():
            return

        self.camOffset = Vec3(0, -14, 5.5)
        y = self.camOffset[1]
        z = self.camOffset[2]
        self._collSolid.setPointB(0, y + 1, 0)
        self.setZ(z)

    def _startUpdateTask(self):
        self.lastSubjectH = self.subject.getH(render)
        taskMgr.add(self._updateTask, OrbitCamera.UpdateTaskName, priority=40)
        self._updateTask()

    def _updateTask(self, task=None):
        self.setFluidPos(render, self.lookAtNode.getPos(render))
        curSubjectH = self.subject.getH(render)
        if self._lockAtRear:
            self.setRotation(0.0)
        elif self._rotateToRearEnabled and self.getAutoFaceForward():
            relH = reduceAngle(self.getH(self.subject))
            absRelH = abs(relH)
            if absRelH < 0.1:
                self.setRotation(0.0)
                self._stopRotateToRearIval()
                self._lockAtRear = True
            else:
                ivalPlaying = self._rotateToRearIvalIsPlaying()
                if ivalPlaying and curSubjectH == self.lastSubjectH:
                    pass
                else:
                    self._stopRotateToRearIval()
                    duration = self._autoFaceForwardMaxDur * absRelH / 180.0
                    targetH = curSubjectH
                    startH = fitSrcAngle2Dest(self.getH(render), targetH)
                    self._rotateToRearIval = LerpHprInterval(
                        self,
                        duration,
                        Point3(targetH, 0, 0),
                        startHpr=Point3(startH, 0, 0),
                        other=render,
                        blendType="easeOut",
                    )
                    self._rotateToRearIval.start()
        self.lastSubjectH = curSubjectH
        # self.setP(0)
        self.setR(0)
        camera.clearMat()
        return Task.cont

    def _stopUpdateTask(self):
        taskMgr.remove(OrbitCamera.UpdateTaskName)

    def setAutoFaceForward(self, autoFaceForward):
        if not autoFaceForward:
            self._stopRotateToRearIval()
        self._autoFaceForward = autoFaceForward

    def getAutoFaceForward(self):
        return self._autoFaceForward

    def setAutoFaceForwardMaxDur(self, autoFaceForwardMaxDur):
        self._autoFaceForwardMaxDur = autoFaceForwardMaxDur

    def getAutoFaceForwardMaxDur(self):
        return self._autoFaceForwardMaxDur

    def _enableRotateToRear(self):
        self._rotateToRearEnabled = True

    def _disableRotateToRear(self):
        self._stopRotateToRearIval()
        self._rotateToRearEnabled = False

    def _rotateToRearIvalIsPlaying(self):
        return self._rotateToRearIval is not None and self._rotateToRearIval.isPlaying()

    def _stopRotateToRearIval(self):
        if hasattr(self, "_rotateToRearIval"):
            if self._rotateToRearIval is not None and self._rotateToRearIval.isPlaying():
                self._rotateToRearIval.pause()
                self._rotateToRearIval = None
        return

    def _getCurDistance(self):
        return -self.camParent.getY()

    def _setCurDistance(self, distance):
        self.camParent.setY(-distance)

    def _zoomToDistance(self, distance):
        curDistance = self._getCurDistance()
        diff = abs(curDistance - distance)
        if diff < 0.01:
            self._setCurDistance(distance)
            return
        speed = (max(curDistance, self._maxDistance) - min(curDistance, self._minDistance)) * 0.5
        duration = diff / speed
        self._stopZoomIval()
        self._zoomIval = LerpPosInterval(
            self.camParent, duration, Point3(0, -distance, 0), blendType="easeOut", name="orbitCamZoom", fluid=1
        )
        self._zoomIval.start()

    def _stopZoomIval(self):
        if self._zoomIval is not None and self._zoomIval.isPlaying():
            self._zoomIval.pause()
            self._zoomIval = None

    def _startCollisionCheck(self):
        self._collSolid = CollisionSegment(0, 0, 0, 0, -(self._maxDistance + OrbitCamera.PullFwdDist), 0)
        collSolidNode = CollisionNode("OrbitCam.CollSolid")
        collSolidNode.addSolid(self._collSolid)

        collSolidNode.setFromCollideMask(
            CameraBitmask | CameraTransparentBitmask | FloorBitmask
        )
        collSolidNode.setIntoCollideMask(BitMask32.allOff())
        self._collSolidNp = self.attachNewNode(collSolidNode)
        self._cHandlerQueue = CollisionHandlerQueue()
        self._cTrav = CollisionTraverser("OrbitCam.cTrav")
        self._cTrav.addCollider(self._collSolidNp, self._cHandlerQueue)
        self._hiddenGeoms = {}
        self._fadeOutIvals = {}
        self._fadeInIvals = {}
        taskMgr.add(self._collisionCheckTask, OrbitCamera.CollisionCheckTaskName, priority=45)

    def _stopCollisionCheck(self):
        taskMgr.remove(OrbitCamera.CollisionCheckTaskName)
        self._cTrav.removeCollider(self._collSolidNp)
        del self._cHandlerQueue
        del self._cTrav
        self._collSolidNp.detachNode()
        del self._collSolidNp

    def _fadeGeom(self, np):
        if np in self._fadeInIvals:
            self._fadeInIvals[np].finish()
            del self._fadeInIvals[np]
        if np not in self._hiddenGeoms:
            hadTransparency = np.getTransparency()
            fadeIval = Sequence(
                Func(np.setTransparency, 1),
                LerpColorScaleInterval(np, OrbitCamera.GeomFadeLerpDur, VBase4(1, 1, 1, 0), blendType="easeInOut"),
                name="OrbitCamFadeGeomOut",
            )
            self._hiddenGeoms[np] = hadTransparency
            self._fadeOutIvals[np] = fadeIval
            fadeIval.start()

    def _unfadeGeom(self, np):
        if np in self._hiddenGeoms:
            if np in self._fadeOutIvals:
                self._fadeOutIvals[np].pause()
                del self._fadeOutIvals[np]
            fadeIval = Sequence(
                LerpColorScaleInterval(np, OrbitCamera.GeomFadeLerpDur, VBase4(1, 1, 1, 1), blendType="easeInOut"),
                Func(np.setTransparency, self._hiddenGeoms[np]),
                name="OrbitCamFadeGeomIn",
            )
            del self._hiddenGeoms[np]
            self._fadeInIvals[np] = fadeIval
            fadeIval.start()

    def enableMouseControl(self):
        CameraMode.CameraMode.enableMouseControl(self)
        self.subject.controlManager.setWASDTurn(0)
        self.accept("mouse1", self.startOrbitalMovement)
        self.accept("mouse1-up", self.stopOrbitalMovement)

    def disableMouseControl(self):
        CameraMode.CameraMode.disableMouseControl(self)
        self.subject.controlManager.setWASDTurn(1)
        self.stopOrbitalMovement()
        self.ignore("mouse1")
        self.ignore("mouse1-up")

    def startOrbitalMovement(self):
        self.usingOrbitalRun = True
        self.toonWasWalking = base.walking
        messenger.send(base.MOVE_FORWARD)
        self.accept(f"{base.MOVE_FORWARD}-up", self.triggerToonWalk, extraArgs=[False])
        self.accept(base.MOVE_FORWARD, self.triggerToonWalk, extraArgs=[True])

    def triggerToonWalk(self, walking):
        if self.acceptingMovement:
            self.toonWasWalking = walking

        self.acceptingMovement = walking
        if not walking:
            messenger.send(base.MOVE_FORWARD)

    def stopOrbitalMovement(self):
        if not self.usingOrbitalRun:
            return
        self.usingOrbitalRun = False
        self.ignore(f"{base.MOVE_FORWARD}-up")
        self.ignore(base.MOVE_FORWARD)
        if not self.toonWasWalking:
            messenger.send(f"{base.MOVE_FORWARD}-up")
        self.toonWasWalking = None
        self.acceptingMovement = True

    def _avatarFacingTask(self, task):
        if hasattr(base, "oobeMode") and base.oobeMode:
            return task.cont

        if self.avFacingScreen:
            return task.cont

        if self.isSubjectMoving():
            camH = self.getH(render)
            subjectH = self.subject.getH(render)
            if abs(camH - subjectH) > 0.01:
                self.subject.setH(render, camH)
                self.setH(0)
        return task.cont

    def isSubjectMoving(self):
        return (
            inputState.isSet("forward")
            or inputState.isSet("reverse")
            or inputState.isSet("turnRight")
            or inputState.isSet("turnLeft")
            or inputState.isSet("slideRight")
            or inputState.isSet("slideLeft")
        ) and self.subject.controlManager.isEnabled

    def _mouseUpdateTask(self, task):
        if hasattr(base, "oobeMode") and base.oobeMode:
            return task.cont
        subjectTurning = (
            inputState.isSet("turnRight") or inputState.isSet("turnLeft")
        ) and self.subject.controlManager.isEnabled
        # if subjectMoving:
        #   hNode = self.subject
        # else:
        hNode = self

        if self.mouseDelta[0] or self.mouseDelta[1]:
            dx, dy = self.mouseDelta
            if subjectTurning:
                dx += dx

            hNode.setH(hNode, -dx * self.SensitivityH)
            curP = self.getP()
            newP = curP + -dy * self.SensitivityP
            newP = min(max(newP, self.MinP), self.MaxP)
            self.setP(newP)
            if self.baseH:
                self._checkHBounds(hNode)

            self.setR(render, 0)

        return task.cont

    def setHBounds(self, baseH, minH, maxH):
        self.baseH = baseH
        self.minH = minH
        self.maxH = maxH
        # if self.isSubjectMoving():
        # hNode = self.subject
        # else:
        hNode = self

        hNode.setH(maxH)

    def clearHBounds(self):
        self.baseH = self.minH = self.maxH = None

    def _checkHBounds(self, hNode):
        currH = fitSrcAngle2Dest(hNode.getH(), 180)
        if currH < self.minH:
            hNode.setH(reduceAngle(self.minH))
        elif currH > self.maxH:
            hNode.setH(reduceAngle(self.maxH))

    def _collisionCheckTask(self, task=None):
        # From FPSCamera Potco
        if hasattr(base, "oobeMode") and base.oobeMode:
            return Task.cont

        self._cTrav.traverse(render)
        try:
            self._cHandlerQueue.sortEntries()
        except AssertionError:
            return Task.cont

        cNormal = (0, -1, 0)
        collEntry = None
        for i in range(self._cHandlerQueue.getNumEntries()):
            collEntry = self._cHandlerQueue.getEntry(i)
            cNormal = collEntry.getSurfaceNormal(self)
            if cNormal[1] < 0:
                break

        if not collEntry:
            camera.setPos(self.camOffset)
            camera.setZ(0)
            return task.cont
        cPoint = collEntry.getSurfacePoint(self)
        offset = 0.9
        camera.setPos(cPoint + cNormal * offset)

        self._cTrav.traverse(render)
        return Task.cont

    def getCamOffset(self):
        return self.camOffset

    def setCamOffset(self, camOffset):
        self.camOffset = Vec3(camOffset)

    def applyCamOffset(self):
        if self.isActive():
            camera.setPos(self.camOffset)

    def setGeomNodeH(self, h):
        geom_node = self.subject.getGeomNode()
        if self.lastGeomH != h:
            LerpHprInterval(geom_node, 0.07, Vec3(h, 0, 0), blendType="easeInOut").start()
            self.lastGeomH = h

    def setCameraPos(self, y, h, p, zDelta=0):
        t = (-14 - y) / -12
        z = self.subject.getHeight() + zDelta
        self._collSolid.setPointB(0, y + 1, 0)
        self.camOffset.setY(y)
        self.setPos(self.getX(), self.getY(), z)
        self.setHpr(h, p, 0)
