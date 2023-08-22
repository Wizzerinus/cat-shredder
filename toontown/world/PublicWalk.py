from . import Walk


class PublicWalk(Walk.Walk):
    notify = directNotify.newCategory("PublicWalk")

    def __init__(self, parentFSM, doneEvent):
        Walk.Walk.__init__(self, doneEvent)
        self.parentFSM = parentFSM

    def load(self):
        Walk.Walk.load(self)

    def unload(self):
        Walk.Walk.unload(self)
        del self.parentFSM

    def enter(self, slowWalk=0):
        Walk.Walk.enter(self, slowWalk)
        base.localAvatar.laffMeter.start()

    def exit(self):
        Walk.Walk.exit(self)
        base.localAvatar.laffMeter.stop()
