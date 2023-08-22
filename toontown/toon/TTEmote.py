from direct.interval.IntervalGlobal import *
from direct.showbase import PythonUtil
from panda3d.core import *
from panda3d.otp import *

from otp.avatar import Emote
from toontown.toonbase import TTLSpeedChat, TTLocalizer
from toontown.toonbase.globals.TTGlobalsChat import EmoteName2Id, Emotes
from . import ToonDNA

EmoteSleepIndex = 4
EmoteClear = -1


def doVictory(toon, volume=1):
    duration = toon.getDuration("victory", "legs")
    sfx = base.loader.loadSfx("phase_3.5/audio/sfx/ENC_Win.ogg")
    sfxDuration = duration - 1.0
    sfxTrack = SoundInterval(sfx, loop=1, duration=sfxDuration, node=toon, volume=volume)
    track = Sequence(Func(toon.play, "victory"), sfxTrack, duration=0)
    return (track, duration, None)


def doJump(toon, volume=1):
    track = Sequence(Func(toon.play, "jump"))
    return (track, 0, None)


def doDead(toon, volume=1):
    toon.animFSM.request("Sad")
    return (None, 0, None)


def doAnnoyed(toon, volume=1):
    duration = toon.getDuration("angry", "torso")
    sfx = None
    if toon.style.getAnimal() == "bear":
        sfx = base.loader.loadSfx("phase_3.5/audio/dial/AV_bear_exclaim.ogg")
    else:
        sfx = base.loader.loadSfx("phase_3.5/audio/sfx/avatar_emotion_angry.ogg")

    def playSfx():
        base.playSfx(sfx, volume=volume, node=toon)

    track = Sequence(Func(toon.angryEyes), Func(toon.blinkEyes), Func(toon.play, "angry"), Func(playSfx))
    exitTrack = Sequence(Func(toon.normalEyes), Func(toon.blinkEyes))
    return (track, duration, exitTrack)


def doAngryEyes(toon, volume=1):
    track = Sequence(Func(toon.angryEyes), Func(toon.blinkEyes), Wait(10.0), Func(toon.normalEyes))
    return (track, 0.1, None)


def doHappy(toon, volume=1):
    track = Sequence(Func(toon.play, "jump"), Func(toon.normalEyes), Func(toon.blinkEyes))
    duration = toon.getDuration("jump", "legs")
    return (track, duration, None)


def doSad(toon, volume=1):
    track = Sequence(Func(toon.sadEyes), Func(toon.blinkEyes))
    exitTrack = Sequence(Func(toon.normalEyes), Func(toon.blinkEyes))
    return (track, 3, exitTrack)


def doSleep(toon, volume=1):
    duration = 4
    track = Sequence(
        Func(toon.stopLookAround),
        Func(toon.stopBlink),
        Func(toon.closeEyes),
        Func(toon.lerpLookAt, Point3(0, 1, -4)),
        Func(toon.loop, "neutral"),
        Func(toon.setPlayRate, 0.4, "neutral"),
        Func(toon.setChatAbsolute, TTLocalizer.ToonSleepString, CFThought),
    )

    def wakeUpFromSleepEmote():
        toon.startLookAround()
        toon.openEyes()
        toon.startBlink()
        toon.setPlayRate(1, "neutral")
        if toon.nametag.getChat() == TTLocalizer.ToonSleepString:
            toon.clearChat()
        toon.lerpLookAt(Point3(0, 1, 0), time=0.25)

    exitTrack = Sequence(Func(wakeUpFromSleepEmote))
    return (track, duration, exitTrack)


def doYes(toon, volume=1):
    tracks = Parallel(autoFinish=1)
    for lod in toon.getLODNames():
        h = toon.getPart("head", lod)
        tracks.append(
            Sequence(
                LerpHprInterval(h, 0.1, Vec3(0, -30, 0)),
                LerpHprInterval(h, 0.15, Vec3(0, 20, 0)),
                LerpHprInterval(h, 0.15, Vec3(0, -20, 0)),
                LerpHprInterval(h, 0.15, Vec3(0, 20, 0)),
                LerpHprInterval(h, 0.15, Vec3(0, -20, 0)),
                LerpHprInterval(h, 0.15, Vec3(0, 20, 0)),
                LerpHprInterval(h, 0.1, Vec3(0, 0, 0)),
            )
        )

    tracks.start()
    return (None, 0, None)


