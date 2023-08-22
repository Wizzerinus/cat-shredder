import abc
import itertools
from enum import Enum, auto
from typing import Any, ClassVar, Dict, List, NamedTuple, Sequence, Tuple, Type

from toontown.toon.Toon import Toon

# some argument types Might use None as a valid value so we make a sentinel
FillValueSentinel = object()


class MagicWordDataType(abc.ABC):
    @abc.abstractmethod
    def stringToValue(self, value: str):
        """
        Converts a string from the chat input box into a value usable by the magic word.
        """

    @abc.abstractmethod
    def valueToDatagram(self, value) -> bytes:
        """
        Converts a value usable by the magic word, into a datagram to be passed over the wire.
        """

    @abc.abstractmethod
    def fromDatagram(self, value: bytes):
        """
        Converts a datagram from the wire into a final value used as an argument to the magic word.
        """

    def getOptions(self) -> Sequence[str]:
        """
        Optional method. Returns the autocomplete options available to this data type.
        Note: we should store this in a trie, but I didn't find a suitable library for this.
        """
        return []


class MagicWordParameter(NamedTuple):
    type: MagicWordDataType
    name: str = ""
    description: str = ""
    default: Any = FillValueSentinel


class MagicWordLocation(Enum):
    SERVER = auto()
    CLIENT = auto()


class MagicWordArgPad:
    def __init__(self, signature, args):
        self.validationErrors = []
        self.__args = {}

        self.signature = signature
        for sig, arg in itertools.zip_longest(signature, args, fillvalue=FillValueSentinel):
            try:
                value = sig.default if arg is FillValueSentinel else sig.type.fromDatagram(arg)
            except ValueError:
                self.validationErrors.append(sig.name)
            else:
                self.__args[sig.name] = value

    def __getitem__(self, item):
        return self.__args[item]

    @property
    def valid(self):
        return len(self.validationErrors) == 0

    def __iter__(self):
        return (getattr(self, sig.name) for sig in self.signature)


class MagicWordStub(abc.ABC):
    description: str = ""
    signature: ClassVar[Sequence[MagicWordParameter]] = []
    locations: ClassVar[List[MagicWordLocation]] = None
    location: ClassVar[MagicWordLocation] = None
    permissionLevel: ClassVar[int] = 1000
    administrative: bool = False

    args: MagicWordArgPad
    toon: Toon

    @classmethod
    def getLocations(cls):
        if cls.locations is not None:
            return cls.locations
        return [cls.location]


class MagicWord(MagicWordStub, abc.ABC):
    def __init__(self):
        self.clientsideCommands = []

    @abc.abstractmethod
    def invoke(self) -> Tuple[bool, str]:
        pass

    def addClientsideCommand(self, command, args):
        self.clientsideCommands.append((command, args))


class MagicWordRegistry:
    magicWords: Dict[str, Type[MagicWordStub]] = {}
    aliases: Dict[str, str] = {}
    stubToWord: Dict[Type[MagicWordStub], Type[MagicWord]] = {}

    @classmethod
    def check(cls, name):
        assert name not in cls.magicWords, f"Magic word {name} is already registered!"
        assert name not in cls.aliases, f"Magic word {name} is already registered as an alias!"

    @classmethod
    def stub(cls, *names: str):
        assert len(names) > 0, "Magic words need at least one name!"
        if __debug__:
            for alias in names:
                cls.check(alias)

        name, *aliases = names
        for alias in aliases:
            cls.aliases[alias] = name

        def decorator(stubcls: Type[MagicWordStub]):
            cls.magicWords[name] = stubcls
            return stubcls

        return decorator

    @classmethod
    def command(cls, mwcls: Type[MagicWord]):
        for clazz in reversed(mwcls.__mro__):
            if issubclass(clazz, MagicWordStub) and clazz.permissionLevel != 1000:
                stub = clazz
                break
        else:
            raise RuntimeError(f"Unable to find the stub subclass for {mwcls}!")

        cls.stubToWord[stub] = mwcls
        return mwcls

    @classmethod
    def getWordClass(cls, wordName):
        wordName = wordName.lower()
        wordName = cls.aliases.get(wordName, wordName)
        stubCls = cls.magicWords.get(wordName)
        if stubCls is None:
            return None
        return cls.stubToWord.get(stubCls, stubCls)


def formatBool(name, value):
    if value:
        return f"{name} enabled."
    return f"{name} disabled."
