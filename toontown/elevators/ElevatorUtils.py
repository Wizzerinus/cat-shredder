from direct.interval.IntervalGlobal import *

from .ElevatorConstants import *


def getLeftClosePoint(elType):
    width = ElevatorData[elType]["width"]
    return Point3(width, 0, 0)


def getRightClosePoint(elType):
    width = ElevatorData[elType]["width"]
    return Point3(-width, 0, 0)


def getLeftOpenPoint(elType):
    return Point3(0, 0, 0)


def getRightOpenPoint(elType):
    return Point3(0, 0, 0)


def closeDoors(leftDoor, rightDoor, elType=ELEVATOR_NORMAL):
    closedPosLeft = getLeftClosePoint(elType)
    closedPosRight = getRightClosePoint(elType)

    leftDoor.setPos(closedPosLeft)
    rightDoor.setPos(closedPosRight)


def openDoors(leftDoor, rightDoor, elType=ELEVATOR_NORMAL):
    openPosLeft = getLeftOpenPoint(elType)
    openPosRight = getRightOpenPoint(elType)

    leftDoor.setPos(openPosLeft)
    rightDoor.setPos(openPosRight)


def getLeftOpenInterval(distObj, leftDoor, elType):
    openTime = ElevatorData[elType]["openTime"]
    closedPos = getLeftClosePoint(elType)
    openPos = getLeftOpenPoint(elType)
    return LerpPosInterval(
        leftDoor,
        openTime,
        openPos,
        startPos=closedPos,
        blendType="easeOut",
        name=distObj.uniqueName("leftDoorOpen"),
    )


def getRightOpenInterval(distObj, rightDoor, elType):
    openTime = ElevatorData[elType]["openTime"]
    closedPos = getRightClosePoint(elType)
    openPos = getRightOpenPoint(elType)
    return LerpPosInterval(
        rightDoor,
        openTime,
        openPos,
        startPos=closedPos,
        blendType="easeOut",
        name=distObj.uniqueName("rightDoorOpen"),
    )


def getOpenInterval(distObj, leftDoor, rightDoor, openSfx, finalOpenSfx, elType=ELEVATOR_NORMAL):
    left = getLeftOpenInterval(distObj, leftDoor, elType)
    right = getRightOpenInterval(distObj, rightDoor, elType)
    openDuration = left.getDuration()
    sfxVolume = ElevatorData[elType]["sfxVolume"]
    if finalOpenSfx:
        sound = Sequence(
            SoundInterval(openSfx, duration=openDuration, volume=sfxVolume, node=leftDoor),
            SoundInterval(finalOpenSfx, volume=sfxVolume, node=leftDoor),
        )
    else:
        sound = SoundInterval(openSfx, volume=sfxVolume, node=leftDoor)
    return Parallel(
        sound,
        left,
        right,
    )


def getLeftCloseInterval(distObj, leftDoor, elType):
    closeTime = ElevatorData[elType]["closeTime"]
    closedPos = getLeftClosePoint(elType)
    openPos = getLeftOpenPoint(elType)
    return LerpPosInterval(
        leftDoor,
        closeTime,
        closedPos,
        startPos=openPos,
        blendType="easeOut",
        name=distObj.uniqueName("leftDoorClose"),
    )


def getRightCloseInterval(distObj, rightDoor, elType):
    closeTime = ElevatorData[elType]["closeTime"]
    closedPos = getRightClosePoint(elType)
    openPos = getRightOpenPoint(elType)
    return LerpPosInterval(
        rightDoor,
        closeTime,
        closedPos,
        startPos=openPos,
        blendType="easeOut",
        name=distObj.uniqueName("rightDoorClose"),
    )


def getCloseInterval(distObj, leftDoor, rightDoor, closeSfx, finalCloseSfx, elType=ELEVATOR_NORMAL):
    left = getLeftCloseInterval(distObj, leftDoor, elType)
    right = getRightCloseInterval(distObj, rightDoor, elType)
    closeDuration = left.getDuration()
    sfxVolume = ElevatorData[elType]["sfxVolume"]
    if finalCloseSfx:
        sound = Sequence(
            SoundInterval(closeSfx, duration=closeDuration, volume=sfxVolume, node=leftDoor),
            SoundInterval(finalCloseSfx, volume=sfxVolume, node=leftDoor),
        )
    else:
        sound = SoundInterval(closeSfx, volume=sfxVolume, node=leftDoor)
    return Parallel(
        sound,
        left,
        right,
    )


def getRideElevatorInterval(elType=ELEVATOR_NORMAL):
    if elType in (ELEVATOR_VP, ELEVATOR_CJ):
        yValue = 30
        zMin = 7.8
        zMid = 8
        zMax = 8.2
    elif elType == ELEVATOR_BB:
        yValue = 21
        zMin = 7
        zMid = 7.2
        zMax = 7.4

    elif elType == ELEVATOR_CFO:
        yValue = 30
        zMin = 7.8
        zMid = 8
        zMax = 8.2
    else:
        return Sequence(
            Wait(0.5),
            LerpPosInterval(camera, 0.5, Point3(0, 14, 3.8), startPos=Point3(0, 14, 4), blendType="easeOut"),
            LerpPosInterval(camera, 0.5, Point3(0, 14, 4), startPos=Point3(0, 14, 3.8)),
            Wait(1.0),
            LerpPosInterval(camera, 0.5, Point3(0, 14, 4.2), startPos=Point3(0, 14, 4), blendType="easeOut"),
            LerpPosInterval(camera, 1.0, Point3(0, 14, 4), startPos=Point3(0, 14, 4.2)),
        )

    return Sequence(
        Wait(0.5),
        LerpPosInterval(camera, 0.5, Point3(0, yValue, zMin), startPos=Point3(0, yValue, zMid), blendType="easeOut"),
        LerpPosInterval(camera, 0.5, Point3(0, yValue, zMid), startPos=Point3(0, yValue, zMin)),
        Wait(1.0),
        LerpPosInterval(camera, 0.5, Point3(0, yValue, zMax), startPos=Point3(0, yValue, zMid), blendType="easeOut"),
        LerpPosInterval(camera, 1.0, Point3(0, yValue, zMid), startPos=Point3(0, yValue, zMax)),
    )
