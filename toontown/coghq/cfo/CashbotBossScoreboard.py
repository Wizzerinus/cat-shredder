import contextlib

from direct.gui.DirectGui import *
from panda3d.core import *

from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *

from toontown.coghq.cfo import CraneLeagueGlobals
from toontown.toon.ToonHead import ToonHead

import random
import math

from toontown.toonbase.globals.TTGlobalsGUI import getCompetitionFont
from toontown.toonbase.globals.TTGlobalsRender import BossBattleCameraFov

POINTS_TEXT_SCALE = 0.09

LABEL_Y_POS = 0.55

# TEXT COLORS
RED = (1, 0, 0, 1)
GREEN = (0, 1, 0, 1)
GOLD = (1, 235.0 / 255.0, 165.0 / 255.0, 1)
WHITE = (0.9, 0.9, 0.9, 0.85)
CYAN = (0, 1, 240.0 / 255.0, 1)


def doGainAnimation(label, amount, old_amount, new_amount, reason="", localAvFlag=False):
    pointText = label.points_text
    reasonFlag = len(reason) > 0  # reason flag is true if there is a reason
    randomRoll = random.randint(1, 20) + 10 if reasonFlag else 5
    textToShow = "+" + str(amount) + " " + reason
    popup = OnscreenText(
        parent=pointText,
        text=textToShow,
        style=3,
        fg=GOLD if reasonFlag else GREEN,
        align=TextNode.ACenter,
        scale=0.05,
        pos=(0.03, 0.03),
        roll=-randomRoll,
        font=getCompetitionFont(),
    )

    def cleanup():
        popup.cleanup()

    def doTextUpdate(n):
        with contextlib.suppress(AttributeError):
            pointText.setText(str(int(math.ceil(n))))

    # points with a reason go towards the right to see easier
    rx = random.random() / 5.0 - 0.1  # -.1-.1
    rz = random.random() / 10.0  # 0-.1
    xOffset = 0.125 + rx if reasonFlag else 0.01 + (rx / 5.0)
    zOffset = 0.02 + rz if reasonFlag else 0.055 + (rz / 5.0)
    reasonTimeAdd = 0.85 if reasonFlag else 0
    popupStartColor = CYAN if reasonFlag else GREEN
    popupFadedColor = (CYAN[0], CYAN[1], CYAN[2], 0) if reasonFlag else (GREEN[0], GREEN[1], GREEN[2], 0)

    targetPos = Point3(pointText.getX() + xOffset, 0, pointText.getZ() + zOffset)
    startPos = Point3(popup.getX(), popup.getY(), popup.getZ())
    label.cancel_inc_ival()

    label.inc_ival = Sequence(
        LerpFunctionInterval(doTextUpdate, fromData=old_amount, toData=new_amount, duration=0.5, blendType="easeOut")
    )
    label.inc_ival.start()

    Sequence(
        Parallel(
            LerpColorScaleInterval(
                popup,
                duration=0.95 + reasonTimeAdd,
                colorScale=popupFadedColor,
                startColorScale=popupStartColor,
                blendType="easeInOut",
            ),
            LerpPosInterval(
                popup, duration=0.95 + reasonTimeAdd, pos=targetPos, startPos=startPos, blendType="easeInOut"
            ),
            Sequence(
                Parallel(
                    LerpScaleInterval(pointText, duration=0.25, scale=1 + 0.2, startScale=1, blendType="easeInOut"),
                    LerpColorScaleInterval(
                        pointText, duration=0.25, colorScale=GREEN, startColorScale=(1, 1, 1, 1), blendType="easeInOut"
                    ),
                ),
                Parallel(
                    LerpScaleInterval(pointText, duration=0.25, startScale=1 + 0.2, scale=1, blendType="easeInOut"),
                    LerpColorScaleInterval(
                        pointText, duration=0.25, startColorScale=GREEN, colorScale=(1, 1, 1, 1), blendType="easeInOut"
                    ),
                ),
            ),
        ),
        Func(cleanup),
    ).start()


