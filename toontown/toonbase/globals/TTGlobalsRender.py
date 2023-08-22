from panda3d.core import BitMask32, ColorBlendAttrib, ColorWriteAttrib

MainCameraBitmask = BitMask32.bit(0)
ReflectionCameraBitmask = BitMask32.bit(1)
ShadowCameraBitmask = BitMask32.bit(2)
SkyReflectionCameraBitmask = BitMask32.bit(3)
GlowCameraBitmask = BitMask32.bit(4)
EnviroCameraBitmask = BitMask32.bit(5)

WallBitmask = BitMask32(0x01)
FloorBitmask = BitMask32(0x02)
CameraBitmask = BitMask32(0x04)
CameraTransparentBitmask = BitMask32(0x08)
GhostBitmask = BitMask32(0x800)
PieBitmask = BitMask32(0x100)
CashbotBossObjectBitmask = BitMask32(0x10)


def setCameraBitmask(default, node_path, camera_bitmask, tag=None, tag_function=None, context=None):
    if node_path:
        show = default
        if tag_function:
            show = tag_function(default, tag, context)
        if show:
            node_path.show(camera_bitmask)
        else:
            node_path.hide(camera_bitmask)


def renderReflection(default, node_path, tag=None, tag_function=None, context=None):
    setCameraBitmask(default, node_path, ReflectionCameraBitmask, tag, tag_function, context)


def renderShadow(default, node_path, tag=None, tag_function=None, context=None):
    setCameraBitmask(default, node_path, ShadowCameraBitmask, tag, tag_function, context)


def renderSkyReflection(default, node_path, tag=None, tag_function=None, context=None):
    setCameraBitmask(default, node_path, SkyReflectionCameraBitmask, tag, tag_function, context)


def renderGlow(default, node_path, tag=None, tag_function=None, context=None):
    setCameraBitmask(default, node_path, GlowCameraBitmask, tag, tag_function, context)


def setAdditiveEffect(node_path, tag=None, bin_name=None, lighting_on=False, reflect=False):
    if node_path:
        node_path.setTransparency(True)
        node_path.setDepthWrite(False)
        node_path.node().setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))

        if not lighting_on:
            node_path.setLightOff()

        node_path.setAttrib(
            ColorWriteAttrib.make(ColorWriteAttrib.CRed | ColorWriteAttrib.CGreen | ColorWriteAttrib.CBlue)
        )

        if not reflect:
            renderReflection(False, node_path, tag, None)

        if bin_name:
            node_path.setBin(bin_name, 0)


OriginalCameraFov = 70.0
DefaultCameraFov = 70.0
BossBattleCameraFov = 72.0
FloorOffset = 0.025
CogHQCameraFov = 60.0

CogHQCameraFar = 900.0
CogHQCameraNear = 1.0
CashbotHQCameraFar = 2000.0
CashbotHQCameraNear = 1.0
DefaultCameraFar = 800.0
DefaultCameraNear = 1.0