def doNo(toon, volume=1):
    tracks = Parallel(autoFinish=1)
    for lod in toon.getLODNames():
        h = toon.getPart("head", lod)
        tracks.append(
            Sequence(
                LerpHprInterval(h, 0.1, Vec3(40, 0, 0)),
                LerpHprInterval(h, 0.15, Vec3(-40, 0, 0)),
                LerpHprInterval(h, 0.15, Vec3(40, 0, 0)),
                LerpHprInterval(h, 0.15, Vec3(-40, 0, 0)),
                LerpHprInterval(h, 0.15, Vec3(20, 0, 0)),
                LerpHprInterval(h, 0.15, Vec3(-20, 0, 0)),
                LerpHprInterval(h, 0.1, Vec3(0, 0, 0)),
            )
        )

    tracks.start()
    return (None, 0, None)


def doShrug(toon, volume=1):
    sfx = base.loader.loadSfx("phase_3.5/audio/sfx/avatar_emotion_shrug.ogg")

    def playSfx():
        base.playSfx(sfx, volume=volume, node=toon)

    track = Sequence(Func(toon.play, "shrug"), Func(playSfx))
    duration = toon.getDuration("shrug", "torso")
    return (track, duration, None)


def doWave(toon, volume=1):
    track = Sequence(Func(toon.play, "wave"))
    duration = toon.getDuration("wave", "torso")
    return (track, duration, None)


def doApplause(toon, volume=1):
    sfx = base.loader.loadSfx("phase_4/audio/sfx/avatar_emotion_applause.ogg")

    def playSfx():
        base.playSfx(sfx, volume=1, node=toon)

    track = Sequence(Func(toon.play, "applause"), Func(playSfx))
    duration = toon.getDuration("applause", "torso")
    return (track, duration, None)


def doConfused(toon, volume=1):
    sfx = base.loader.loadSfx("phase_4/audio/sfx/avatar_emotion_confused.ogg")

    def playSfx():
        base.playSfx(sfx, node=toon, volume=volume)

    track = Sequence(Func(toon.play, "confused"), Func(playSfx))
    duration = toon.getDuration("confused", "torso")
    return (track, duration, None)


def doSlipForward(toon, volume=1):
    sfx = base.loader.loadSfx("phase_4/audio/sfx/MG_cannon_hit_dirt.ogg")

    def playSfx():
        base.playSfx(sfx, volume=volume, node=toon)

    sfxDelay = 0.7
    track = Sequence(Func(toon.play, "slip-forward"), Wait(sfxDelay), Func(playSfx))
    duration = toon.getDuration("slip-forward", "torso") - sfxDelay
    return (track, duration, None)


def doBored(toon, volume=1):
    sfx = base.loader.loadSfx("phase_4/audio/sfx/avatar_emotion_bored.ogg")

    def playSfx():
        base.playSfx(sfx, volume=volume, node=toon)

    sfxDelay = 2.2
    track = Sequence(Func(toon.play, "bored"), Wait(sfxDelay), Func(playSfx))
    duration = toon.getDuration("bored", "torso") - sfxDelay
    return (track, duration, None)


def doBow(toon, volume=1):
    if toon.style.torso[1] == "d":
        track = Sequence(Func(toon.play, "curtsy"))
        duration = toon.getDuration("curtsy", "torso")
    else:
        track = Sequence(Func(toon.play, "bow"))
        duration = toon.getDuration("bow", "torso")
    return (track, duration, None)


def doSlipBackward(toon, volume=1):
    sfx = base.loader.loadSfx("phase_4/audio/sfx/MG_cannon_hit_dirt.ogg")

    def playSfx():
        base.playSfx(sfx, volume=volume, node=toon)

    sfxDelay = 0.7
    track = Sequence(Func(toon.play, "slip-backward"), Wait(sfxDelay), Func(playSfx))
    duration = toon.getDuration("slip-backward", "torso") - sfxDelay
    return (track, duration, None)


