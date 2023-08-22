import traceback

from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.MsgTypes import MsgName2Id
from direct.distributed.PyDatagram import PyDatagram


class OTPInternalRepository(AstronInternalRepository):
    notify = directNotify.newCategory("OTPInternalRepository")
    dbId = 4003
    context = InitialContext = 0

    def __init__(self, baseChannel, serverId, dcFileNames, dcSuffix, connectMethod, threadedNet):
        AstronInternalRepository.__init__(
            self,
            baseChannel,
            serverId=serverId,
            dcFileNames=dcFileNames,
            dcSuffix=dcSuffix,
            connectMethod=connectMethod,
            threadedNet=threadedNet,
        )

    def handleConnected(self):
        AstronInternalRepository.handleConnected(self)

    def readerPollOnce(self):
        try:
            return AstronInternalRepository.readerPollOnce(self)
        except Exception as e:
            traceback.print_exc()

            if self.getAvatarIdFromSender() > 100000000:
                dg = PyDatagram()
                dg.addServerHeader(self.getMsgSender(), self.ourChannel, MsgName2Id["CLIENTAGENT_EJECT"])
                dg.addUint16(166)
                dg.addString("You were kicked to prevent a district crash.")
                self.send(dg)

            self.notify.warning(f"INTERNAL-EXCEPTION: {repr(e)} ({self.getAvatarIdFromSender()})")

        return 1

    def getAccountIdFromSender(self):
        return (self.getMsgSender() >> 32) & 0xFFFFFFFF

    def getAvatarIdFromSender(self):
        return self.getMsgSender() & 0xFFFFFFFF

    def sendSetZone(self, distObj, zoneId):
        distObj.setLocation(distObj.parentId, zoneId)
        self.sendSetLocation(distObj, distObj.parentId, zoneId)

    def setAllowClientSend(self, avId, distObj, fieldNameList=None):
        if fieldNameList is None:
            fieldNameList = []
        dg = PyDatagram()
        dg.addServerHeader(
            distObj.GetPuppetConnectionChannel(avId), self.ourChannel, MsgName2Id["CLIENTAGENT_SET_FIELDS_SENDABLE"]
        )
        fieldIds = []
        for fieldName in fieldNameList:
            field = distObj.dclass.getFieldByName(fieldName)
            if field:
                fieldIds.append(field.getNumber())

        dg.addUint32(distObj.getDoId())
        dg.addUint16(len(fieldIds))
        for fieldId in fieldIds:
            dg.addUint16(fieldId)

        self.send(dg)

    def createDgUpdateToDoId(self, dclassName, fieldName, doId, args, channelId=None):
        """
        channelId can be used as a recipient if you want to bypass the normal
        airecv, ownrecv, broadcast, etc.  If you don't include a channelId
        or if channelId == doId, then the normal broadcast options will
        be used.

        This is just like sendUpdateToDoId, but just returns
        the datagram instead of immediately sending it.
        """
        result = None
        dclass = self.dclassesByName.get(dclassName + self.dcSuffix)
        assert dclass is not None
        if channelId is None:
            channelId = doId
        if dclass is not None:
            dg = dclass.aiFormatUpdate(fieldName, doId, channelId, self.ourChannel, args)
            result = dg
        return result

    def getSenderReturnChannel(self):
        return self.getMsgSender()

    def sendUpdateToDoId(self, dclassName, fieldName, doId, args, channelId=None):
        """
        channelId can be used as a recipient if you want to bypass the normal
        airecv, ownrecv, broadcast, etc.  If you don't include a channelId
        or if channelId == doId, then the normal broadcast options will
        be used.

        See Also: def queryObjectField
        """
        dclass = self.dclassesByName.get(dclassName + self.dcSuffix)
        if dclass is not None:
            if channelId is None:
                channelId = doId
            dg = dclass.aiFormatUpdate(fieldName, doId, channelId, self.ourChannel, args)
            self.send(dg)
        else:
            self.notify.warning(f"Unknown DClass: {dclassName}/{self.dcSuffix}")

    def allocateContext(self):
        self.context += 1
        if self.context >= (1 << 32):
            self.context = self.InitialContext
        return self.context
