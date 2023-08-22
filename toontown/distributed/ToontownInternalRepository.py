from otp.distributed.OTPInternalRepository import OTPInternalRepository
from toontown.toonbase.globals.TTGlobalsCore import OTP_DO_ID_TOONTOWN


class ToontownInternalRepository(OTPInternalRepository):
    notify = directNotify.newCategory("ToontownInternalRepository")
    susnotify = directNotify.newCategory("Suspicious")
    GameGlobalsId = OTP_DO_ID_TOONTOWN
    dbId = 4003

    def __init__(
        self, baseChannel, serverId=None, dcFileNames=None, dcSuffix="AI", connectMethod=None, threadedNet=None
    ):
        OTPInternalRepository.__init__(self, baseChannel, serverId, dcFileNames, dcSuffix, connectMethod, threadedNet)

    def isValidPlayerLocation(self, parentId, zoneId):
        if zoneId < 100 and zoneId != 1:
            return False

        return True

    def writeServerEvent(self, logtype, *args, **kwargs):
        super().writeServerEvent(logtype, *args, **kwargs)
        if logtype == "suspicious":
            self.susnotify.warning(f"avId={args[0]} triggered a suspicious event: {args[1]}")
