import pathlib
import sys
import time

from direct.showbase.PythonUtil import *

__all__ = ["ParamObj"]


"""
ParamObj/ParamSet
=================
These two classes support you in the definition of a formal set of
parameters for an object type. The parameters may be safely queried/set on
an object instance at any time, and the object will react to newly-set
values immediately.
ParamSet & ParamObj also provide a mechanism for atomically setting
multiple parameter values before allowing the object to react to any of the
new values--useful when two or more parameters are interdependent and there
is risk of setting an illegal combination in the process of applying a new
set of values.
To make use of these classes, derive your object from ParamObj. Then define
a 'ParamSet' subclass that derives from the parent class' 'ParamSet' class,
and define the object's parameters within its ParamSet class. (see examples
below)
The ParamObj base class provides 'get' and 'set' functions for each
parameter if they are not defined. These default implementations
respectively set the parameter value directly on the object, and expect the
value to be available in that location for retrieval.
Classes that derive from ParamObj can optionally declare a 'get' and 'set'
function for each parameter. The setter should simply store the value in a
location where the getter can find it; it should not do any further
processing based on the new parameter value. Further processing should be
implemented in an 'apply' function. The applier function is optional, and
there is no default implementation.
NOTE: the previous value of a parameter is available inside an apply
function as 'self.getPriorValue()'
The ParamSet class declaration lists the parameters and defines a default
value for each. ParamSet instances represent a complete set of parameter
values. A ParamSet instance created with no constructor arguments will
contain the default values for each parameter. The defaults may be
overriden by passing keyword arguments to the ParamSet's constructor. If a
ParamObj instance is passed to the constructor, the ParamSet will extract
the object's current parameter values.
ParamSet.applyTo(obj) sets all of its parameter values on 'obj'.
SETTERS AND APPLIERS
====================
Under normal conditions, a call to a setter function, i.e.
 cam.setFov(90)
will actually result in the following calls being made:
 cam.setFov(90)
 cam.applyFov()
Calls to several setter functions, i.e.
 cam.setFov(90)
 cam.setViewType('cutscene')
will result in this call sequence:
 cam.setFov(90)
 cam.applyFov()
 cam.setViewType('cutscene')
 cam.applyViewType()
Suppose that you desire the view type to already be set to 'cutscene' at
the time when applyFov() is called. You could reverse the order of the set
calls, but suppose that you also want the fov to be set properly at the
time when applyViewType() is called.
In this case, you can 'lock' the params, i.e.
 cam.lockParams()
 cam.setFov(90)
 cam.setViewType('cutscene')
 cam.unlockParams()
This will result in the following call sequence:
 cam.setFov(90)
 cam.setViewType('cutscene')
 cam.applyFov()
 cam.applyViewType()
NOTE: Currently the order of the apply calls following an unlock is not
guaranteed.
EXAMPLE CLASSES
===============
Here is an example of a class that uses ParamSet/ParamObj to manage its
parameters:
class Camera(ParamObj):
    class ParamSet(ParamObj.ParamSet):
        Params = {
            'viewType': 'normal',
            'fov': 60,
            }
    ...
    def getViewType(self):
        return self.viewType
    def setViewType(self, viewType):
        self.viewType = viewType
    def applyViewType(self):
        if self.viewType == 'normal':
            ...
    def getFov(self):
        return self.fov
    def setFov(self, fov):
        self.fov = fov
    def applyFov(self):
        base.camera.setFov(self.fov)
    ...
EXAMPLE USAGE
=============
cam = Camera()
...
savedSettings = cam.ParamSet(cam)
cam.setViewType('closeup')
cam.setFov(90)
...
savedSettings.applyTo(cam)
del savedSettings
"""