def doLossAnimation(label, amount, old_amount, new_amount, reason="", localAvFlag=False):
    pointText = label.points_text
    reasonFlag = len(reason) > 0  # reason flag is true if there is a reason
    randomRoll = random.randint(5, 15) + 15 if reasonFlag else 5

    textToShow = str(amount) + " " + reason
    popup = OnscreenText(
        parent=pointText,
        text=textToShow,
        style=3,
        fg=RED,
        align=TextNode.ACenter,
        scale=0.05,
        pos=(0.03, 0.03),
        roll=-randomRoll,
        font=getCompetitionFont(),
    )

    def cleanup():
        popup.cleanup()

    def doTextUpdate(n):
        with contextlib.suppress(AttributeError):
            pointText.setText(str(int(n)))

    rx = random.random() / 5.0 - 0.1  # -.1-.1
    rz = random.random() / 10.0  # 0-.1
    xOffset = 0.125 + rx if reasonFlag else 0.01 + (rx / 5.0)
    zOffset = 0.02 + rz if reasonFlag else 0.055 + (rz / 5.0)
    targetPos = Point3(pointText.getX() + xOffset, 0, pointText.getZ() + zOffset)
    startPos = Point3(popup.getX(), popup.getY(), popup.getZ())
    label.cancel_inc_ival()

    label.inc_ival = Sequence(
        LerpFunctionInterval(doTextUpdate, fromData=old_amount, toData=new_amount, duration=0.5, blendType="easeOut")
    )
    label.inc_ival.start()
    Sequence(
        Parallel(
            LerpFunc(doTextUpdate, fromData=old_amount, toData=new_amount, duration=0.5, blendType="easeInOut"),
            LerpColorScaleInterval(
                popup, duration=2, colorScale=(1, 0, 0, 0), startColorScale=RED, blendType="easeInOut"
            ),
            LerpPosInterval(popup, duration=2, pos=targetPos, startPos=startPos, blendType="easeInOut"),
            Sequence(
                Parallel(
                    LerpScaleInterval(pointText, duration=0.25, scale=1 - 0.2, startScale=1, blendType="easeInOut"),
                    LerpColorScaleInterval(
                        pointText, duration=0.25, colorScale=RED, startColorScale=(1, 1, 1, 1), blendType="easeInOut"
                    ),
                ),
                Parallel(
                    LerpScaleInterval(pointText, duration=0.25, startScale=1 - 0.2, scale=1, blendType="easeInOut"),
                    LerpColorScaleInterval(
                        pointText, duration=0.25, startColorScale=RED, colorScale=(1, 1, 1, 1), blendType="easeInOut"
                    ),
                ),
            ),
        ),
        Func(cleanup),
    ).start()


def getScoreboardTextRow(scoreboard_frame, unique_id, default_text="", frame_color=(0.5, 0.5, 0.5, 0.75), isToon=False):
    n = TextNode(unique_id)
    n.setText(default_text)
    n.setAlign(TextNode.ALeft)
    n.setFrameColor(frame_color)
    y_margin_addition = 0.4 if isToon else 0
    n.setFrameAsMargin(0.4, 0.4, 0.2 + y_margin_addition, 0.2 + y_margin_addition)
    n.setCardColor(0.2, 0.2, 0.2, 0.75)
    n.setCardAsMargin(0.38, 0.38, 0.19, 0.19)
    n.setCardDecal(True)
    n.setShadow(0.05, 0.05)
    n.setShadowColor(0, 0, 0, 1)
    n.setTextColor(0.7, 0.7, 0.7, 1)
    n.setTextScale(1)
    n.setFont(getCompetitionFont())
    p = scoreboard_frame.attachNewNode(n)
    p.setScale(0.05)
    return n, p  # Modify n for actual text properties, p for scale/pos


