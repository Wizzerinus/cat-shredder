from datetime import datetime, timedelta, timezone

from direct.gui.DirectGui import *
from panda3d.core import *

from direct.task.Task import Task

from toontown.toonbase.globals.TTGlobalsGUI import getCompetitionFont


class BossSpeedrunTimer:
    TIMER = 0
    STOPWATCH = 1
    MODE = STOPWATCH

    def __init__(self):
        self.frame = DirectFrame(pos=(-0.22, 0, 0.9))
        self.time_text = OnscreenText(
            parent=self.frame,
            text="00:00.00",
            style=3,
            fg=(0.9, 0.9, 0.9, 0.85),
            align=TextNode.ALeft,
            scale=0.1,
            font=getCompetitionFont(),
        )
        self.reset()
        self.overridden_time = None
        self.start_updating()

    def reset(self):
        self.started = datetime.now(tz=timezone.utc)
        self.overridden_time = None

    def set_pos(self, pos):
        self.frame.setPos(pos)

    def stop_updating(self):
        taskMgr.remove("boss-timer-update-time")

    def start_updating(self):
        self.stop_updating()
        taskMgr.add(self._update_time_task, "boss-timer-update-time")

    def _update_time_task(self, task):
        self.update_time()
        return Task.cont

    def update_time(self):
        now = datetime.now(tz=timezone.utc)
        difference = now - self.started
        total_secs = difference.total_seconds() if not self.overridden_time else self.overridden_time
        minutes = total_secs // 60
        seconds = total_secs % 60
        frac = int((total_secs - int(total_secs)) * 100)
        new_time = "{:02}:{:02}.{:02}".format(int(minutes), int(seconds), frac)
        self.time_text.setText(new_time)

    def override_time(self, secs):
        self.overridden_time = secs

    def cleanup(self):
        self.stop_updating()
        self.time_text.cleanup()
        self.frame.destroy()

    def show(self):
        self.time_text.show()

    def hide(self):
        self.time_text.hide()


# Same thing as the other timer, but counts down instead
class BossSpeedrunTimedTimer(BossSpeedrunTimer):
    MODE = BossSpeedrunTimer.TIMER

    def __init__(self, time_limit):
        BossSpeedrunTimer.__init__(self)
        self.time_limit = time_limit

    def reset(self):
        BossSpeedrunTimer.reset(self)
        self.time_text["fg"] = (0.9, 0.9, 0.9, 0.85)

    def update_time(self):
        now = datetime.now(tz=timezone.utc)
        end = self.started + timedelta(seconds=self.time_limit)
        time_left = end - now
        total_secs = time_left.total_seconds()
        if total_secs < 0:
            total_secs = 0

        if self.overridden_time is not None:
            self.time_text["fg"] = (0, 0.7, 0, 1) if self.overridden_time > 0.0 else (0.7, 0, 0, 1)
            if self.overridden_time <= 0.0:
                self.time_text.setText("00:00.00")
                return

        if total_secs <= 10:
            frac_secs = int((total_secs - int(total_secs)) * 100)
            self.time_text["fg"] = (0.7, 0, 0, 1) if frac_secs < 50 else (0.9, 0.9, 0.9, 0.85)
        elif total_secs <= 31:
            self.time_text["fg"] = (0.7, 0, 0, 1) if int(total_secs) % 2 == 0 else (0.9, 0.9, 0.9, 0.85)

        minutes = total_secs // 60
        seconds = total_secs % 60
        frac = int((total_secs - int(total_secs)) * 100)

        new_time = "{:02}:{:02}.{:02}".format(int(minutes), int(seconds), frac)
        self.time_text.setText(new_time)
