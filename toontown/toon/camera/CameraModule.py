from direct.interval.LerpInterval import LerpFunctionInterval
from direct.showbase.DirectObject import DirectObject
from panda3d.core import (
    BitMask32,
    CollisionHandlerFloor,
    CollisionHandlerPusher,
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionSegment,
    CollisionSphere,
    CollisionTraverser,
    ConfigVariableBool,
)

from toontown.toon.camera.OrbitalCamera import OrbitalCamera
from toontown.toonbase.globals.TTGlobalsRender import CameraBitmask, FloorBitmask


class CameraModule(DirectObject):
    notify = directNotify.newCategory("CameraModule")

    def __init__(self, toon):
        self.toon = toon
        self.orbitalCamera = OrbitalCamera(toon)
        self.currentCamera = self.orbitalCamera

        self.traversalGeom = render
        self.ccTrav = CollisionTraverser("LocalAvatar.ccTrav")

        self.ccLine = CollisionSegment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.ccLineNode = CollisionNode("ccLineNode")
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.toon.attachNewNode(self.ccLineNode)
        self.ccLineNode.setFromCollideMask(CameraBitmask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())

        self.camCollisionQueue = CollisionHandlerQueue()

        self.ccTrav.addCollider(self.ccLineNodePath, self.camCollisionQueue)

        self.ccSphere = CollisionSphere(0, 0, 0, 1)
        self.ccSphereNode = CollisionNode("ccSphereNode")
        self.ccSphereNode.addSolid(self.ccSphere)
        self.ccSphereNodePath = base.camera.attachNewNode(self.ccSphereNode)
        self.ccSphereNode.setFromCollideMask(CameraBitmask)
        self.ccSphereNode.setIntoCollideMask(BitMask32.allOff())

        self.camPusher = CollisionHandlerPusher()
        self.camPusher.addCollider(self.ccSphereNodePath, base.camera)

        self.camPusher.setCenter(self.toon)

        self.ccPusherTrav = CollisionTraverser("LocalAvatar.ccPusherTrav")

        self.ccSphere2 = self.ccSphere
        self.ccSphereNode2 = CollisionNode("ccSphereNode2")
        self.ccSphereNode2.addSolid(self.ccSphere2)
        self.ccSphereNodePath2 = base.camera.attachNewNode(self.ccSphereNode2)
        self.ccSphereNode2.setFromCollideMask(CameraBitmask)
        self.ccSphereNode2.setIntoCollideMask(BitMask32.allOff())

        self.camPusher2 = CollisionHandlerPusher()
        self.ccPusherTrav.addCollider(self.ccSphereNodePath2, self.camPusher2)
        self.camPusher2.addCollider(self.ccSphereNodePath2, base.camera)

        self.camPusher2.setCenter(self.toon)

        self.camFloorRayNode = self.toon.attachNewNode("camFloorRayNode")

        self.ccRay = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRayNode = CollisionNode("ccRayNode")
        self.ccRayNode.addSolid(self.ccRay)
        self.ccRayNodePath = self.camFloorRayNode.attachNewNode(self.ccRayNode)
        self.ccRayBitMask = FloorBitmask
        self.ccRayNode.setFromCollideMask(self.ccRayBitMask)
        self.ccRayNode.setIntoCollideMask(BitMask32.allOff())

        self.ccTravFloor = CollisionTraverser("LocalAvatar.ccTravFloor")

        self.camFloorCollisionQueue = CollisionHandlerQueue()
        self.ccTravFloor.addCollider(self.ccRayNodePath, self.camFloorCollisionQueue)

        self.ccTravOnFloor = CollisionTraverser("LocalAvatar.ccTravOnFloor")

        self.ccRay2 = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRay2Node = CollisionNode("ccRay2Node")
        self.ccRay2Node.addSolid(self.ccRay2)
        self.ccRay2NodePath = self.camFloorRayNode.attachNewNode(self.ccRay2Node)
        self.ccRay2BitMask = FloorBitmask
        self.ccRay2Node.setFromCollideMask(self.ccRay2BitMask)
        self.ccRay2Node.setIntoCollideMask(BitMask32.allOff())

        self.ccRay2MoveNodePath = hidden.attachNewNode("ccRay2MoveNode")

        self.camFloorCollisionBroadcaster = CollisionHandlerFloor()
        self.camFloorCollisionBroadcaster.setInPattern("on-floor")
        self.camFloorCollisionBroadcaster.setOutPattern("off-floor")
        self.camFloorCollisionBroadcaster.addCollider(self.ccRay2NodePath, self.ccRay2MoveNodePath)

        self.cameraLerp = None

        self.cameraPresets = [(-9, 0, 0), (-24, 0, -10), (-12, 0, -15)]  # (y, heading, pitch)
        self.currentPreset = 0
        self.currentOverride = None
        self.cameraOverrides = []

        if ConfigVariableBool("enable-camera-debug", 0):
            taskMgr.doMethodLater(1, self.debugCameraPosition, "CameraDebug")

        base.cmod = self

    def debugCameraPosition(self, task):
        print(camera, camera.getPosHpr(), self.currentCamera.getPosHpr())
        return task.again

    def enable(self, inputAllowed=True):
        self.stopCameraLerp()
        self.ccTravOnFloor.addCollider(self.ccRay2NodePath, self.camFloorCollisionBroadcaster)
        self.toon.cTrav.addCollider(self.ccSphereNodePath, self.camPusher)
        taskMgr.remove("updateSmartCamera")
        taskMgr.add(self.updateSmartCamera, "updateSmartCamera", priority=47)
        self.setPreset(self.currentPreset)
        self.currentCamera.start()
        if inputAllowed:
            self.currentCamera.enableInput()
        self.acceptTab()

    def disable(self):
        self.stopCameraLerp()
        self.currentCamera.stop()
        self.toon.cTrav.removeCollider(self.ccSphereNodePath)
        self.ccTravOnFloor.removeCollider(self.ccRay2NodePath)
        taskMgr.remove("updateSmartCamera")
        self.ignoreTab()

    def setGeom(self, node):
        self.traversalGeom = node

    def updateSmartCamera(self, task):
        self.ccTrav.traverse(self.traversalGeom)
        self.ccPusherTrav.traverse(self.traversalGeom)
        self.ccTravOnFloor.traverse(self.traversalGeom)
        return task.cont

    def destroy(self):
        self.disable()
        self.orbitalCamera.destroy()

        self.ccLineNodePath.removeNode()
        self.ccRayNodePath.removeNode()
        self.ccRay2NodePath.removeNode()
        self.ccRay2MoveNodePath.removeNode()
        self.ccSphereNodePath.removeNode()
        self.ccSphereNodePath2.removeNode()

        self.stopCameraLerp()
        taskMgr.remove("CameraDebug")

    def lerpFov(self, fov, duration):
        self.stopCameraLerp()

        currentFov = base.camLens.getHfov()
        if abs(currentFov - fov) > 0.1:
            duration *= abs(currentFov - fov) / 20
            self.cameraLerp = LerpFunctionInterval(base.camLens.setFov, duration, fromData=currentFov, toData=fov)
            self.cameraLerp.start()
        else:
            base.camLens.setFov(fov)
            self.cameraLerp = None

    def override(self, pos):
        self.forceOrbitalCam()
        self.cameraOverrides.append(pos)
        self.setCameraPosition(pos)

    def removeOverride(self, pos):
        try:
            self.cameraOverrides.remove(pos)
        except ValueError:
            self.revertPos()
            return

        if self.cameraPresets:
            self.setCameraPosition(self.cameraPresets[-1])
        else:
            self.revertPos()
        self.acceptTab()

    def setPreset(self, presetIndex=None):
        if presetIndex is not None:
            if presetIndex >= len(self.cameraPresets) or presetIndex < 0:
                self.notify.warning(f"Invalid preset index: {presetIndex}")
                return

            self.currentPreset = presetIndex
        self.setCameraPosition(self.cameraPresets[self.currentPreset])

    def setCameraPosition(self, pos):
        if self.currentCamera == self.orbitalCamera:
            self.orbitalCamera.start()
            self.currentCamera.setCameraPos(*pos)

    def revertPos(self):
        self.cameraOverrides = []
        self.setPreset(self.currentPreset)

    def stopCameraLerp(self):
        if self.cameraLerp is not None:
            self.cameraLerp.pause()
            self.cameraLerp = None

    def acceptTab(self):
        self.accept("tab", self.toggleFirstPerson)

    def ignoreTab(self):
        self.ignore("tab")

    def toggleFirstPerson(self):
        self.currentPreset = (self.currentPreset + 1) % len(self.cameraPresets)
        self.revertPos()

    def setCameraMode(self, mode):
        if isinstance(mode, str):
            mode = getattr(self, mode)
        self.currentCamera.stop()
        self.currentCamera = mode
        self.currentCamera.start()
        self.acceptTab()

    def forceOrbitalCam(self):
        if self.currentCamera == self.orbitalCamera:
            return
        self.currentCamera.stop()
        self.currentCamera = self.orbitalCamera
        self.currentCamera.start()
        self.ignoreTab()

    def reparentToRender(self):
        self.currentCamera.request("Off")
        camera.reparentTo(render)