def doThink(toon, volume=1):
    duration = 47.0 / 24.0 * 2
    animTrack = Sequence(
        ActorInterval(toon, "think", startFrame=0, endFrame=46), ActorInterval(toon, "think", startFrame=46, endFrame=0)
    )
    track = Sequence(animTrack, duration=0)
    return (track, duration, None)


def doCringe(toon, volume=1):
    track = Sequence(Func(toon.play, "cringe"))
    duration = toon.getDuration("cringe", "torso")
    return (track, duration, None)


def doResistanceSalute(toon, volume=1):
    playRate = 0.75
    duration = 10.0 / 24.0 * (1 / playRate) * 2
    animTrack = Sequence(
        Func(toon.setChatAbsolute, TTLSpeedChat.CustomSCStrings[4020], CFSpeech | CFTimeout),
        Func(toon.setPlayRate, playRate, "victory"),
        ActorInterval(toon, "victory", playRate=playRate, startFrame=0, endFrame=9),
        ActorInterval(toon, "victory", playRate=playRate, startFrame=9, endFrame=0),
    )
    track = Sequence(animTrack, duration=0)
    return (track, duration, None)


def doNothing(toon, volume=1):
    return (None, 0, None)


def doSurprise(toon, volume=1):
    sfx = None
    sfx = base.loader.loadSfx("phase_4/audio/sfx/avatar_emotion_surprise.ogg")

    def playSfx(volume=1):
        base.playSfx(sfx, volume=volume, node=toon)

    def playAnim(anim):
        anim.start()

    def stopAnim(anim):
        anim.finish()
        toon.stop()
        sfx.stop()

    anim = Sequence(
        ActorInterval(toon, "conked", startFrame=9, endFrame=50),
        ActorInterval(toon, "conked", startFrame=70, endFrame=101),
    )
    track = Sequence(
        Func(toon.stopBlink),
        Func(toon.surpriseEyes),
        Func(toon.showSurpriseMuzzle),
        Parallel(Func(playAnim, anim), Func(playSfx, volume)),
    )
    exitTrack = Sequence(
        Func(toon.hideSurpriseMuzzle), Func(toon.openEyes), Func(toon.startBlink), Func(stopAnim, anim)
    )
    return (track, 3.0, exitTrack)


def doUpset(toon, volume=1):
    sfx = None
    sfx = base.loader.loadSfx("phase_4/audio/sfx/avatar_emotion_very_sad_1.ogg")

    def playSfx(volume=1):
        base.playSfx(sfx, volume=volume, node=toon)

    def playAnim(anim):
        anim.start()

    def stopAnim(anim):
        anim.finish()
        toon.stop()
        sfx.stop()

    anim = Sequence(
        ActorInterval(toon, "bad-putt", startFrame=29, endFrame=59, playRate=-0.75),
        ActorInterval(toon, "bad-putt", startFrame=29, endFrame=59, playRate=0.75),
    )
    track = Sequence(
        Func(toon.sadEyes),
        Func(toon.blinkEyes),
        Func(toon.showSadMuzzle),
        Parallel(Func(playAnim, anim), Func(playSfx, volume)),
    )
    exitTrack = Sequence(Func(toon.hideSadMuzzle), Func(toon.normalEyes), Func(stopAnim, anim))
    return (track, 4.0, exitTrack)


def doDelighted(toon, volume=1):
    sfx = None
    sfx = base.loader.loadSfx("phase_4/audio/sfx/delighted_06.ogg")

    def playSfx(volume=1):
        base.playSfx(sfx, volume=volume, node=toon)

    def playAnim(anim):
        anim.start()

    def stopAnim(anim):
        anim.finish()
        toon.stop()
        sfx.stop()

    anim = Sequence(ActorInterval(toon, "left"), Wait(1), ActorInterval(toon, "left", playRate=-1))
    track = Sequence(
        Func(toon.blinkEyes), Func(toon.showSmileMuzzle), Parallel(Func(playAnim, anim), Func(playSfx, volume))
    )
    exitTrack = Sequence(Func(toon.hideSmileMuzzle), Func(toon.blinkEyes), Func(stopAnim, anim))
    return (track, 2.5, exitTrack)


