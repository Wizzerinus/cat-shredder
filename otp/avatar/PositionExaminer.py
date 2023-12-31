from direct.showbase.DirectObject import DirectObject
from panda3d.core import (
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionSegment,
    CollisionSphere,
    CollisionTraverser,
    NodePath,
)

from toontown.toonbase.globals.TTGlobalsRender import *


class PositionExaminer(DirectObject, NodePath):
    """
    This class defines an object that can be used to examine a point in
    space for suitability for standing on.  It's used, for instance,
    to choose a particular point to Go to when you Goto a friend.

    A valid destination point is one that (a) has a ground whose
    height is not too far from our target height, (b) is not already
    occupied, and (c) is not behind a wall.
    """

    PositionExaminerInitialized = False

    def __init__(self):
        if self.PositionExaminerInitialized:
            return

        self.PositionExaminerInitialized = True

        NodePath.__init__(self, hidden.attachNewNode("PositionExaminer"))

        self.cRay = CollisionRay(0.0, 0.0, 6.0, 0.0, 0.0, -1.0)
        self.cRayNode = CollisionNode("cRayNode")
        self.cRayNode.addSolid(self.cRay)
        self.cRayNodePath = self.attachNewNode(self.cRayNode)
        self.cRayNodePath.hide()
        self.cRayBitMask = FloorBitmask
        self.cRayNode.setFromCollideMask(self.cRayBitMask)
        self.cRayNode.setIntoCollideMask(BitMask32.allOff())

        self.cSphere = CollisionSphere(0.0, 0.0, 0.0, 1.5)
        self.cSphereNode = CollisionNode("cSphereNode")
        self.cSphereNode.addSolid(self.cSphere)
        self.cSphereNodePath = self.attachNewNode(self.cSphereNode)
        self.cSphereNodePath.hide()
        self.cSphereBitMask = WallBitmask
        self.cSphereNode.setFromCollideMask(self.cSphereBitMask)
        self.cSphereNode.setIntoCollideMask(BitMask32.allOff())

        self.ccLine = CollisionSegment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.ccLineNode = CollisionNode("ccLineNode")
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.attachNewNode(self.ccLineNode)
        self.ccLineNodePath.hide()
        self.ccLineBitMask = CameraBitmask
        self.ccLineNode.setFromCollideMask(self.ccLineBitMask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())

        self.cRayTrav = CollisionTraverser("PositionExaminer.cRayTrav")
        self.cRayTrav.setRespectPrevTransform(False)
        self.cRayQueue = CollisionHandlerQueue()
        self.cRayTrav.addCollider(self.cRayNodePath, self.cRayQueue)

        self.cSphereTrav = CollisionTraverser("PositionExaminer.cSphereTrav")
        self.cSphereTrav.setRespectPrevTransform(False)
        self.cSphereQueue = CollisionHandlerQueue()
        self.cSphereTrav.addCollider(self.cSphereNodePath, self.cSphereQueue)

        self.ccLineTrav = CollisionTraverser("PositionExaminer.ccLineTrav")
        self.ccLineTrav.setRespectPrevTransform(False)
        self.ccLineQueue = CollisionHandlerQueue()
        self.ccLineTrav.addCollider(self.ccLineNodePath, self.ccLineQueue)

    def delete(self):
        del self.cRay
        del self.cRayNode
        self.cRayNodePath.removeNode()
        del self.cRayNodePath

        del self.cSphere
        del self.cSphereNode
        self.cSphereNodePath.removeNode()
        del self.cSphereNodePath

        del self.ccLine
        del self.ccLineNode
        self.ccLineNodePath.removeNode()
        del self.ccLineNodePath

        del self.cRayTrav
        del self.cRayQueue

        del self.cSphereTrav
        del self.cSphereQueue

        del self.ccLineTrav
        del self.ccLineQueue

    def consider(self, node, pos, eyeHeight):
        """consider(self, NodePath node, Point3 pos, eyeHeight)

        Considers the indicated point, relative to the given NodePath.
        The point must have a floor polygon that's within a foot or
        two of the NodePath's origin, there must be no one standing
        near the point, and it must have a clear line-of-sight to the
        NodePath's origin.

        Returns the actual point to stand if all these conditions are
        met, or None if one of them fails.
        """
        self.reparentTo(node)
        self.setPos(pos)

        result = None

        self.cRayTrav.traverse(render)
        if self.cRayQueue.getNumEntries() != 0:
            self.cRayQueue.sortEntries()
            floorPoint = self.cRayQueue.getEntry(0).getSurfacePoint(self.cRayNodePath)

            if abs(floorPoint[2]) <= 4.0:
                pos += floorPoint
                self.setPos(pos)

                self.cSphereTrav.traverse(render)
                if self.cSphereQueue.getNumEntries() == 0:
                    self.ccLine.setPointA(0, 0, eyeHeight)
                    self.ccLine.setPointB(-pos[0], -pos[1], eyeHeight)
                    self.ccLineTrav.traverse(render)
                    if self.ccLineQueue.getNumEntries() == 0:
                        result = pos

        self.reparentTo(hidden)
        self.cRayQueue.clearEntries()
        self.cSphereQueue.clearEntries()
        self.ccLineQueue.clearEntries()

        return result
