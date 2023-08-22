from enum import IntEnum, auto


class MagicWordError(IntEnum):
    UNKNOWN_WORD = auto()
    INSUFFICIENT_ACCESS = auto()
    INVALID_ARGUMENTS = auto()
    RUNNER_ERROR = auto()
    MAGIC_WORD_ERROR = auto()
    TOO_MANY_ARGS = auto()
    TOO_FEW_ARGS = auto()
    ARGUMENT_ERROR = auto()
    NOT_IMPLEMENTED = auto()

    # Special error that is not really a error
    MAGIC_WORD_NOT_ISSUED = auto()


ErrorDescriptions = {
    MagicWordError.UNKNOWN_WORD: "Unknown magic word: %(name)s",
    MagicWordError.INSUFFICIENT_ACCESS: "Insufficient access to use %(name)s!",
    # this one can only happen if something goes totally wrong, probably an injector.
    MagicWordError.INVALID_ARGUMENTS: "Invalid argument list issued!",
    MagicWordError.RUNNER_ERROR: "Unknown error while invoking the magic word!",
    MagicWordError.MAGIC_WORD_ERROR: "Magic word failed: %(status)s",
    MagicWordError.TOO_MANY_ARGS: "Too many arguments for %(name)s! Expected up to %(expected)d, given %(given)d.",
    MagicWordError.TOO_FEW_ARGS: "Too few arguments for %(name)s! Expected at least %(expected)d, given %(given)d.",
    MagicWordError.NOT_IMPLEMENTED: "The magic word %(name)s is not implemented!",
    MagicWordError.ARGUMENT_ERROR: "Error parsing argument for %(name)s: %(error_msg)s.",
}

DefaultError = "Unknown error while executing a magic word!"
