from direct.interval.MetaInterval import Sequence

PULSE_GUI_DURATION = 0.2
PULSE_GUI_CHANGE = 0.333


def cleanup(name):
    taskMgr.remove(name)


def start(ival):
    cleanup(ival.getName())
    ival.start()
    return ival


def loop(ival):
    cleanup(ival.getName())
    ival.loop()
    return ival


def getPulseLargerIval(np, name, duration=PULSE_GUI_DURATION, scale=1):
    return getPulseIval(np, name, 1 + PULSE_GUI_CHANGE, duration=duration, scale=scale)


def getPulseSmallerIval(np, name, duration=PULSE_GUI_DURATION, scale=1):
    return getPulseIval(np, name, 1 - PULSE_GUI_CHANGE, duration=duration, scale=scale)


def getPulseIval(np, name, change, duration=PULSE_GUI_CHANGE, scale=1):
    return Sequence(
        np.scaleInterval(duration, scale * change, blendType="easeOut"),
        np.scaleInterval(duration, scale, blendType="easeIn"),
        name=name,
        autoFinish=1,
    )
