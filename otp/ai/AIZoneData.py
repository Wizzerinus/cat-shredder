from direct.distributed import ParentMgr
from direct.task import Task
from panda3d.core import BitMask32, CollisionTraverser, NodePath

from toontown.toonbase.globals.TTGlobalsCore import AICollisionPriority, SPHidden, SPRender


class AIZoneData:
    """This is a proxy to the AIZoneDataObj for a particular zone. When all
    AIZoneData objects for a zone have been destroyed, the AIZoneDataObj
    object for that zone is destroyed as well."""

    notify = directNotify.newCategory("AIZoneData")

    def __init__(self, air, parentId, zoneId):
        self._air = air
        self._parentId = parentId
        self._zoneId = zoneId
        self._data = self._air.getZoneDataStore().getDataForZone(self._parentId, self._zoneId)

    def destroy(self):
        self._data = None
        self._air.getZoneDataStore().releaseDataForZone(self._parentId, self._zoneId)
        self._zoneId = None
        self._parentId = None
        self._air = None

    def __getattr__(self, attr):
        return getattr(self._data, attr)


class AIZoneDataObj:
    """
    This class stores per-zone information on an AI district. Only one of these
    exists for a particular zone, and it only exists if somebody requested it.
    """

    notify = directNotify.newCategory("AIZoneDataObj")

    DefaultCTravName = "default"
    _render = None
    _parentMgr = None
    _nonCollidableParent = None

    def __init__(self, parentId, zoneId):
        assert self.notify.debug(f"AIZoneDataObj.__init__({parentId}, {zoneId})")
        self._parentId = parentId
        self._zoneId = zoneId
        self._refCount = 0
        self._collTravs = {}
        self._collTravsStarted = set()

    def __str__(self):
        output = str(self._collTravs)
        output += "\n"
        totalColliders = 0
        totalTraversers = 0
        for currCollTrav in list(self._collTravs.values()):
            totalTraversers += 1
            totalColliders += currCollTrav.getNumColliders()
        output += f"Num traversers: {totalTraversers}  Num total colliders: {totalColliders}"
        return output

    def incRefCount(self):
        self._refCount += 1

    def decRefCount(self):
        self._refCount -= 1

    def getRefCount(self):
        return self._refCount

    def destroy(self):
        assert self.notify.debug(f"AIZoneDataObj.destroy({self._parentId}, {self._zoneId})")
        for name in list(self._collTravsStarted):
            self.stopCollTrav(cTravName=name)
        del self._collTravsStarted
        del self._collTravs
        if self._nonCollidableParent:
            self._nonCollidableParent.removeNode()
            del self._nonCollidableParent
        if self._render:
            self._render.removeNode()
            self._render = None
        if self._parentMgr:
            self._parentMgr.destroy()
            del self._parentMgr
        del self._zoneId
        del self._parentId

    def getLocation(self):
        return self._parentId, self._zoneId

    def getRender(self):
        if not self._render:
            self._render = NodePath(f"render-{self._parentId}-{self._zoneId}")
        return self._render

    def getNonCollidableParent(self):
        if not self._nonCollidableParent:
            renderNode = self.getRender()
            self._nonCollidableParent = renderNode.attachNewNode("nonCollidables")
        if __dev__:
            assert (
                self._nonCollidableParent.getCollideMask() == BitMask32().allOff()
            ), f"collidable geometry under non-collidable parent node for location ({self._parentId},{self._zoneId})"
        return self._nonCollidableParent

    def getParentMgr(self):
        if not self._parentMgr:
            self._parentMgr = ParentMgr.ParentMgr()
            self._parentMgr.registerParent(SPHidden, hidden)
            self._parentMgr.registerParent(SPRender, self.getRender())
        return self._parentMgr

    def hasCollTrav(self, name=None):
        if name is None:
            name = AIZoneDataObj.DefaultCTravName
        return name in self._collTravs

    def getCollTrav(self, name=None):
        if name is None:
            name = AIZoneDataObj.DefaultCTravName
        if name not in self._collTravs:
            self._collTravs[name] = CollisionTraverser(f"cTrav-{name}-{self._parentId}-{self._zoneId}")
        return self._collTravs[name]

    def removeCollTrav(self, name):
        if name in self._collTravs:
            del self._collTravs[name]

    def _getCTravTaskName(self, name=None):
        if name is None:
            name = AIZoneDataObj.DefaultCTravName
        return f"collTrav-{name}-{self._parentId}-{self._zoneId}"

    def _doCollisions(self, topNode=None, cTravName=None):
        renderNode = self.getRender()
        curTime = globalClock.getFrameTime()
        renderNode.setTag("lastTraverseTime", str(curTime))
        if topNode is not None:
            if not renderNode.isAncestorOf(topNode):
                self.notify.warning(f"invalid topNode for collision traversal in {self.getLocation()}: {topNode}")
        else:
            topNode = renderNode

        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName

        collTrav = self._collTravs[cTravName]
        messenger.send(f"preColl-{collTrav.getName()}")
        collTrav.traverse(topNode)
        messenger.send(f"postColl-{collTrav.getName()}")

        return Task.cont

    def doCollTrav(self, topNode=None, cTravName=None):
        assert self.notify.debug(f"doCollTrav({self._parentId}, {self._zoneId})")
        self.getCollTrav(cTravName)
        self._doCollisions(topNode=topNode, cTravName=cTravName)

    def startCollTrav(self, respectPrevTransform=1, cTravName=None):
        """sets up and starts collision traverser for this zone.
        Pass in zero for 'respectPrevTransform' to disable support for
        tunneling/trailing sphere support. This will allow objects to
        break through collision barriers, but may run faster -- see
        drose for more info.
        """
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        assert self.notify.debug(
            f"startCollTrav({cTravName}, ({self._parentId}, {self._zoneId}), {respectPrevTransform})"
        )
        if cTravName not in self._collTravsStarted:
            self.getCollTrav(name=cTravName)
            taskMgr.add(
                self._doCollisions,
                self._getCTravTaskName(name=cTravName),
                priority=AICollisionPriority,
                extraArgs=[],
            )
            self._collTravsStarted.add(cTravName)
            assert self.notify.debug(f"adding {cTravName} collision traversal for ({self._parentId}, {self._zoneId})")
        self.setRespectPrevTransform(respectPrevTransform, cTravName=cTravName)

    def stopCollTrav(self, cTravName=None):
        """frees resources used by collision traverser for this zone"""
        assert self.notify.debugStateCall(self)
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        self.notify.debug(f"stopCollTrav({cTravName}, {self._parentId}, {self._zoneId})")
        if cTravName in self._collTravsStarted:
            self.notify.info(f"removing {cTravName} collision traversal for ({self._parentId}, {self._zoneId})")
            taskMgr.remove(self._getCTravTaskName(name=cTravName))
            self._collTravsStarted.remove(cTravName)

    def setRespectPrevTransform(self, flag, cTravName=None):
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        self._collTravs[cTravName].setRespectPrevTransform(flag)

    def getRespectPrevTransform(self, cTravName=None):
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        return self._collTravs[cTravName].getRespectPrevTransform()


class AIZoneDataStore:
    """This class holds all of the AIZoneDataObj objects for a district."""

    notify = directNotify.newCategory("AIZoneDataStore")

    def __init__(self):
        self._zone2data = {}

    def destroy(self):
        for _zone, data in list(self._zone2data.items()):
            data.destroy()
        del self._zone2data

    def hasDataForZone(self, parentId, zoneId):
        key = (parentId, zoneId)
        return key in self._zone2data

    def getDataForZone(self, parentId, zoneId):
        key = (parentId, zoneId)
        if key not in self._zone2data:
            self._zone2data[key] = AIZoneDataObj(parentId, zoneId)
            self.printStats()
        data = self._zone2data[key]
        data.incRefCount()
        return data

    def releaseDataForZone(self, parentId, zoneId):
        key = (parentId, zoneId)
        data = self._zone2data[key]
        data.decRefCount()
        refCount = data.getRefCount()
        assert refCount >= 0
        if refCount == 0:
            del self._zone2data[key]
            data.destroy()
            self.printStats()

    def printStats(self):
        self.notify.debug(f"{len(self._zone2data)} zones have zone data allocated")
