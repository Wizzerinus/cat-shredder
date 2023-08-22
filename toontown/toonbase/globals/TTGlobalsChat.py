from enum import IntEnum, auto


class Emotes(IntEnum):
    WAVE = 0
    HAPPY = auto()
    SAD = auto()
    ANGRY = auto()
    SLEEPY = auto()
    SHRUG = auto()
    THINK = auto()
    BOW = auto()
    APPLAUSE = auto()
    DANCE = auto()
    BORED = auto()
    CRINGE = auto()
    CONFUSED = auto()
    BELLY_FLOP = auto()
    BANANA_PEEL = auto()
    SURPRISE = auto()
    CRY = auto()
    DELIGHTED = auto()
    FURIOUS = auto()
    LAUGH = auto()
    SALUTE = auto()
    YES = auto()
    NO = auto()


DefaultEmotes = [Emotes.WAVE, Emotes.HAPPY, Emotes.YES, Emotes.SAD, Emotes.NO, Emotes.ANGRY, Emotes.SLEEPY]

EmoteDict = {
    Emotes.WAVE: "Wave",
    Emotes.HAPPY: "Happy",
    Emotes.SAD: "Sad",
    Emotes.ANGRY: "Angry",
    Emotes.SLEEPY: "Sleepy",
    Emotes.SHRUG: "Shrug",
    Emotes.THINK: "Think",
    Emotes.BOW: "Bow",
    Emotes.APPLAUSE: "Applause",
    Emotes.DANCE: "Dance",
    Emotes.BORED: "Bored",
    Emotes.CRINGE: "Cringe",
    Emotes.CONFUSED: "Confused",
    Emotes.BELLY_FLOP: "Belly Flop",
    Emotes.BANANA_PEEL: "Banana Peel",
    Emotes.SURPRISE: "Surprise",
    Emotes.CRY: "Cry",
    Emotes.DELIGHTED: "Delighted",
    Emotes.FURIOUS: "Furious",
    Emotes.LAUGH: "Laugh",
    Emotes.SALUTE: "Resistance Salute",
}

EmoteWhispers = {
    Emotes.WAVE: "%s waves.",
    Emotes.HAPPY: "%s is happy.",
    Emotes.SAD: "%s is sad.",
    Emotes.ANGRY: "%s is angry.",
    Emotes.SLEEPY: "%s is sleepy.",
    Emotes.SHRUG: "%s shrugs.",
    Emotes.DANCE: "%s dances.",
    Emotes.THINK: "%s thinks.",
    Emotes.BORED: "%s is bored.",
    Emotes.APPLAUSE: "%s applauds.",
    Emotes.CRINGE: "%s cringes.",
    Emotes.CONFUSED: "%s is confused.",
    Emotes.BELLY_FLOP: "%s does a belly flop.",
    Emotes.BOW: "%s bows to you.",
    Emotes.BANANA_PEEL: "%s slips on a banana peel.",
    Emotes.SURPRISE: "%s is surprised.",
    Emotes.CRY: "%s is crying.",
    Emotes.DELIGHTED: "%s is delighted.",
    Emotes.FURIOUS: "%s is furious.",
    Emotes.LAUGH: "%s is laughing.",
    Emotes.SALUTE: "%s gives the resistance salute.",
}

# Reverse lookup:  get the index from the name.
EmoteName2Id = {name: emote for emote, name in EmoteDict.items()}

ChatOnlyEmotes = {Emotes.YES, Emotes.NO}

# Cutoff string lengths to determine how much barking to play
DialogLength1 = 6
DialogLength2 = 12
DialogLength3 = 20
DialogSpecial = "ooo"
DialogExclamation = "!"
DialogQuestion = "?"


class CheesyEffects:
    NORMAL = 0
    GHOST = "g"


SPEEDCHAT_NORMAL = 1
SPEEDCHAT_EMOTE = 2
SPEEDCHAT_CUSTOM = 3

MagicWordStartSymbols = ["/", "~", "`"]
