from direct.actor.DistributedActor import DistributedActor
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpPosInterval, LerpScaleInterval
from direct.interval.MetaInterval import Parallel, Sequence
from direct.task import Task
from panda3d.core import Point3, TextNode
from panda3d.otp import Nametag

from otp.avatar.Avatar import Avatar
from toontown.toonbase.globals.TTGlobalsCore import SPHidden
from toontown.toonbase.globals.TTGlobalsGUI import getSignFont


class DistributedAvatar(DistributedActor, Avatar):
    HpTextEnabled = 1

    ManagesNametagAmbientLightChanged = True
    DistributedAvatarInitialized = False
    DistributedAvatar_announced = False
    checkDeathAllowed = True

    def __init__(self, cr):
        """
        Handle distributed updates
        """

        if self.DistributedAvatarInitialized:
            return

        self.DistributedAvatarInitialized = True

        Avatar.__init__(self)
        DistributedActor.__init__(self, cr)

        self.hpText = None
        self.hp = 0
        self.maxHp = 0

        self.HpTextGenerator = TextNode("HpTextGenerator")
        self.HpTextGenerator.setFont(getSignFont())
        self.HpTextGenerator.clearShadow()
        self.HpTextGenerator.setAlign(TextNode.ACenter)

        self.hpNumbers = []

    def disable(self):
        try:
            del self.DistributedAvatar_announced
        except AttributeError:
            return
        self.reparentTo(hidden)
        self.removeActive()
        self.disableBodyCollisions()
        self.hideHpText()
        self.hp = 0

        DistributedActor.disable(self)

    def delete(self):
        Avatar.delete(self)
        DistributedActor.delete(self)

    def generate(self):
        DistributedActor.generate(self)
        if not self.isLocal():
            self.addActive()

        self.setParent(SPHidden)

        self.setTag("avatarDoId", str(self.doId))

    def announceGenerate(self):
        if self.DistributedAvatar_announced:
            return

        self.DistributedAvatar_announced = True

        if not self.isLocal():
            self.initializeBodyCollisions(f"distAvatarCollNode-{self.doId}")

        DistributedActor.announceGenerate(self)

    def do_setParent(self, parentToken):
        """do_setParent(self, int parentToken)

        This overrides a function defined in DistributedNode to
        reparent the node somewhere.  A DistributedAvatar wants to
        hide the onscreen nametag when the parent is hidden.
        """
        if not self.isDisabled():
            if parentToken == SPHidden:
                self.nametag2dDist &= ~Nametag.CName
            else:
                self.nametag2dDist |= Nametag.CName
            self.nametag.getNametag2d().setContents(self.nametag2dContents & self.nametag2dDist)
            DistributedActor.do_setParent(self, parentToken)

    def toonUp(self, hpGained):
        if self.hp is None or hpGained < 0:
            return

        oldHp = self.hp

        if self.hp + hpGained <= 0:
            self.hp += hpGained
        else:
            self.hp = min(max(self.hp, 0) + hpGained, self.maxHp)

        hpGained = self.hp - max(oldHp, 0)
        if hpGained > 0:
            self.showHpText(hpGained)
            self.hpChange()

    def takeDamage(self, hpLost, bonus=0):
        if self.hp is None or hpLost < 0:
            return

        oldHp = self.hp
        self.hp = max(self.hp - hpLost, 0)

        hpLost = oldHp - self.hp
        if hpLost > 0:
            self.showHpText(-hpLost, bonus)
            self.hpChange()

            if self.hp <= 0 and oldHp > 0:
                self.died()

    def setHp(self, hitPoints, checkDeath=True):
        self.hp = hitPoints
        self.hpChange()

        if checkDeath and self.checkDeathAllowed:
            justRanOutOfHp = self.hp is not None and self.hp - hitPoints > 0 and hitPoints <= 0
            if justRanOutOfHp:
                self.died()

    def hpChange(self, quietly=0):
        if hasattr(self, "doId"):
            if self.hp is not None and self.maxHp is not None:
                messenger.send(self.uniqueName("hpChange"), [self.hp, self.maxHp, quietly])
            if self.hp is not None and self.hp > 0:
                messenger.send(self.uniqueName("positiveHP"))

    def died(self):
        """
        This is a hook for derived classes to do something when the
        avatar runs out of HP.  The base function doesn't do anything.
        """

    def getHp(self):
        return self.hp

    def setMaxHp(self, hitPoints):
        self.maxHp = hitPoints
        self.hpChange()

    def getMaxHp(self):
        return self.maxHp

    def getName(self):
        return Avatar.getName(self)

    def setName(self, name):
        try:
            self.node().setName(f"{name}-{int(self.doId)}")
            self.gotName = 1
        except (AttributeError, ValueError):
            pass

        return Avatar.setName(self, name)

    def modifyHpFromBattle(self, diff):
        self.setHp(self.getHp() + diff, checkDeath=False)

    def appendHpAndMoveRest(self, item, offset=1.3):
        for i in self.hpNumbers:
            x, y, z = i.getPos()
            i.setPos(x, y, z + offset)
        self.hpNumbers.append(item)
        item.show()

    def removeFirstHp(self):
        self.hpNumbers[0].removeNode()
        self.hpNumbers = self.hpNumbers[1:]

    def generateText(self, text, color):
        self.HpTextGenerator.setText(text)
        self.HpTextGenerator.setTextColor(*color)
        return self.HpTextGenerator.generate()

    def getHpSequence(self, hpChange, color, text, icon=None, hpChanges=True):
        if not self.HpTextEnabled or self.ghostMode:
            return None

        textParent = self.attachNewNode("textParent")
        textParent.setBillboardPointEye()
        textParent.wrtReparentTo(self, 1000)

        textPath = textParent.attachNewNode(self.generateText(text, color))
        if icon:
            iconPath, xPosition = self.addIconSpot(textParent, text)
            icon.reparentTo(iconPath)
        else:
            textPath.setPos(0, 0, self.height * 0.75)
            xPosition = 0

        textParent.hide()
        return Sequence(
            Func(self.modifyHpFromBattle, hpChange) if hpChanges else Wait(0),
            Func(self.appendHpAndMoveRest, textParent),
            Parallel(
                LerpScaleInterval(textPath, 0.4, 1, startScale=0, blendType="easeOut"),
                LerpPosInterval(textPath, 0.6, (xPosition, 0, self.height + 1.5), blendType="easeOut"),
            ),
            Wait(2),
            textPath.colorInterval(0.1, color),
            Func(self.removeFirstHp),
        )

    def addIconSpot(self, textParent, text):
        textPath = textParent.getChild(0)
        iconPath = textPath.attachNewNode("statusIcon")
        if not text:
            iconPath.setPos(0, 0, 0.4)
            textPath.setPos(0, 0, self.height * 0.75)
            return iconPath, 0
        textRight = self.HpTextGenerator.getCardActual()[1]
        iconDistance = textRight + self.HpTextGenerator.calcWidth(text[-1])
        iconPath.setPos(iconDistance, 0, 0.4)
        textPath.setPos(-textRight, 0, self.height * 0.75)
        return iconPath, -textRight

    def getTextParent(self, text, color, icon=True):
        if not self.HpTextEnabled or self.ghostMode:
            return None

        textParent = self.attachNewNode("textParent")

        textParent.setBillboardPointEye()

        textParent.setBin("fixed", 100)

        if text:
            textParent.attachNewNode(self.generateText(text, color))
        else:
            textParent.attachNewNode("empty")

        if icon:
            self.addIconSpot(textParent, text)
        textParent.hide()
        return textParent

    @staticmethod
    def getHpTextColor(number, bonus):
        colors = {
            0: (0.9, 0, 0, 1) if number < 0 else (0, 0.9, 0, 1),
            1: (1, 1, 0, 1),
            2: (1, 0.5, 0, 1),
        }
        return colors[bonus]

    def showHpText(self, number, bonus=0, scale=1):
        if not self.HpTextEnabled or self.ghostMode:
            return

        if number != 0:
            if self.hpText:
                self.hideHpText()
            self.HpTextGenerator.setFont(getSignFont())
            if number < 0:
                self.HpTextGenerator.setText(str(number))
            else:
                self.HpTextGenerator.setText(f"+{number}")
            self.HpTextGenerator.clearShadow()
            self.HpTextGenerator.setAlign(TextNode.ACenter)
            color = self.getHpTextColor(number, bonus)
            self.HpTextGenerator.setTextColor(*color)
            hpTextNode = self.HpTextGenerator.generate()

            self.hpText = self.attachNewNode(hpTextNode)

            self.hpText.setScale(0)
            self.hpText.setBillboardPointEye()
            self.hpText.setDepthTest(0)
            self.hpText.wrtReparentTo(self, 1000)

            self.hpText.setPos(0, 0, self.height // 2)
            seq = Sequence(
                Parallel(
                    self.hpText.scaleInterval(0.4, scale, blendType="easeOut"),
                    self.hpText.posInterval(0.6, (0, 0, self.height + 1.5), blendType="easeOut"),
                ),
                Wait(2),
                self.hpText.colorInterval(0.1, color),
                Func(self.hideHpText),
            )
            seq.start()

    def hideHpTextTask(self, task):
        self.hideHpText()
        return Task.done

    def hideHpText(self):
        if self.hpText:
            taskMgr.remove(self.uniqueName("hpText"))
            self.hpText.removeNode()
            self.hpText = None

    def getStareAtNodeAndOffset(self):
        return self, Point3(0, 0, self.height)

    def getAvIdName(self):
        return f"{self.getName()}\n{self.doId}"

    def askAvOnShard(self, avId):
        if base.cr.doId2do.get(avId):
            messenger.send(f"AvOnShard{avId}", [True])
        else:
            self.sendUpdate("checkAvOnShard", [avId])

    @staticmethod
    def confirmAvOnShard(avId, onShard=True):
        messenger.send(f"AvOnShard{avId}", [onShard])

    def getDialogueArray(self):
        return None
