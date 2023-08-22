from enum import IntEnum, auto

CashbotBossToMagnetTime = 0.2
CashbotBossFromMagnetTime = 1
CashbotBossBattleThreePosHpr = (120, -315, 0, 180, 0, 0)
CashbotBossSafeKnockImpact = 0.5


class TreasureTypes(IntEnum):
    ICE_CREAM = auto()
    STARFISH = auto()
    FLOWER = auto()
    MUSIC_NOTE = auto()
    SNOWFLAKE = auto()
    ZZZS = auto()


TreasureModels = {
    TreasureTypes.ICE_CREAM: "phase_4/models/props/icecream",
    TreasureTypes.STARFISH: "phase_6/models/props/starfish_treasure",
    TreasureTypes.SNOWFLAKE: "phase_8/models/props/snowflake_treasure",
    TreasureTypes.MUSIC_NOTE: "phase_6/models/props/music_treasure",
    TreasureTypes.FLOWER: "phase_8/models/props/flower_treasure",
    TreasureTypes.ZZZS: "phase_8/models/props/zzz_treasure",
}
