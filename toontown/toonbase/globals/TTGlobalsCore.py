from enum import IntEnum, auto


class AccessLevels(IntEnum):
    USER = auto()
    MODERATOR = auto()
    DEVELOPER = auto()
    ADMIN = auto()


# Astron parents
SPHidden = 1
SPRender = 2
# task priority of standard per-zone collision pass on the AI
AICollisionPriority = 10

# Reasons for the client to disconnect from the server and/or AI.
DisconnectUnknown = 0  # e.g. connection lost, client machine rebooted
DisconnectBookExit = 1
DisconnectCloseWindow = 2
DisconnectPythonError = 3
DisconnectSwitchShards = 4
DisconnectGraphicsError = 5

DisconnectReasons = {
    DisconnectUnknown: "unknown",
    DisconnectBookExit: "book exit",
    DisconnectCloseWindow: "closed window",
    DisconnectPythonError: "python error",
    DisconnectSwitchShards: "switch shards",
    DisconnectGraphicsError: "graphics error",
}

ThinkPosHotkey = "shift-f1"
SynchronizeHotkey = "shift-f6"
OTP_DO_ID_TOONTOWN = 4618
OTP_DO_ID_ASTRON_LOGIN_MANAGER = 4670
OTP_DO_ID_CHAT_ROUTER = 4681
OTP_DO_ID_TT_FRIENDS_MANAGER = 4699
OTP_ZONE_ID_QUIET_ZONE = 1
OTP_ZONE_ID_MANAGEMENT = 2
OTP_ZONE_ID_DISTRICTS = 3
OTP_ZONE_ID_DISTRICTS_STATS = 4
OTP_ZONE_ID_SOCKET = 5
