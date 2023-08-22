import shlex

from toontown.chat.magic.MagicBase import FillValueSentinel, MagicWord, MagicWordArgPad, MagicWordRegistry
from toontown.chat.magic.MagicWordErrors import MagicWordError
from toontown.toonbase.globals.TTGlobalsChat import MagicWordStartSymbols


class MagicWordRunner:
    notify = directNotify.newCategory("MagicWordRunner")

    def run(self, accessLevel, wordName, args, mode, toon, doId=0):
        wordDef = MagicWordRegistry.getWordClass(wordName)
        if not wordDef:
            return MagicWordError.UNKNOWN_WORD, "", None

        # NOTE: this should occur earlier than MAGIC_WORD_NOT_ISSUED
        # so we know it should not be run on the client side if we're currently running on server
        if not self.sufficientAccessLevel(accessLevel, wordName):
            self.notify.warning(f"Insufficient access while running {wordName}! Affected toon: {doId}")
            return MagicWordError.INSUFFICIENT_ACCESS, "", None

        if mode not in wordDef.getLocations():
            return MagicWordError.MAGIC_WORD_NOT_ISSUED, "", None

        if not issubclass(wordDef, MagicWord):
            return MagicWordError.NOT_IMPLEMENTED, "", None

        argpad = MagicWordArgPad(wordDef.signature, args)
        if not argpad.valid:
            self.notify.warning(f"Invalid arguments supplied to {wordName}! Affected toon: {doId}")
            return MagicWordError.INVALID_ARGUMENTS, "", None
        mwObject = wordDef()

        mwObject.toon = toon
        mwObject.args = argpad

        success, message = mwObject.invoke()
        if not success:
            return MagicWordError.MAGIC_WORD_ERROR, message, None

        return 0, message, mwObject

    @classmethod
    def parseArgs(cls, wordString):
        # the first symbol is / slash so lets get rid of that first
        if not wordString or wordString[0] not in MagicWordStartSymbols:
            return "", [], MagicWordError.RUNNER_ERROR, {}

        wordString = wordString[1:]
        if " " not in wordString:
            wordName, argString = wordString, ""
        else:
            wordName, argString = wordString.split(" ", 1)

        if not (wordDef := MagicWordRegistry.getWordClass(wordName)):
            return wordName, [], MagicWordError.UNKNOWN_WORD, dict(name=wordName)

        argList = cls.splitArgs(argString)
        if (givenArgs := len(argList)) > (signArgs := len(wordDef.signature)):
            return wordName, [], MagicWordError.TOO_MANY_ARGS, dict(name=wordName, expected=signArgs, given=givenArgs)
        minArgs = sum(1 for item in wordDef.signature if item.default is FillValueSentinel)
        if givenArgs < minArgs:
            return wordName, [], MagicWordError.TOO_FEW_ARGS, dict(name=wordName, expected=minArgs, given=givenArgs)

        values = []
        for givenArg, signItem in zip(argList, wordDef.signature):
            try:
                value = signItem.type.stringToValue(givenArg)
                values.append(signItem.type.valueToDatagram(value))
            except ValueError as e:
                return wordName, [], MagicWordError.ARGUMENT_ERROR, dict(name=wordName, error_msg=e)
        return wordName, values, 0, {}

    @staticmethod
    def splitArgs(argString):
        lex = shlex.shlex(argString)
        lex.quotes = '"'
        lex.whitespace_split = True
        lex.commenters = ""
        return list(lex)

    @staticmethod
    def sufficientAccessLevel(accessLevel, wordName):
        wordDef = MagicWordRegistry.getWordClass(wordName)
        if not wordDef:
            return False

        return wordDef.permissionLevel <= accessLevel