def doFurious(toon, volume=1):
    duration = toon.getDuration("angry", "torso")
    sfx = None
    sfx = base.loader.loadSfx("phase_4/audio/sfx/furious_03.ogg")

    def playSfx(volume=1):
        base.playSfx(sfx, volume=volume, node=toon)

    track = Sequence(
        Func(toon.angryEyes),
        Func(toon.blinkEyes),
        Func(toon.showAngryMuzzle),
        Func(toon.play, "angry"),
        Func(playSfx, volume),
    )
    exitTrack = Sequence(Func(toon.normalEyes), Func(toon.blinkEyes), Func(toon.hideAngryMuzzle))
    return (track, duration, exitTrack)


def doLaugh(toon, volume=1):
    sfx = None
    sfx = base.loader.loadSfx("phase_4/audio/sfx/avatar_emotion_laugh.ogg")

    def playSfx(volume=1):
        base.playSfx(sfx, volume=volume, node=toon)

    def playAnim():
        toon.setPlayRate(10, "neutral")
        toon.loop("neutral")

    def stopAnim():
        toon.setPlayRate(1, "neutral")

    track = Sequence(Func(toon.blinkEyes), Func(toon.showLaughMuzzle), Func(playAnim), Func(playSfx, volume))
    exitTrack = Sequence(Func(toon.hideLaughMuzzle), Func(toon.blinkEyes), Func(stopAnim))
    return (track, 2, exitTrack)


def getSingingNote(toon, note, volume=1):
    sfx = None
    filePath = "phase_3.5/audio/dial/"
    filePrefix = "tt_s_dlg_sng_"
    fileSuffix = ".ogg"
    speciesName = ToonDNA.getSpeciesName(toon.style.head)
    sfx = base.loader.loadSfx(filePath + filePrefix + speciesName + "_" + note + fileSuffix)

    def playSfx(volume=1):
        base.playSfx(sfx, volume=volume, node=toon)

    def playAnim():
        toon.loop("neutral")

    def stopAnim():
        toon.setPlayRate(1, "neutral")

    track = Sequence(Func(toon.showSurpriseMuzzle), Parallel(Func(playAnim), Func(playSfx, volume)))
    exitTrack = Sequence(Func(toon.hideSurpriseMuzzle), Func(stopAnim))
    return (track, 0.1, exitTrack)


def playSingingAnim(toon):
    pass


def stopSinginAnim(toon):
    pass


def returnToLastAnim(toon):
    if hasattr(toon, "playingAnim") and toon.playingAnim:
        toon.loop(toon.playingAnim)
    elif not hasattr(toon, "hp") or toon.hp > 0:
        toon.loop("neutral")
    else:
        toon.loop("sad-neutral")


EmoteFunc = {
    Emotes.WAVE: [doWave, 0],
    Emotes.HAPPY: [doHappy, 0],
    Emotes.SAD: [doSad, 0],
    Emotes.ANGRY: [doAnnoyed, 0],
    Emotes.SLEEPY: [doSleep, 0],
    Emotes.SHRUG: [doShrug, 0],
    Emotes.DANCE: [doVictory, 0],
    Emotes.THINK: [doThink, 0],
    Emotes.BORED: [doBored, 0],
    Emotes.APPLAUSE: [doApplause, 0],
    Emotes.CRINGE: [doCringe, 0],
    Emotes.CONFUSED: [doConfused, 0],
    Emotes.BELLY_FLOP: [doSlipForward, 0],
    Emotes.BOW: [doBow, 0],
    Emotes.BANANA_PEEL: [doSlipBackward, 0],
    Emotes.SALUTE: [doResistanceSalute, 0],
    Emotes.YES: [doYes, 0],
    Emotes.NO: [doNo, 0],
    Emotes.SURPRISE: [doSurprise, 0],
    Emotes.CRY: [doUpset, 0],
    Emotes.DELIGHTED: [doDelighted, 0],
    Emotes.FURIOUS: [doFurious, 0],
    Emotes.LAUGH: [doLaugh, 0],
}


