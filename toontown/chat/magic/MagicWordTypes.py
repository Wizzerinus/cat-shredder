from toontown.chat.magic.MagicBase import MagicWordDataType


class MWTInteger(MagicWordDataType):
    def __init__(self, minValue=None, maxValue=None, byteLength=4):
        self.minValue = minValue
        self.maxValue = maxValue
        self.byteLength = byteLength

    def validate(self, num):
        if self.minValue is not None and num < self.minValue:
            raise ValueError(f"Value {num} must not be less than {self.minValue}")
        if self.maxValue is not None and num > self.maxValue:
            raise ValueError(f"Value {num} must not be greater than {self.maxValue}")
        return num

    def stringToValue(self, value: str):
        try:
            value = int(value)
        except ValueError as e:
            raise ValueError(f"Value {value} must be an integer") from e
        return self.validate(value)

    def valueToDatagram(self, value) -> bytes:
        return value.to_bytes(self.byteLength, "big")

    def fromDatagram(self, value: bytes):
        return self.validate(int.from_bytes(value, "big"))


def cleanString(val):
    return val.lower().replace("_", "").replace("-", "")


class MWTNormalEnum(MagicWordDataType):
    def __init__(self, enum):
        self.enum = enum
        self.valueSet = {cleanString(i.name): i.name for i in enum}

    def stringToValue(self, value: str):
        value = cleanString(value)
        if (name := self.valueSet.get(value)) is not None:
            return name

        raise ValueError(f"Invalid enum value: {value}")

    def valueToDatagram(self, value) -> bytes:
        return value.encode("utf-8")

    def fromDatagram(self, value: bytes):
        return self.stringToValue(value.decode("utf-8"))

    def getOptions(self):
        return list(self.valueSet.keys())


class MWTIntEnum(MagicWordDataType):
    def __init__(self, enum, byteLength=2):
        self.enum = enum
        self.byteLength = byteLength
        self.intSet = set(enum)
        self.enumItems = {cleanString(i.name): i.value for i in enum}

    def stringToValue(self, value: str):
        value = cleanString(value)
        if (enumItem := self.enumItems.get(value)) is not None:
            return enumItem

        try:
            data = int(value)
        except ValueError as e:
            raise ValueError(f"Value {value} not found in the enum and is not a number") from e
        if data in self.intSet:
            return data

        raise ValueError(f"Value {value} is not in the enum")

    def valueToDatagram(self, value) -> bytes:
        return value.to_bytes(self.byteLength, "big")

    def fromDatagram(self, value: bytes):
        return self.enum(int.from_bytes(value, "big"))

    def getOptions(self):
        return list(self.enumItems.keys())


class MWTBool(MagicWordDataType):
    def stringToValue(self, value: str):
        if value.lower() in ("false", "0", "-", "no"):
            return False
        return True

    def valueToDatagram(self, value) -> bytes:
        return bytes(1) if value else bytes(0)

    def fromDatagram(self, value: bytes):
        return value != bytes(0)
