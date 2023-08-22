class PlayerBase:
    def __init__(self):
        self.gmState = False

    def isGM(self):
        return self.gmState