class TTEmote(Emote.Emote):
    notify = directNotify.newCategory("TTEmote")
    SLEEP_INDEX = 4

    def __init__(self):
        self.emoteFunc = EmoteFunc
        self.headEmotes = [Emotes.YES, Emotes.NO, Emotes.SAD]
        self.bodyEmotes = [emote for emote in Emotes if emote not in self.headEmotes]
        if len(self.emoteFunc) != len(Emotes):
            self.notify.error("Emote.EmoteFunc and OTPLocalizer.EmoteList are different lengths.")
        self.track = None
        self.stateChangeMsgLocks = 0
        self.stateHasChanged = 0
        return

    def lockStateChangeMsg(self):
        self.stateChangeMsgLocks += 1

    def unlockStateChangeMsg(self):
        if self.stateChangeMsgLocks <= 0:
            print(PythonUtil.lineTag() + ": someone unlocked too many times")
            return
        self.stateChangeMsgLocks -= 1
        if self.stateChangeMsgLocks == 0 and self.stateHasChanged:
            messenger.send(self.EmoteEnableStateChanged)
            self.stateHasChanged = 0

    def emoteEnableStateChanged(self):
        if self.stateChangeMsgLocks > 0:
            self.stateHasChanged = 1
        else:
            messenger.send(self.EmoteEnableStateChanged)

    def disableAll(self, toon, msg=None):
        if toon != base.localAvatar:
            return
        self.disableGroup(list(range(len(self.emoteFunc))), toon)

    def releaseAll(self, toon, msg=None):
        if toon != base.localAvatar:
            return
        self.enableGroup(list(range(len(self.emoteFunc))), toon)

    def disableBody(self, toon, msg=None):
        if toon != base.localAvatar:
            return
        self.disableGroup(self.bodyEmotes, toon)

    def releaseBody(self, toon, msg=None):
        if toon != base.localAvatar:
            return
        self.enableGroup(self.bodyEmotes, toon)

    def disableHead(self, toon, msg=None):
        if toon != base.localAvatar:
            return
        self.disableGroup(self.headEmotes, toon)

    def releaseHead(self, toon, msg=None):
        if toon != base.localAvatar:
            return
        self.enableGroup(self.headEmotes, toon)

    def getHeadEmotes(self):
        return self.headEmotes

    def disableGroup(self, indices, toon):
        self.lockStateChangeMsg()
        for i in indices:
            self.disable(i, toon)

        self.unlockStateChangeMsg()

    def enableGroup(self, indices, toon):
        self.lockStateChangeMsg()
        for i in indices:
            self.enable(i, toon)

        self.unlockStateChangeMsg()

    def disable(self, index, toon):
        if isinstance(index, str):
            index = EmoteName2Id[index]
        self.emoteFunc[index][1] = self.emoteFunc[index][1] + 1
        if toon is base.localAvatar:
            if self.emoteFunc[index][1] == 1:
                self.emoteEnableStateChanged()

    def enable(self, index, toon):
        if isinstance(index, str):
            index = EmoteName2Id[index]
        self.emoteFunc[index][1] = self.emoteFunc[index][1] - 1
        if toon is base.localAvatar:
            if self.emoteFunc[index][1] == 0:
                self.emoteEnableStateChanged()

    def doEmote(self, toon, emoteIndex, ts=0, volume=1):
        try:
            func = self.emoteFunc[emoteIndex][0]
        except:
            print("Error in finding emote func %s" % emoteIndex)
            return (None, None)

        def clearEmoteTrack():
            base.localAvatar.emoteTrack = None
            base.localAvatar.d_setEmoteState(self.EmoteClear, 1.0)
            return

        if volume == 1:
            track, duration, exitTrack = func(toon)
        else:
            track, duration, exitTrack = func(toon, volume)
        if track != None:
            track = Sequence(Func(self.disableAll, toon, "doEmote"), track)
            if duration > 0:
                track = Sequence(track, Wait(duration))
            if exitTrack != None:
                track = Sequence(track, exitTrack)
            if duration > 0:
                track = Sequence(track, Func(returnToLastAnim, toon))
            track = Sequence(track, Func(self.releaseAll, toon, "doEmote"), autoFinish=1)
            if toon.isLocal():
                track = Sequence(track, Func(clearEmoteTrack))
        if track != None:
            if toon.emote != None:
                toon.emote.finish()
                toon.emote = None
            toon.emote = track
            track.start(ts)
        del clearEmoteTrack
        return (track, duration)

    def printEmoteState(self, action, msg):
        pass


Emote.globalEmote = TTEmote()
globalEmote = Emote.globalEmote
