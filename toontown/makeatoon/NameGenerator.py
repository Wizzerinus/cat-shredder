import random

from panda3d.core import *

from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont


class NameGenerator:
    text = TextNode("text")
    text.setFont(getInterfaceFont())
    notify = directNotify.newCategory("NameGenerator")
    boyTitles = []
    girlTitles = []
    neutralTitles = []
    boyFirsts = []
    girlFirsts = []
    neutralFirsts = []
    capPrefixes = []
    lastPrefixes = []
    lastSuffixes = []

    def __init__(self):
        self.generateLists()

    def generateLists(self):
        self.boyTitles = []
        self.girlTitles = []
        self.neutralTitles = []
        self.boyFirsts = []
        self.girlFirsts = []
        self.neutralFirsts = []
        self.capPrefixes = []
        self.lastPrefixes = []
        self.lastSuffixes = []
        self.nameDictionary = {}
        searchPath = DSearchPath()
        if __debug__:
            searchPath.appendDirectory(Filename("resources/phase_3/etc"))
        filename = Filename("NameMasterEnglish.txt")
        found = vfs.resolveFilename(filename, searchPath)
        if not found:
            self.notify.error("NameGenerator: Error opening name list text file '%s'." % "NameMasterEnglish.txt")
        contentReader = StreamReader(vfs.openReadFile(filename, 1), 1)
        currentLine = contentReader.readline()
        while currentLine:
            if currentLine.lstrip()[0:1] != b"#":
                a1 = currentLine.find(b"*")
                a2 = currentLine.find(b"*", a1 + 1)
                self.nameDictionary[int(currentLine[0:a1])] = (
                    int(currentLine[a1 + 1 : a2]),
                    currentLine[a2 + 1 :].rstrip().decode("utf-8"),
                )
            currentLine = contentReader.readline()

        masterList = [
            self.boyTitles,
            self.girlTitles,
            self.neutralTitles,
            self.boyFirsts,
            self.girlFirsts,
            self.neutralFirsts,
            self.capPrefixes,
            self.lastPrefixes,
            self.lastSuffixes,
        ]
        for tu in list(self.nameDictionary.values()):
            masterList[tu[0]].append(tu[1])

        return 1

    def returnUniqueID(self, name, listnumber):
        newtu = [(), (), ()]
        if listnumber == 0:
            newtu[0] = (0, name)
            newtu[1] = (1, name)
            newtu[2] = (2, name)
        elif listnumber == 1:
            newtu[0] = (3, name)
            newtu[1] = (4, name)
            newtu[2] = (5, name)
        elif listnumber == 2:
            newtu[0] = (6, name)
            newtu[1] = (7, name)
        else:
            newtu[0] = (8, name)
        for tu in list(self.nameDictionary.items()):
            for g in newtu:
                if tu[1] == g:
                    return tu[0]

        return -1

    def randomNameMoreinfo(self, boy=0, girl=0):
        if boy and girl:
            self.notify.error("A name can't be both boy and girl!")
        if not boy and not girl:
            boy = random.choice([0, 1])
            girl = not boy
        uberFlag = random.choice(["title-first", "title-last", "first", "last", "first-last", "title-first-last"])
        titleFlag = "title" in uberFlag
        firstFlag = "first" in uberFlag
        lastFlag = "last" in uberFlag
        retString = ""
        uberReturn = [0, 0, 0, "", "", "", ""]
        uberReturn[0] = titleFlag
        uberReturn[1] = firstFlag
        uberReturn[2] = lastFlag
        titleList = self.neutralTitles[:]
        if boy:
            titleList += self.boyTitles
        elif girl:
            titleList += self.girlTitles
        else:
            self.notify.error("Must be boy or girl.")
        uberReturn[3] = random.choice(titleList)
        firstList = self.neutralFirsts[:]
        if boy:
            firstList += self.boyFirsts
        elif girl:
            firstList += self.girlFirsts
        else:
            self.notify.error("Must be boy or girl.")
        uberReturn[4] = random.choice(firstList)
        lastPrefix = random.choice(self.lastPrefixes)
        lastSuffix = random.choice(self.lastSuffixes)
        if lastPrefix in self.capPrefixes:
            lastSuffix = lastSuffix.capitalize()
        uberReturn[5] = lastPrefix
        uberReturn[6] = lastSuffix
        if titleFlag:
            retString += uberReturn[3] + " "
        if firstFlag:
            retString += uberReturn[4]
            if lastFlag:
                retString += " "
        if lastFlag:
            retString += uberReturn[5] + uberReturn[6]
        uberReturn.append(retString)
        return uberReturn
