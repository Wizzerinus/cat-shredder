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

from toontown.toon.camera.OrbitalCamera import OrbitCamera
from toontown.toonbase.globals.TTGlobalsRender import *


class CameraModule(DirectObject):
    notify = directNotify.newCategory("CameraModule")

    def __init__(self, toon):
        self.toon = toon
        self.orbitalCamera = OrbitCamera(toon)

        self.traversalGeom = render
        self.ccTrav = CollisionTraverser("LocalAvatar.ccTrav")

        # Set up the camera obstruction test line segment
        # This is a line segment from the visibility point to the ideal
        # camera location
        self.ccLine = CollisionSegment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.ccLineNode = CollisionNode("ccLineNode")
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.toon.attachNewNode(self.ccLineNode)
        self.ccLineNode.setFromCollideMask(CameraBitmask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())

        # set up camera collision mechanism
        self.camCollisionQueue = CollisionHandlerQueue()

        # set up camera obstruction collision reciever
        self.ccTrav.addCollider(self.ccLineNodePath, self.camCollisionQueue)

        # set up a sphere around camera to keep it away from the walls

        # make the collision sphere, its attribs will be calculated later
        self.ccSphere = CollisionSphere(0, 0, 0, 1)
        self.ccSphereNode = CollisionNode("ccSphereNode")
        self.ccSphereNode.addSolid(self.ccSphere)
        self.ccSphereNodePath = base.camera.attachNewNode(self.ccSphereNode)
        self.ccSphereNode.setFromCollideMask(CameraBitmask)
        self.ccSphereNode.setIntoCollideMask(BitMask32.allOff())

        # attach a pusher to the sphere
        self.camPusher = CollisionHandlerPusher()
        # Do this when the camera gets activated
        self.camPusher.addCollider(self.ccSphereNodePath, base.camera)

        # Set a special mode on the pusher so that it doesn't get
        # fooled by walls facing away from the toon.
        self.camPusher.setCenter(self.toon)

        # create another traverser with a camera pusher
        # sphere so that we can push the camera at will
        self.ccPusherTrav = CollisionTraverser("LocalAvatar.ccPusherTrav")

        # make the sphere
        self.ccSphere2 = self.ccSphere
        self.ccSphereNode2 = CollisionNode("ccSphereNode2")
        self.ccSphereNode2.addSolid(self.ccSphere2)
        self.ccSphereNodePath2 = base.camera.attachNewNode(self.ccSphereNode2)
        self.ccSphereNode2.setFromCollideMask(CameraBitmask)
        self.ccSphereNode2.setIntoCollideMask(BitMask32.allOff())

        # attach a pusher to the sphere
        self.camPusher2 = CollisionHandlerPusher()
        self.ccPusherTrav.addCollider(self.ccSphereNodePath2, self.camPusher2)
        self.camPusher2.addCollider(self.ccSphereNodePath2, base.camera)

        # Set a special mode on the pusher so that it doesn't get
        # fooled by walls facing away from the toon.
        self.camPusher2.setCenter(self.toon)

        # create a separate node for the camera's floor-detection ray
        # If we just parented the ray to the camera, it would rotate
        # with the camera and no longer be facing straight down.
        self.camFloorRayNode = self.toon.attachNewNode("camFloorRayNode")

        # set up camera collision mechanisms

        # Set up the "cameraman" collison ray
        # This is a ray cast from the camera down to detect floor polygons
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

        # set up another ray to generate on-floor/off-floor events
        self.ccRay2 = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRay2Node = CollisionNode("ccRay2Node")
        self.ccRay2Node.addSolid(self.ccRay2)
        self.ccRay2NodePath = self.camFloorRayNode.attachNewNode(self.ccRay2Node)
        self.ccRay2BitMask = FloorBitmask
        self.ccRay2Node.setFromCollideMask(self.ccRay2BitMask)
        self.ccRay2Node.setIntoCollideMask(BitMask32.allOff())

        # dummy node for CollisionHandlerFloor to move
        self.ccRay2MoveNodePath = hidden.attachNewNode("ccRay2MoveNode")

        self.camFloorCollisionBroadcaster = CollisionHandlerFloor()
        self.camFloorCollisionBroadcaster.setInPattern("on-floor")
        self.camFloorCollisionBroadcaster.setOutPattern("off-floor")
        # detect the floor with ccRay2, and move a dummy node
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
        print(camera, camera.getPosHpr(), self.orbitalCamera.getPosHpr())  # noqa
        return task.again

    def enable(self):
        self.stopCameraLerp()
        self.ccTravOnFloor.addCollider(self.ccRay2NodePath, self.camFloorCollisionBroadcaster)
        self.toon.cTrav.addCollider(self.ccSphereNodePath, self.camPusher)
        taskMgr.remove("updateSmartCamera")
        taskMgr.add(self.updateSmartCamera, "updateSmartCamera", priority=47)
        self.setPreset(self.currentPreset)
        self.orbitalCamera.start()
        self.acceptTab()

    def disable(self):
        self.stopCameraLerp()
        self.orbitalCamera.stop()
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

        if self.cameraLerp:
            self.cameraLerp.finish()
            self.cameraLerp = None

        taskMgr.remove("CameraDebug")

    def lerpFov(self, fov, duration):
        if self.cameraLerp:
            self.cameraLerp.finish()

        currentFov = base.camLens.getHfov()
        if abs(currentFov - fov) > 0.1:
            self.cameraLerp = LerpFunctionInterval(base.camLens.setFov, duration, fromData=currentFov, toData=fov)
            self.cameraLerp.start()
        else:
            base.camLens.setFov(fov)
            self.cameraLerp = None

    def override(self, pos):
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

    def setPreset(self, presetIndex):
        if presetIndex >= len(self.cameraPresets) or presetIndex < 0:
            self.notify.warning(f"Invalid preset index: {presetIndex}")
            return

        self.currentPreset = presetIndex
        self.setCameraPosition(self.cameraPresets[presetIndex])

    def setCameraPosition(self, pos):
        self.orbitalCamera.start()
        self.orbitalCamera.setCameraPos(*pos)

    def revertPos(self):
        self.cameraOverrides = []
        self.setPreset(self.currentPreset)

    def stopCameraLerp(self):
        if self.cameraLerp is not None:
            self.cameraLerp.finish()
            self.cameraLerp = None

    def acceptTab(self):
        self.accept("tab", self.toggleFirstPerson)

    def ignoreTab(self):
        self.ignore("tab")

    def toggleFirstPerson(self):
        self.currentPreset = (self.currentPreset + 1) % len(self.cameraPresets)
        self.revertPos()

    def reparentToRender(self):
        self.orbitalCamera.request("Off")
        camera.reparentTo(render)