class CashbotBossScoreboardToonRow(DirectObject):
    INSTANCES = []

    FIRST_PLACE_HEAD_X = -0.24
    FIRST_PLACE_HEAD_Y = 0.013
    FIRST_PLACE_TEXT_X = 0

    FRAME_X = 0.31
    FRAME_Y_FIRST_PLACE = -0.12

    PLACE_Y_OFFSET = 0.125

    # Called when a button on a row is clicked, instance is the actual instance that clicked this
    @classmethod
    def _clicked(cls, instance, _=None):
        # Loop through all instances
        for ins in cls.INSTANCES:
            # Skip the instance that clicked
            if ins is instance:
                continue

            # Another thing was clicked, force stop spectating if they were
            if ins.isBeingSpectated:
                ins.__stop_spectating()

        # Spec
        instance.__attempt_spectate()

    def __init__(self, scoreboard_frame, avId, place=0, ruleset=None):
        DirectObject.__init__(self)

        self.ruleset = ruleset

        self.INSTANCES.append(self)

        # 0 based index based on what place they are in, y should be adjusted downwards
        self.place = place
        self.avId = avId
        self.points = 0
        self.damage, self.stuns, self.stomps = 0, 0, 0
        self.frame = DirectFrame(parent=scoreboard_frame)
        self.toon_head = self.createToonHead(avId, scale=0.125)
        self.toon_head_button = DirectButton(
            parent=self.frame,
            pos=(self.FIRST_PLACE_HEAD_X, 0, self.FIRST_PLACE_HEAD_Y + 0.015),
            scale=0.5,
            command=CashbotBossScoreboardToonRow._clicked,
            extraArgs=[self],
        )
        self.toon_head_button.setTransparency(TransparencyAttrib.MAlpha)
        self.toon_head_button.setColorScale(1, 1, 1, 0)
        self.frame.setX(self.FRAME_X)
        self.frame.setZ(self.getYFromPlaceOffset(self.FRAME_Y_FIRST_PLACE))
        self.toon_head.reparentTo(self.frame)
        self.toon_head.setPos(self.FIRST_PLACE_HEAD_X, 0, self.FIRST_PLACE_HEAD_Y)
        self.toon_head.setH(180)
        self.toon_head.startBlink()
        self.points_text = OnscreenText(
            parent=self.frame,
            text=str(self.points),
            style=3,
            fg=WHITE,
            align=TextNode.ABoxedCenter,
            scale=0.09,
            pos=(self.FIRST_PLACE_TEXT_X, 0),
            font=getCompetitionFont(),
        )
        self.combo_text = OnscreenText(
            parent=self.frame,
            text="x" + "0",
            style=3,
            fg=CYAN,
            align=TextNode.ACenter,
            scale=0.055,
            pos=(self.FIRST_PLACE_HEAD_X + 0.1, +0.055),
            font=getCompetitionFont(),
        )
        self.sad_text = OnscreenText(
            parent=self.frame,
            text="SAD!",
            style=3,
            fg=RED,
            align=TextNode.ACenter,
            scale=0.065,
            pos=(self.FIRST_PLACE_HEAD_X, 0),
            roll=-15,
            font=getCompetitionFont(),
        )

        self.extra_stats_text = OnscreenText(
            parent=self.frame,
            text="",
            style=3,
            fg=WHITE,
            align=TextNode.ABoxedCenter,
            scale=0.09,
            pos=(self.FIRST_PLACE_TEXT_X + 0.47, 0),
            font=getCompetitionFont(),
        )

        self.combo_text.hide()
        self.sad_text.hide()
        if self.avId == base.localAvatar.doId:
            self.points_text["fg"] = GOLD
            self.extra_stats_text["fg"] = GOLD

        self.extra_stats_text.hide()

        self.sadSecondsLeft = -1

        self.isBeingSpectated = False

        self.inc_ival = None

    def __attempt_spectate(self):
        # If there is no base.boss attribute set don't do anything
        if not hasattr(base, "boss"):
            return

        # Is the toon spectating?
        if not base.boss.localToonSpectating:
            return

        # Toon exists?
        t = base.cr.doId2do.get(self.avId)
        if not t:
            return

        # Already spectating?
        if self.isBeingSpectated:
            self.__stop_spectating()
            return

        # Check all the cranes
        crane = None
        for c in list(base.boss.cranes.values()):
            # Our toon is on a crane
            if c.avId == self.avId:
                crane = c
                break

        # Spectate them
        self.__change_camera_angle(t, crane)
        self.isBeingSpectated = True

        # Listen for when the toon hops on/off the crane
        self.accept("crane-enter-exit-%s" % self.avId, self.__change_camera_angle)

    def __change_camera_angle(self, toon, crane, _=None):
        base.cmod.disable()
        base.camera.reparentTo(render)
        # if crane is not None, then parent the camera to the crane, otherwise the toon
        if not crane:
            # Fallback, if toon does not exist then just exit spectate
            if not toon:
                self.__stop_spectating()
                return

            base.camera.reparentTo(toon)
            base.camera.setY(-12)
            base.camera.setZ(5)
            base.camera.setP(-5)
        else:
            base.camera.reparentTo(crane.hinge)
            camera.setPosHpr(0, -20, -5, 0, -20, 0)

    def __stop_spectating(self):
        base.localAvatar.setCameraFov(BossBattleCameraFov)
        base.cmod.enable()
        self.isBeingSpectated = False
        # Not spectating anymore, no need to watch for crane events any more
        self.ignore("crane-enter-exit-%s" % self.avId)

    def getYFromPlaceOffset(self, y):
        return y - (self.PLACE_Y_OFFSET * self.place)

    def createToonHead(self, avId, scale=0.15):
        head = ToonHead()
        av = base.cr.doId2do[avId]

        head.setupHead(av.style, forGui=1)

        head.setupToonHeadHat(av.getHat(), av.style.head)
        head.setupToonHeadGlasses(av.getGlasses(), av.style.head)

        head.fitAndCenterHead(scale, forGui=1)
        return head

    def cancel_inc_ival(self):
        if self.inc_ival:
            self.inc_ival.finish()

        self.inc_ival = None

    def addScore(self, amount, reason=""):
        # First update the amount
        old = self.points
        self.points += amount

        # find the difference
        diff = self.points - old

        # if we lost points make a red popup, if we gained green popup
        if diff > 0:
            doGainAnimation(self, diff, old, self.points, localAvFlag=self.avId == base.localAvatar.doId, reason=reason)
        elif diff < 0:
            doLossAnimation(self, diff, old, self.points, localAvFlag=self.avId == base.localAvatar.doId, reason=reason)

    def updatePosition(self):
        # Move to new position based on place
        oldPos = Point3(self.frame.getX(), self.frame.getY(), self.frame.getZ())
        newPos = Point3(self.frame.getX(), self.frame.getY(), self.getYFromPlaceOffset(self.FRAME_Y_FIRST_PLACE))
        LerpPosInterval(self.frame, duration=0.5, pos=newPos, startPos=oldPos, blendType="easeInOut").start()

    def updateExtraStatsLabel(self):
        s = "%-7s %-7s %-7s" % (self.damage, self.stuns, self.stomps)
        self.extra_stats_text.setText(s)

    def addDamage(self, n):
        self.damage += n
        self.updateExtraStatsLabel()

    def addStun(self):
        self.stuns += 1
        self.updateExtraStatsLabel()

    def addStomp(self):
        self.stomps += 1
        self.updateExtraStatsLabel()

    def expand(self):
        self.updateExtraStatsLabel()
        self.extra_stats_text.show()

    def collapse(self):
        self.extra_stats_text.hide()

    def reset(self):
        if self.isBeingSpectated:
            self.__stop_spectating()
        self.points = 0
        self.damage = 0
        self.stuns = 0
        self.stomps = 0
        self.updateExtraStatsLabel()
        self.points_text.setText("0")
        self.combo_text.setText("COMBO x0")
        self.combo_text.hide()
        taskMgr.remove("sadtimer-" + str(self.avId))
        self.sad_text.hide()
        self.sad_text.setText("SAD!")
        self.cancel_inc_ival()

    def cleanup(self):
        if self.isBeingSpectated:
            self.__stop_spectating()
        self.toon_head.cleanup()
        del self.toon_head
        self.points_text.cleanup()
        del self.points_text
        self.combo_text.cleanup()
        del self.combo_text
        taskMgr.remove("sadtimer-" + str(self.avId))
        self.sad_text.cleanup()
        del self.sad_text
        self.toon_head_button.destroy()
        del self.toon_head_button
        self.extra_stats_text.cleanup()
        del self.extra_stats_text
        self.cancel_inc_ival()
        del self.inc_ival
        self.INSTANCES.remove(self)

    def show(self):
        self.points_text.show()
        self.toon_head.show()

    def hide(self):
        self.extra_stats_text.hide()
        self.points_text.hide()
        self.toon_head.hide()
        self.combo_text.hide()
        self.sad_text.hide()

    def toonDied(self):
        self.toon_head.sadEyes()
        self.sad_text.show()
        self.sadSecondsLeft = self.ruleset.REVIVE_TOONS_TIME

        if self.ruleset.REVIVE_TOONS_UPON_DEATH:
            taskMgr.remove("sadtimer-" + str(self.avId))
            taskMgr.add(self.__updateSadTimeLeft, "sadtimer-" + str(self.avId))

    def toonRevived(self):
        self.toon_head.normalEyes()
        self.sad_text.hide()

    def __updateSadTimeLeft(self, task):
        if self.sadSecondsLeft < 0:
            return Task.done

        self.sad_text.setText(str(self.sadSecondsLeft))
        self.sadSecondsLeft -= 1
        task.delayTime = 1
        return Task.again


