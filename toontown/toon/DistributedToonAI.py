from direct.distributed import DistributedSmoothNodeAI
from direct.distributed.ClockDelta import *

from otp.ai.AIBaseGlobal import *
from otp.avatar import DistributedPlayerAI
from toontown.chat import ResistanceChat
from . import ToonDNA
from ..toonbase.globals.TTGlobalsWorld import ValidStartingLocations


class DistributedToonAI(DistributedPlayerAI.DistributedPlayerAI, DistributedSmoothNodeAI.DistributedSmoothNodeAI):
    notify = directNotify.newCategory("DistributedToonAI")

    def __init__(self, air):
        DistributedPlayerAI.DistributedPlayerAI.__init__(self, air)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.__init__(self, air)
        self.dna = ToonDNA.ToonDNA()

    def generate(self):
        DistributedPlayerAI.DistributedPlayerAI.generate(self)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.generate(self)

    def announceGenerate(self):
        DistributedPlayerAI.DistributedPlayerAI.announceGenerate(self)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.announceGenerate(self)
        if self.isPlayerControlled():
            messenger.send("avatarEntered", [self])

    def delete(self):
        self.notify.debug("----Deleting DistributedToonAI %d " % self.doId)
        if self.isPlayerControlled():
            messenger.send("avatarExited", [self])
        del self.dna
        self._sendExitServerEvent()
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)
        DistributedPlayerAI.DistributedPlayerAI.delete(self)
        return

    def b_setHat(self, idx, textureIdx):
        self.d_setHat(idx, textureIdx)
        self.setHat(idx, textureIdx)

    def d_setHat(self, idx, textureIdx):
        self.sendUpdate("setHat", [idx, textureIdx])

    def setHat(self, idx, textureIdx):
        self.hat = (idx, textureIdx)

    def getHat(self):
        return self.hat

    def b_setGlasses(self, idx, textureIdx):
        self.d_setGlasses(idx, textureIdx)
        self.setGlasses(idx, textureIdx)

    def d_setGlasses(self, idx, textureIdx):
        self.sendUpdate("setGlasses", [idx, textureIdx])

    def setGlasses(self, idx, textureIdx):
        self.glasses = (idx, textureIdx)

    def getGlasses(self):
        return self.glasses

    def b_setBackpack(self, idx, textureIdx):
        self.d_setBackpack(idx, textureIdx)
        self.setBackpack(idx, textureIdx)

    def d_setBackpack(self, idx, textureIdx):
        self.sendUpdate("setBackpack", [idx, textureIdx])

    def setBackpack(self, idx, textureIdx):
        self.backpack = (idx, textureIdx)

    def getBackpack(self):
        return self.backpack

    def b_setShoes(self, idx, textureIdx):
        self.d_setShoes(idx, textureIdx)
        self.setShoes(idx, textureIdx)

    def d_setShoes(self, idx, textureIdx):
        self.sendUpdate("setShoes", [idx, textureIdx])

    def setShoes(self, idx, textureIdx):
        self.shoes = (idx, textureIdx)

    def getShoes(self):
        return self.shoes

    def b_setDNAString(self, string):
        self.d_setDNAString(string)
        self.setDNAString(string)

    def d_setDNAString(self, string):
        self.sendUpdate("setDNAString", [string])

    def setDNAString(self, string):
        self.dna.makeFromNetString(string)

    def getDNAString(self):
        return self.dna.makeNetString()

    def getStyle(self):
        return self.dna

    def setDefaultZone(self, zone):
        self.defaultZone = zone
        self.notify.debug("setting default zone to %s" % zone)

    def getDefaultZone(self):
        return self.defaultZone

    def b_setDefaultZone(self, zoneId):
        self.setDefaultZone(zoneId)
        self.sendUpdate("setDefaultZone", [zoneId])

    def setLocation(self, parentId, zoneId, teleport=0):
        success = DistributedPlayerAI.DistributedPlayerAI.setLocation(self, parentId, zoneId, teleport)
        if not success:
            return

        print("go to zone id:", zoneId)
        zoneId %= 100
        if zoneId in ValidStartingLocations:
            self.b_setDefaultZone(zoneId)
            return

        zoneId %= 1000
        if zoneId in ValidStartingLocations:
            self.b_setDefaultZone(zoneId)
            return

    def takeDamage(self, hpLost, quietly=0, sendTotal=1):
        if not self.immortalMode:
            if not quietly:
                self.sendUpdate("takeDamage", [hpLost])
            if hpLost > 0 and self.hp > 0:
                self.hp -= hpLost
                if self.hp <= 0:
                    self.hp = -1
                    messenger.send(self.getGoneSadMessage())
        if not self.hpOwnedByBattle:
            self.hp = min(self.hp, self.maxHp)
            if sendTotal:
                self.d_setHp(self.hp)

    @staticmethod
    def getGoneSadMessageForAvId(avId):
        return "goneSad-%s" % avId

    def getGoneSadMessage(self):
        return self.getGoneSadMessageForAvId(self.doId)

    def setHp(self, hp):
        DistributedPlayerAI.DistributedPlayerAI.setHp(self, hp)
        if hp <= 0:
            messenger.send(self.getGoneSadMessage())

    def getLastHood(self):
        return self.lastHood

    def b_setAnimState(self, animName, animMultiplier):
        self.setAnimState(animName, animMultiplier)
        self.d_setAnimState(animName, animMultiplier)

    def d_setAnimState(self, animName, animMultiplier):
        timestamp = globalClockDelta.getRealNetworkTime()
        self.sendUpdate("setAnimState", [animName, animMultiplier, timestamp])
        return None

    def setAnimState(self, animName, animMultiplier, timestamp=0):
        self.animName = animName
        self.animMultiplier = animMultiplier

    def b_setEmoteAccess(self, bits):
        self.setEmoteAccess(bits)
        self.d_setEmoteAccess(bits)

    def d_setEmoteAccess(self, bits):
        self.sendUpdate("setEmoteAccess", [bits])

    def setEmoteAccess(self, bits):
        if len(bits) == 20:
            bits.extend([0, 0, 0, 0, 0])
            self.b_setEmoteAccess(bits)
        else:
            self.emoteAccess = bits

    def getEmoteAccess(self):
        return self.emoteAccess

    def setEmoteAccessId(self, id, bit):
        self.emoteAccess[id] = bit
        self.d_setEmoteAccess(self.emoteAccess)

    def b_setCustomMessages(self, customMessages):
        self.d_setCustomMessages(customMessages)
        self.setCustomMessages(customMessages)

    def d_setCustomMessages(self, customMessages):
        self.sendUpdate("setCustomMessages", [customMessages])

    def setCustomMessages(self, customMessages):
        self.customMessages = customMessages

    def getCustomMessages(self):
        return self.customMessages

    def b_setResistanceMessages(self, resistanceMessages):
        self.d_setResistanceMessages(resistanceMessages)
        self.setResistanceMessages(resistanceMessages)

    def d_setResistanceMessages(self, resistanceMessages):
        self.sendUpdate("setResistanceMessages", [resistanceMessages])

    def setResistanceMessages(self, resistanceMessages):
        self.resistanceMessages = resistanceMessages

    def getResistanceMessages(self):
        return self.resistanceMessages

    def addResistanceMessage(self, textId):
        msgs = self.getResistanceMessages()
        for i in range(len(msgs)):
            if msgs[i][0] == textId:
                msgs[i][1] += 1
                self.b_setResistanceMessages(msgs)
                return

        msgs.append([textId, 1])
        self.b_setResistanceMessages(msgs)

    def removeResistanceMessage(self, textId):
        msgs = self.getResistanceMessages()
        for i in range(len(msgs)):
            if msgs[i][0] == textId:
                msgs[i][1] -= 1
                if msgs[i][1] <= 0:
                    del msgs[i]
                self.b_setResistanceMessages(msgs)
                return 1

        self.notify.warning("Toon %s doesn't have resistance message %s" % (self.doId, textId))
        return 0

    def restockAllResistanceMessages(self, charges=1):
        from toontown.chat import ResistanceChat

        msgs = []
        for menuIndex in ResistanceChat.resistanceMenu:
            for itemIndex in ResistanceChat.getItems(menuIndex):
                textId = ResistanceChat.encodeId(menuIndex, itemIndex)
                msgs.append([textId, charges])

        self.b_setResistanceMessages(msgs)

    def b_setGhostMode(self, flag):
        self.setGhostMode(flag)
        self.d_setGhostMode(flag)

    def d_setGhostMode(self, flag):
        self.sendUpdate("setGhostMode", [flag])

    def setGhostMode(self, flag):
        self.ghostMode = flag

    def setImmortalMode(self, flag):
        self.immortalMode = flag

    def toonUp(self, hpGained, quietly=0, sendTotal=1):
        if hpGained > self.maxHp:
            hpGained = self.maxHp
        if not quietly:
            self.sendUpdate("toonUp", [hpGained])
        if self.hp + hpGained <= 0:
            self.hp += hpGained
        else:
            self.hp = max(self.hp, 0) + hpGained
        clampedHp = min(self.hp, self.maxHp)
        if not self.hpOwnedByBattle:
            self.hp = clampedHp
        if sendTotal and not self.hpOwnedByBattle:
            self.d_setHp(clampedHp)

    def isToonedUp(self):
        return self.hp >= self.maxHp

    def incrementPopulation(self):
        if self.isPlayerControlled():
            DistributedPlayerAI.DistributedPlayerAI.incrementPopulation(self)

    def decrementPopulation(self):
        if self.isPlayerControlled():
            DistributedPlayerAI.DistributedPlayerAI.decrementPopulation(self)

    def reqSCResistance(self, msgIndex, nearbyPlayers):
        self.d_setSCResistance(msgIndex, nearbyPlayers)

    def d_setSCResistance(self, msgIndex, nearbyPlayers):
        if not ResistanceChat.validateId(msgIndex):
            self.air.writeServerEvent("suspicious", self.doId, "said resistance %s, which is invalid." % msgIndex)
            return
        if not self.removeResistanceMessage(msgIndex):
            self.air.writeServerEvent("suspicious", self.doId, "said resistance %s, but does not have it." % msgIndex)
            return
        if hasattr(self, "autoResistanceRestock") and self.autoResistanceRestock:
            self.restockAllResistanceMessages(1)
        affectedPlayers = []
        for toonId in nearbyPlayers:
            toon = self.air.doId2do.get(toonId)
            if not toon:
                self.notify.warning("%s said resistance %s for %s; not on server" % (self.doId, msgIndex, toonId))
            elif toon.__class__ != DistributedToonAI:
                self.air.writeServerEvent(
                    "suspicious",
                    self.doId,
                    "said resistance %s for %s; object of type %s" % (msgIndex, toonId, toon.__class__.__name__),
                )
            elif toonId in affectedPlayers:
                self.air.writeServerEvent(
                    "suspicious", self.doId, "said resistance %s for %s twice in same message." % (msgIndex, toonId)
                )
            else:
                toon.doResistanceEffect(msgIndex)
                affectedPlayers.append(toonId)

        if len(affectedPlayers) > 50:
            self.air.writeServerEvent(
                "suspicious", self.doId, "said resistance %s for %s toons." % (msgIndex, len(affectedPlayers))
            )
            self.notify.warning(
                "%s said resistance %s for %s toons: %s" % (self.doId, msgIndex, len(affectedPlayers), affectedPlayers)
            )
        self.sendUpdate("setSCResistance", [msgIndex, affectedPlayers])
        type = ResistanceChat.getMenuName(msgIndex)
        value = ResistanceChat.getItemValue(msgIndex)
        self.air.writeServerEvent(
            "resistanceChat", self.zoneId, "%s|%s|%s|%s" % (self.doId, type, value, affectedPlayers)
        )

    def doResistanceEffect(self, msgIndex):
        msgType, itemIndex = ResistanceChat.decodeId(msgIndex)
        msgValue = ResistanceChat.getItemValue(msgIndex)
        if msgType == ResistanceChat.RESISTANCE_TOONUP:
            if msgValue == -1:
                self.toonUp(self.maxHp)
            else:
                self.toonUp(msgValue)
            self.notify.debug("Toon-up for " + self.name)
        elif msgType == ResistanceChat.RESISTANCE_RESTOCK:
            self.notify.debug("Restock for " + self.name)
        elif msgType == ResistanceChat.RESISTANCE_MONEY:
            if msgValue == -1:
                self.addMoney(999999)
            else:
                self.addMoney(msgValue)
            self.notify.debug("Money for " + self.name)

    def squish(self, damage):
        self.takeDamage(damage)

    def b_setNametagStyle(self, nametagStyle):
        self.d_setNametagStyle(nametagStyle)
        self.setNametagStyle(nametagStyle)

    def d_setNametagStyle(self, nametagStyle):
        self.sendUpdate("setNametagStyle", [nametagStyle])

    def setNametagStyle(self, nametagStyle):
        self.nametagStyle = nametagStyle

    def getNametagStyle(self):
        return self.nametagStyle