class ParamObj:
    class ParamSet:
        Params = {}

        def __init__(self, *args, **kwArgs):
            self.__class__._compileDefaultParams()
            if len(args) == 1 and len(kwArgs) == 0:
                obj = args[0]
                self.paramVals = {}
                for param in self.getParams():
                    self.paramVals[param] = getSetter(obj, param, "get")()
            else:
                assert len(args) == 0
                self.paramVals = dict(kwArgs)

        def getValue(self, param):
            if param in self.paramVals:
                return self.paramVals[param]
            return self._Params[param]

        def applyTo(self, obj):
            obj.lockParams()
            for param in self.getParams():
                getSetter(obj, param)(self.getValue(param))
            obj.unlockParams()

        def extractFrom(self, obj):
            obj.lockParams()
            for param in self.getParams():
                self.paramVals[param] = getSetter(obj, param, "get")()
            obj.unlockParams()

        @classmethod
        def getParams(cls):
            cls._compileDefaultParams()
            return list(cls._Params.keys())

        @classmethod
        def getDefaultValue(cls, param):
            cls._compileDefaultParams()
            dv = cls._Params[param]
            if callable(dv):
                dv = dv()
            return dv

        @classmethod
        def _compileDefaultParams(cls):
            if "_Params" in cls.__dict__:
                return
            bases = list(cls.__bases__)
            if object in bases:
                bases.remove(object)
            mostDerivedLast(bases)
            cls._Params = {}
            for c in [*bases, cls]:
                c._compileDefaultParams()
                if "Params" in c.__dict__:
                    cls._Params.update(c.Params)
            del bases

        def __repr__(self):
            argStr = ""
            for param in self.getParams():
                argStr += f"{param}={repr(self.getValue(param))},"
            return f"{self.__class__.__module__}.{self.__class__.__name__}({argStr})"

    def __init__(self, *args, **kwArgs):
        assert issubclass(self.ParamSet, ParamObj.ParamSet)
        params = None
        if len(args) == 1 and len(kwArgs) == 0:
            params = args[0]
        elif len(kwArgs) > 0:
            assert len(args) == 0
            params = self.ParamSet(**kwArgs)

        self._paramLockRefCount = 0
        self._curParamStack = []
        self._priorValuesStack = []

        for param in self.ParamSet.getParams():
            setattr(self, param, self.ParamSet.getDefaultValue(param))

            setterName = getSetterName(param)
            getterName = getSetterName(param, "get")

            if not hasattr(self, setterName):

                def defaultSetter(self, value, param=param):
                    setattr(self, param, value)

                setattr(self, setterName, defaultSetter)
            if not hasattr(self, getterName):

                def defaultGetter(self, param=param, default=self.ParamSet.getDefaultValue(param)):  # noqa
                    return getattr(self, param, default)

                setattr(self, getterName, defaultGetter)

            origSetterName = f"{setterName}_ORIG"
            if not hasattr(self, origSetterName):
                origSetterFunc = getattr(self.__class__, setterName)
                setattr(self.__class__, origSetterName, origSetterFunc)
                """
                if setterName in self.__dict__:
                    self.__dict__[setterName + '_MOVED'] = self.__dict__[setterName]
                    setterFunc = self.__dict__[setterName]
                    """
                """
                setattr(self, setterName, types.MethodType(
                    Functor(setterStub, param, setterFunc), self, self.__class__))
                    """

                def setterStub(self, value, param=param, origSetterName=origSetterName):
                    if self._paramLockRefCount > 0:
                        priorValues = self._priorValuesStack[-1]
                        if param not in priorValues:
                            try:
                                priorValue = getSetter(self, param, "get")()
                            except BaseException:
                                priorValue = None
                            priorValues[param] = priorValue
                        self._paramsSet[param] = None
                        getattr(self, origSetterName)(value)
                    else:
                        try:
                            priorValue = getSetter(self, param, "get")()
                        except BaseException:
                            priorValue = None
                        self._priorValuesStack.append(
                            {
                                param: priorValue,
                            }
                        )
                        getattr(self, origSetterName)(value)
                        applier = getattr(self, getSetterName(param, "apply"), None)
                        if applier is not None:
                            self._curParamStack.append(param)
                            applier()
                            self._curParamStack.pop()
                        self._priorValuesStack.pop()
                        if hasattr(self, "handleParamChange"):
                            self.handleParamChange((param,))

                setattr(self.__class__, setterName, setterStub)

        if params is not None:
            params.applyTo(self)

    def destroy(self):
        """
        for param in self.ParamSet.getParams():
            setterName = getSetterName(param)
            self.__dict__[setterName].destroy()
            del self.__dict__[setterName]
        """

    def setDefaultParams(self):
        self.ParamSet().applyTo(self)

    def getCurrentParams(self):
        params = self.ParamSet()
        params.extractFrom(self)
        return params

    def lockParams(self):
        self._paramLockRefCount += 1
        if self._paramLockRefCount == 1:
            self._handleLockParams()

    def unlockParams(self):
        if self._paramLockRefCount > 0:
            self._paramLockRefCount -= 1
            if self._paramLockRefCount == 0:
                self._handleUnlockParams()

    def _handleLockParams(self):
        self._paramsSet = {}
        self._priorValuesStack.append({})

    def _handleUnlockParams(self):
        for param in self._paramsSet:
            applier = getattr(self, getSetterName(param, "apply"), None)
            if applier is not None:
                self._curParamStack.append(param)
                applier()
                self._curParamStack.pop()
        self._priorValuesStack.pop()
        if hasattr(self, "handleParamChange"):
            self.handleParamChange(tuple(self._paramsSet.keys()))
        del self._paramsSet

    def paramsLocked(self):
        return self._paramLockRefCount > 0

    def getPriorValue(self):
        return self._priorValuesStack[-1][self._curParamStack[-1]]

    def __repr__(self):
        argStr = ""
        for param in self.ParamSet.getParams():
            try:
                value = getSetter(self, param, "get")()
            except BaseException:
                value = "<unknown>"
            argStr += f"{param}={repr(value)},"
        return f"{self.__class__.__name__}({argStr})"


def configureLogs(baseDir, keepStdout=True):
    ltime = time.localtime()
    logSuffix = "%02d%02d%02d_%02d%02d%02d" % (ltime[0] - 2000, ltime[1], ltime[2], ltime[3], ltime[4], ltime[5])
    logfile = f"tt-{logSuffix}.log"

    class LogAndOutput:
        def __init__(self, orig, logHandler):
            self.orig = orig
            self.log = logHandler

        def write(self, item):
            self.log.write(item)
            self.log.flush()
            if keepStdout:
                self.orig.write(item)
                self.orig.flush()

        def flush(self):
            self.log.flush()
            if keepStdout:
                self.orig.flush()

    dirPath = pathlib.Path(baseDir, "logs")
    dirPath.mkdir(parents=True, exist_ok=True)
    # we want this file to be open permanently so we don't make a context manager
    log = open(dirPath / logfile, "a")  # noqa
    logOut = LogAndOutput(sys.__stdout__, log)
    logErr = LogAndOutput(sys.__stderr__, log)
    sys.stdout = logOut
    sys.stderr = logErr
