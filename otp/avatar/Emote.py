from toontown.toonbase.globals.TTGlobalsChat import EmoteName2Id


class Emote:
    EmoteClear = -1
    EmoteEnableStateChanged = "EmoteEnableStateChanged"

    def __init__(self):
        self.emoteFunc = None

    def isEnabled(self, index):
        if isinstance(index, str):
            index = EmoteName2Id[index]

        if self.emoteFunc is None:
            return 0
        elif self.emoteFunc[index][1] == 0:
            return 1
        return 0


globalEmote = None
