from enum import IntEnum, auto

from panda3d.core import Vec4

AvatarDefaultRadius = 1


class AvatarTypes(IntEnum):
    COG = auto()
    TOON = auto()
    GOON = auto()
    BOSS = auto()
    PET = auto()


ShadowScales = {
    AvatarTypes.COG: 0.375,
    AvatarTypes.TOON: 0.5,
    AvatarTypes.GOON: 0.375,
    AvatarTypes.PET: 0.375,
    AvatarTypes.BOSS: 0.5,
}


GoonModelDict = {
    "n": (
        "phase_9/models/char/Cog_Goonie",
        (
            ("walk", "-walk"),
            ("collapse", "-collapse"),
            ("recovery", "-recovery"),
        ),
    ),
    "p": (
        "phase_9/models/char/Cog_Goonie",
        (
            ("walk", "-walk"),
            ("collapse", "-collapse"),
            ("recovery", "-recovery"),
        ),
    ),
}

GoonHatColors = {
    "n": (
        (0, None),
        (13, Vec4(0.75, 0.35, 0.1, 1)),
        (26, Vec4(0.95, 0, 0, 1)),
    ),
    "p": (
        (0, None),
        (17, Vec4(0.35, 0.0, 0.75, 1)),
        (34, Vec4(0.0, 0.0, 0.95, 1)),
    ),
}

ToonBodyScales = {
    "mouse": 0.60,
    "cat": 0.73,
    "duck": 0.66,
    "rabbit": 0.74,
    "horse": 0.83,
    "dog": 0.8,
    "monkey": 0.68,
    "bear": 0.84,
    "pig": 0.77,
}

ToonLegHeights = {"s": 1.5, "m": 2.0, "l": 2.75}
ToonTorsoHeights = {
    "s": 1.5,
    "m": 1.75,
    "l": 2.25,
    "ss": 1.5,
    "ms": 1.75,
    "ls": 2.25,
    "sd": 1.5,
    "md": 1.75,
    "ld": 2.25,
}
ToonHeadHeights = {
    "dls": 0.75,
    "dss": 0.5,
    "dsl": 0.5,
    "dll": 0.75,
    "cls": 0.75,
    "css": 0.5,
    "csl": 0.5,
    "cll": 0.75,
    "hls": 0.75,
    "hss": 0.5,
    "hsl": 0.5,
    "hll": 0.75,
    "mls": 0.75,
    "mss": 0.5,
    "rls": 0.75,
    "rss": 0.5,
    "rsl": 0.5,
    "rll": 0.75,
    "fls": 0.75,
    "fss": 0.5,
    "fsl": 0.5,
    "fll": 0.75,
    "pls": 0.75,
    "pss": 0.5,
    "psl": 0.5,
    "pll": 0.75,
    "bls": 0.75,
    "bss": 0.5,
    "bsl": 0.5,
    "bll": 0.75,
    "sls": 0.75,
    "sss": 0.5,
    "ssl": 0.5,
    "sll": 0.75,
}
