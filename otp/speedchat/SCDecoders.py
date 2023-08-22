from otp.speedchat.SCCustomTerminal import decodeSCCustomMsg  # noqa: F401
from otp.speedchat.SCEmoteTerminal import decodeSCEmoteWhisperMsg  # noqa: F401
from otp.speedchat.SCStaticTextTerminal import decodeSCStaticTextMsg  # noqa: F401
from toontown.toonbase.globals import TTGlobalsChat

"""SCDecoders.py: contains functions to decode SpeedChat messages """

"""
Each of these functions normally returns the ready-to-display text
string that corresponds to the encoded message. If there is a problem,
None is returned.
"""

decoderCallbacks = {
    TTGlobalsChat.SPEEDCHAT_NORMAL: decodeSCStaticTextMsg,
    TTGlobalsChat.SPEEDCHAT_CUSTOM: decodeSCCustomMsg,
    TTGlobalsChat.SPEEDCHAT_EMOTE: decodeSCEmoteWhisperMsg,
}


def decodeMessageFlexible(mode, message, avName=None):
    if mode == TTGlobalsChat.SPEEDCHAT_EMOTE:
        return decoderCallbacks[mode](message, avName)
    return decoderCallbacks[mode](message)
