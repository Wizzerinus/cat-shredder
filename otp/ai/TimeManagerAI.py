from direct.distributed import DistributedObjectAI
from direct.distributed.ClockDelta import globalClockDelta
from panda3d.core import HashVal

from toontown.toonbase.globals.TTGlobalsCore import DisconnectReasons


class TimeManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = directNotify.newCategory("TimeManagerAI")

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

    def requestServerTime(self, context):
        """requestServerTime(self, int8 context)

        This message is sent from the client to the AI to initiate a
        synchronization phase.  The AI should immediately report back
        with its current time.  The client will then measure the round
        trip.
        """
        timestamp = globalClockDelta.getRealNetworkTime(bits=32)
        requesterId = self.air.getAvatarIdFromSender()
        self.sendUpdateToAvatarId(requesterId, "serverTime", [context, timestamp])

    def setDisconnectReason(self, disconnectCode):
        """setDisconnectReason(self, uint8 disconnectCode)

        This method is called by the client just before it leaves a
        shard to alert the AI as to the reason it's going.  If the AI
        doesn't get this message, it can assume the client aborted
        messily or its internet connection was dropped.
        """
        requesterId = self.air.getAvatarIdFromSender()
        self.notify.info(
            f"Client {requesterId} leaving for reason {disconnectCode} "
            f"({DisconnectReasons.get(disconnectCode, 'invalid reason')})."
        )

        if disconnectCode in DisconnectReasons:
            self.air.setAvatarDisconnectReason(requesterId, disconnectCode)
        else:
            self.air.writeServerEvent("suspicious", requesterId, f"invalid disconnect reason: {disconnectCode}")

    def setSignature(self, signatureHash):
        """
        This method is called by the client at startup time, to send
        the xrc signature and the prc hash to the AI for logging in
        case the client does anything suspicious.
        """
        requesterId = self.air.getAvatarIdFromSender()
        prcHash = HashVal()
        prcHash.setFromBin(signatureHash)
        info = prcHash.asHex()
        self.notify.info(f"Client {requesterId} signature: {info}")
        self.air.writeServerEvent("client-signature", requesterId, info)