class CashbotBossScoreboard(DirectObject):
    def __init__(self, ruleset=None):
        DirectObject.__init__(self)

        self.ruleset = ruleset
        self.frame = DirectFrame(parent=base.a2dLeftCenter)
        self.frame.setPos(0.2, 0, 0.5)

        self.default_row, self.default_row_path = getScoreboardTextRow(
            self.frame, "master-row", default_text="%-10s %-7s\0" % ("Toon", "Pts")
        )
        self.default_row_path.setScale(0.06)

        self.rows = {}  # maps avId -> ScoreboardToonRow object
        self.accept("f1", self._consider_expand)

        self.is_expanded = False

        self.expand_tip = OnscreenText(
            parent=self.frame,
            text="Press F1 to show more stats",
            style=3,
            fg=WHITE,
            align=TextNode.ACenter,
            scale=0.05,
            pos=(0.22, 0.1),
            font=getCompetitionFont(),
        )
        self.expand_tip.hide()

    def set_ruleset(self, ruleset):
        self.ruleset = ruleset
        for r in list(self.rows.values()):
            r.ruleset = ruleset

    def _consider_expand(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self.is_expanded = True
        self.default_row.setText("%-10s %-9s %-7s %-7s %-8s\0" % ("Toon", "Pts", "Dmg", "Stuns", "Stomps"))
        for r in list(self.rows.values()):
            r.expand()

    def collapse(self):
        self.is_expanded = False
        self.default_row.setText("%-10s %-7s\0" % ("Toon", "Pts"))
        for r in list(self.rows.values()):
            r.collapse()

    def addToon(self, avId):
        if avId not in self.rows:
            self.rows[avId] = CashbotBossScoreboardToonRow(self.frame, avId, len(self.rows), ruleset=self.ruleset)

        self.show()

    def clearToons(self):
        for row in list(self.rows.values()):
            row.cleanup()
            del self.rows[row.avId]

        self.hide()

    def __addScoreLater(self, avId, amount, task=None):
        self.addScore(avId, amount, reason=CraneLeagueGlobals.LOW_LAFF_BONUS_TEXT, ignoreLaff=True)

    # Positive/negative amount of points to add to a player
    def addScore(self, avId, amount, reason="", ignoreLaff=False):
        # If we don't want to include penalties for low laff bonuses and the amount is negative ignore laff
        if not self.ruleset.LOW_LAFF_BONUS_INCLUDE_PENALTIES and amount <= 0:
            ignoreLaff = True

        # Should we consider a low laff bonus?
        if not ignoreLaff and self.ruleset.WANT_LOW_LAFF_BONUS:
            av = base.cr.doId2do.get(avId)
            if av and av.getHp() <= self.ruleset.LOW_LAFF_BONUS_THRESHOLD:
                taskMgr.doMethodLater(
                    0.75,
                    self.__addScoreLater,
                    "delayedScore",
                    extraArgs=[avId, int(amount * self.ruleset.LOW_LAFF_BONUS)],
                )

        # If we don't get an integer
        if not isinstance(amount, int):
            raise Exception("amount should be an int! got " + type(amount))

        # If it is 0 (could be set by developer) don't do anything
        if amount == 0:
            return

        if avId in self.rows:
            self.rows[avId].addScore(amount, reason=reason)
            self.updatePlacements()

    def updatePlacements(self):
        # make a list of all the objects
        rows = list(self.rows.values())
        # sort it based on how many points they have in descending order
        rows.sort(key=lambda x: x.points, reverse=True)
        # set place
        i = 0
        for r in rows:
            r.place = i
            r.updatePosition()
            i += 1

    def getToons(self):
        return list(self.rows.keys())

    def cleanup(self):
        self.clearToons()

        self.default_row_path.removeNode()
        self.ignore("f1")

    def hide_tip_later(self):
        taskMgr.remove("expand-tip")
        taskMgr.doMethodLater(5.0, self.__hide_tip, "expand-tip")

    def __hide_tip(self, _=None):
        taskMgr.remove("expand-tip")
        LerpColorScaleInterval(
            self.expand_tip, 1.0, colorScale=(1, 1, 1, 0), startColorScale=(1, 1, 1, 1), blendType="easeInOut"
        ).start()

    def reset(self):
        self.expand_tip.show()
        self.expand_tip.setColorScale(1, 1, 1, 1)
        self.hide_tip_later()
        taskMgr.remove("expand-tip")
        for row in list(self.rows.values()):
            row.reset()

        self.updatePlacements()
        self.collapse()

    def show(self):
        self.expand_tip.show()
        self.expand_tip.setColorScale(1, 1, 1, 1)
        self.hide_tip_later()
        self.default_row_path.show()
        for row in list(self.rows.values()):
            row.show()

        self.collapse()

    def hide(self):
        self.expand_tip.hide()
        self.default_row_path.hide()
        for row in list(self.rows.values()):
            row.hide()

    # updates combo text
    def setCombo(self, avId, amount):
        row = self.rows.get(avId)
        if not row:
            return

        row.combo_text.setText("x" + str(amount))

        if amount < 2:
            row.combo_text.hide()
            return

        row.combo_text["fg"] = CYAN
        row.combo_text.show()

        Parallel(
            Sequence(
                LerpScaleInterval(row.combo_text, duration=0.25, scale=1.07, startScale=1, blendType="easeInOut"),
                LerpScaleInterval(row.combo_text, duration=0.25, startScale=1.07, scale=1, blendType="easeInOut"),
            ),
            LerpColorScaleInterval(
                row.combo_text,
                duration=self.ruleset.COMBO_DURATION,
                colorScale=(1, 1, 1, 0),
                startColorScale=(1, 1, 1, 1),
            ),
        ).start()

    def toonDied(self, avId):
        row = self.rows.get(avId)
        if not row:
            return

        row.toonDied()

    def toonRevived(self, avId):
        row = self.rows.get(avId)
        if not row:
            return

        row.toonRevived()

    def addDamage(self, avId, n):
        row = self.rows.get(avId)
        if row:
            row.addDamage(n)

    def addStun(self, avId):
        row = self.rows.get(avId)
        if row:
            row.addStun()

    def addStomp(self, avId):
        row = self.rows.get(avId)
        if row:
            row.addStomp()
