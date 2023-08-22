class PotentialAvatar:
    def __init__(
        self,
        avId,
        name,
        dna,
        position,
        creator=1,
        shared=1,
        online=0,
        lastLogout=0,
    ):
        self.id = avId
        self.avName = name
        self.dna = dna
        self.avatarType = None
        self.position = position
        self.creator = creator
        self.shared = shared
        self.online = online
        self.lastLogout = lastLogout
