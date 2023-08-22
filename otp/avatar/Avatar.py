import random

from direct.actor.Actor import Actor
from direct.distributed import ClockDelta
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.MetaInterval import Sequence
from panda3d.core import CollisionNode, CollisionTube, Point3
from panda3d.otp import CFNoQuitButton, CFPageButton, CFQuitButton, CFSpeech
from panda3d.otp import Nametag, NametagGroup

from otp.avatar.ShadowCaster import ShadowCaster
from toontown.toonbase.globals.TTGlobalsAvatars import AvatarDefaultRadius, ShadowScales
from toontown.toonbase.globals.TTGlobalsChat import *
from toontown.toonbase.globals.TTGlobalsGUI import getInterfaceFont
from toontown.toonbase.globals.TTGlobalsRender import *
import contextlib

teleportNotify = directNotify.newCategory("Teleport")
teleportNotify.showTime = True


class Avatar(Actor, ShadowCaster):
    """
    Avatar class: contains methods for making actors that walk
    and talk
    """

    notify = directNotify.newCategory("Avatar")

    ActiveAvatars = []
    ManagesNametagAmbientLightChanged = False
    Avatar_initialized = False
    Avatar_deleted = False
    shadow = None
    playerType = None
    collNode = None
    collNodePath = None

    def __init__(self, mat=0, other=None):
        """
        Create the toon, suit, or char specified by the dna array
        """

        if self.Avatar_initialized:
            return
        self.Avatar_initialized = True

        self._name = ""

        Actor.__init__(self, None, None, other, flattenable=0, setFinal=1)
        ShadowCaster.__init__(self, False)
        self.getGeomNode().showThrough(ShadowCameraBitmask)
        self.mat = mat
        self.__font = getInterfaceFont()

        self.soundChatBubble = None

        self.avatarType = ""
        self.enableBlend()
        self.setTwoSided(False)

        self.nametagNodePath = None

        self.__nameVisible = 1
        self.nametag = NametagGroup()
        self.nametag.setAvatar(self)
        self.nametag.setFont(getInterfaceFont())
        self.nametag2dContents = Nametag.CName | Nametag.CSpeech
        self.nametag2dDist = Nametag.CName | Nametag.CSpeech
        self.nametag2dNormalContents = Nametag.CName | Nametag.CSpeech

        self.nametag3d = self.attachNewNode("nametag3d")
        self.nametag3d.setTag("cam", "nametag")
        self.nametag3d.setLightOff()

        if self.ManagesNametagAmbientLightChanged:
            self.acceptNametagAmbientLightChange()

        renderReflection(False, self.nametag3d, "otp_avatar_nametag", None)

        self.getGeomNode().showThrough(ShadowCameraBitmask)
        self.nametag3d.hide(ShadowCameraBitmask)

        self.collTube = None
        self.battleTube = None

        self.scale = 1.0
        self.nametagScale = 1.0
        self.height = 0.0
        self.battleTubeHeight = 0.0
        self.battleTubeRadius = 0.0
        self.style = None
        self.setPlayerType(NametagGroup.CCNormal)

        self.ghostMode = 0

        self.__chatParagraph = None
        self.__chatMessage = None
        self.__chatFlags = 0
        self.__chatPageNumber = None
        self.__chatAddressee = None
        self.__chatDialogueList = []
        self.__chatSet = 0
        self.__chatLocal = 0
        self.currentDialogue = None
        self.displayName = ""

    def initShadow(self):
        if game.mockeryInstance:
            return
        if self.shadow is not None:
            self.shadow.removeNode()
            self.shadow = None

        self.shadow = loader.loadModel("phase_3/models/props/drop_shadow.bam")
        self.shadow.setScale(ShadowScales[self.avatarType])
        self.shadow.flattenMedium()
        self.shadow.setBillboardAxis(2)
        self.shadow.setColor(0, 0, 0, 0.5, 1)
        self.shadow.reparentTo(self)

    def delete(self):
        if self.Avatar_deleted:
            return
        self.Avatar_deleted = True

        self.deleteNametag3d()
        Actor.cleanup(self)
        if self.ManagesNametagAmbientLightChanged:
            self.ignoreNametagAmbientLightChange()
        del self.__font
        del self.soundChatBubble
        del self.nametag
        self.nametag3d.removeNode()
        Actor.delete(self)

    def deleteShadow(self):
        if hasattr(self, "shadow") and self.shadow:
            self.shadow.removeNode()
            self.shadow = None

    def acceptNametagAmbientLightChange(self):
        self.accept("nametagAmbientLightChanged", self.nametagAmbientLightChanged)

    def ignoreNametagAmbientLightChange(self):
        self.ignore("nametagAmbientLightChanged")

    def isLocal(self):
        return 0

    def isPet(self):
        return False

    @staticmethod
    def isProxy():
        return False

    def setPlayerType(self, playerType):
        """
        setPlayerType(self, NametagGroup.ColorCode playerType)

        Indicates whether the avatar is a human player
        (NametagGroup.CCNormal), a friendly non-player character
        (NametagGroup.CCNonPlayer), or a suit (NametagGroup.CCSuit).
        This determines the color of the nametag, as well as whether
        chat messages from this avatar should be garbled.
        """
        self.playerType = playerType

        if not hasattr(self, "nametag"):
            self.notify.warning("no nametag attributed, but would have been used.")
            return
        self.nametag.setColorCode(self.playerType)

    def setDNA(self, dna):
        assert self.notify.error("called setDNA on parent class")

    def getAvatarScale(self):
        """
        Return the avatar's scale
        """
        return self.scale

    def setAvatarScale(self, scale):
        """
        Set the avatar's scale.  This both sets the scale on the
        NodePath, and also stores it for later retrieval, not to
        mention fiddling with the nametag to keep everything
        consistent.  You should use this call to adjust the avatar's
        scale, instead of adjusting it directly.
        """
        if self.scale != scale:
            self.scale = scale
            self.getGeomNode().setScale(scale)
            self.setHeight(self.height)

    def getNametagScale(self):
        """
        Return the nametag's overall scale.  This value does not
        change in response to camera position.
        """
        return self.nametagScale

    def setNametagScale(self, scale):
        """
        Sets the scale of the 3-d nametag floating over the avatar's
        head.  The nametags will also be scaled in response to the
        camera position, but this gives us an overall scale.
        """
        self.nametagScale = scale
        self.nametag3d.setScale(scale)

    def adjustNametag3d(self):
        """adjustNametag3d(self)
        Adjust nametag according to the height
        """
        self.nametag3d.setPos(0, 0, self.height + 0.5)

    def getHeight(self):
        """
        Return the avatar's height
        """
        return self.height

    def setHeight(self, height):
        """setHeight(self, float)
        Set the avatar's height.
        """
        self.height = height
        self.adjustNametag3d()
        if self.collTube:
            self.collTube.setPointB(0, 0, height - self.getRadius())
            if self.collNodePath:
                self.collNodePath.forceRecomputeBounds()
        if self.battleTube:
            self.battleTube.setPointB(0, 0, height - self.getRadius())

    def getRadius(self):
        """
        Returns the radius of the avatar's collision tube.
        """
        return AvatarDefaultRadius

    def getName(self):
        """
        Return the avatar's name
        """
        return self.name

    def getType(self):
        """
        Return the avatar's Type
        """
        return self.avatarType

    def setName(self, name):
        """
        name is a string

        Set the avatar's name
        """
        self.name = name
        if hasattr(self, "nametag"):
            self.nametag.setName(name)

    def setDisplayName(self, strr):
        self.nametag.setDisplayName(strr)
        self.displayName = strr

    def getFont(self):
        """
        Returns the font used to display the avatar's name and chat
        messages.
        """
        return self.__font

    def setFont(self, font):
        """
        Changes the font used to display the avatar's name and chat
        messages.
        """
        self.__font = font
        self.nametag.setFont(font)

    def getStyle(self):
        """
        Return the dna string for the avatar
        """
        return self.style

    def getShadow(self):
        if hasattr(self, "shadow") and self.shadow:
            return self.shadow
        return None

    def setStyle(self, style):
        self.style = style

    def getDialogueArray(self):
        return None

    def playCurrentDialogue(self, dialogue, chatFlags, interrupt=1):
        if interrupt and self.currentDialogue is not None:
            self.currentDialogue.stop()
        self.currentDialogue = dialogue
        if dialogue:
            base.playSfx(dialogue, node=self)
        elif (chatFlags & CFSpeech) != 0 and self.nametag.getNumChatPages() > 0:
            self.playDialogueForString(self.nametag.getChat())
            if self.soundChatBubble is not None:
                base.playSfx(self.soundChatBubble, node=self)

    def playDialogueForString(self, chatString, delay=0.0):
        """
        Play dialogue samples to match the given chat string
        """
        if not chatString:
            return

        searchString = chatString.lower()
        if searchString.find(DialogSpecial) >= 0:
            dialogueType = "special"
        elif searchString.find(DialogExclamation) >= 0:
            dialogueType = "exclamation"
        elif searchString.find(DialogQuestion) >= 0:
            dialogueType = "question"
        else:
            dialogueType = random.choice(["statementA", "statementB"])

        stringLength = len(chatString)
        if stringLength <= DialogLength1:
            length = 1
        elif stringLength <= DialogLength2:
            length = 2
        elif stringLength <= DialogLength3:
            length = 3
        else:
            length = 4

        self.playDialogue(dialogueType, length, delay)

    def setChatAbsolute(self, chatString, chatFlags, dialogue=None, interrupt=1):
        """
        Receive the chat string, play dialogue if in range, display
        the chat message and spawn task to reset the chat message
        """
        self.nametag.setChat(chatString, chatFlags)

        self.playCurrentDialogue(dialogue, chatFlags, interrupt)

    def setChatMuted(self, chatString, chatFlags, dialogue=None, interrupt=1, quiet=0):
        """
        This method is a modification of setChatAbsolute in Toontown in which
        just the text of the chat is displayed on the nametag.
        No animal sound is played along with it.
        This method is defined in toontown/src/toon/DistributedToon.
        """

    def displayTalk(self, chatString):
        if base.localAvatar.checkIgnored(self.doId):
            return

        message, flags = base.talkAssistant.parseMessage(chatString)
        self.nametag.setChat(message, flags)

    def clearChat(self):
        """
        Clears the last chat message
        """
        self.nametag.clearChat()

    def isInView(self):
        """
        Check to see if avatar is in view. Use a point near the eye height
        to perform the test
        """
        pos = self.getPos(camera)
        eyePos = Point3(pos[0], pos[1], pos[2] + self.getHeight())
        return base.camNode.isInView(eyePos)

    def getNameVisible(self):
        return self.__nameVisible

    def setNameVisible(self, isVisible):
        self.__nameVisible = isVisible
        if isVisible:
            self.showName()
        else:
            self.hideName()

    def hideName(self):
        self.nametag.getNametag3d().setContents(Nametag.CSpeech | Nametag.CThought)

    def showName(self):
        if self.__nameVisible and not self.ghostMode:
            self.nametag.getNametag3d().setContents(Nametag.CName | Nametag.CSpeech | Nametag.CThought)

    def hideNametag2d(self):
        """
        Temporarily hides the onscreen 2-d nametag.
        """
        self.nametag2dContents = 0
        self.nametag.getNametag2d().setContents(self.nametag2dContents & self.nametag2dDist)

    def showNametag2d(self):
        """
        Reveals the onscreen 2-d nametag after a previous call to
        hideNametag2d.
        """
        self.nametag2dContents = self.nametag2dNormalContents
        if self.ghostMode:
            self.nametag2dContents = Nametag.CSpeech

        self.nametag.getNametag2d().setContents(self.nametag2dContents & self.nametag2dDist)

    def hideNametag3d(self):
        """
        Temporarily hides the 3-d nametag.
        """
        self.nametag.getNametag3d().setContents(0)

    def showNametag3d(self):
        """
        Reveals the 3-d nametag after a previous call to
        hideNametag3d.
        """
        if self.__nameVisible and not self.ghostMode:
            self.nametag.getNametag3d().setContents(Nametag.CName | Nametag.CSpeech | Nametag.CThought)
        else:
            self.nametag.getNametag3d().setContents(0)

    def setPickable(self, flag):
        """
        Indicates whether the avatar can be picked by clicking on him
        or his nametag.
        """
        self.nametag.setActive(flag)

    def clickedNametag(self):
        """
        This hook is called whenever the user clicks on the nametag
        associated with this particular avatar (or, rather, clicks on
        the avatar itself).  It simply maps that C++-generated event
        into a Python event that includes the avatar as a parameter.
        """
        if self.nametag.hasButton():
            self.advancePageNumber()
        elif self.nametag.isActive():
            messenger.send("av-clickedNametag", [self])

    def setPageChat(
        self, addressee, paragraph, message, quitButton, extraChatFlags=None, dialogueList=None, pageButton=True
    ):
        """
        setPageChat(self, int addressee, int paragraph, string message, bool quitButton, list dialogueList)

        The NPC is giving instruction or quest information to a
        particular Toon, which may involve multiple pages of text that
        the user must click through.

        The paragraph number indicates a unique number for the
        particular paragraph that is being spoken, and the addressee
        is the particular Toon that is being addressed.  Only the
        indicated Toon will be presented with the click-through
        buttons.

        This is normally called by the client from within a movie; it
        is not a message in its own right.
        """
        if dialogueList is None:
            dialogueList = []
        self.__chatAddressee = addressee
        self.__chatPageNumber = None
        self.__chatParagraph = paragraph
        self.__chatMessage = message
        if extraChatFlags is None:
            self.__chatFlags = CFSpeech
        else:
            self.__chatFlags = CFSpeech | extraChatFlags
        self.__chatDialogueList = dialogueList
        self.__chatSet = 0
        self.__chatLocal = 0
        self.__updatePageChat()

        if addressee == base.localAvatar.doId:
            if pageButton:
                self.__chatFlags |= CFPageButton
            if quitButton is None:
                self.__chatFlags |= CFNoQuitButton
            elif quitButton:
                self.__chatFlags |= CFQuitButton

            self.b_setPageNumber(self.__chatParagraph, 0)

    def setLocalPageChat(self, message, quitButton, extraChatFlags=None, dialogueList=None):
        """
        setLocalPageChat(self, string message, bool quitButton, list dialogueList)

        Locally sets up a multiple-page chat message.  This is
        intended for use when the NPC is giving advice to the toon in
        a local context, e.g. in the Tutorial.

        If quitButton is 1, a red cancel button will be drawn in the
        place of the page advance arrow on the last page.  If
        quitButton is 0, a page advance arrow will be drawn on the
        last page.  If quitButton is None, no button at all will be
        drawn on the last page.
        """
        if dialogueList is None:
            dialogueList = []
        self.__chatAddressee = base.localAvatar.doId
        self.__chatPageNumber = None
        self.__chatParagraph = None
        self.__chatMessage = message
        if extraChatFlags is None:
            self.__chatFlags = CFSpeech
        else:
            self.__chatFlags = CFSpeech | extraChatFlags
        self.__chatDialogueList = dialogueList
        self.__chatSet = 1
        self.__chatLocal = 1

        self.__chatFlags |= CFPageButton
        if quitButton is None:
            self.__chatFlags |= CFNoQuitButton
        elif quitButton:
            self.__chatFlags |= CFQuitButton

        dialogue = dialogueList[0] if len(dialogueList) > 0 else None
        self.clearChat()
        self.setChatAbsolute(message, self.__chatFlags, dialogue)
        self.setPageNumber(None, 0)

    def setPageNumber(self, paragraph, pageNumber, timestamp=None):
        """
        setPageNumber(self, int paragraph, int pageNumber)

        This message is generated by the client when the advance-page
        button is clicked.  All clients also receive this message.
        When the pageNumber is -1, the last page has been cleared.
        """
        elapsed = 0.0 if timestamp is None else ClockDelta.globalClockDelta.localElapsedTime(timestamp)

        self.__chatPageNumber = [paragraph, pageNumber]
        self.__updatePageChat()

        if hasattr(self, "uniqueName"):
            if pageNumber >= 0:
                messenger.send(self.uniqueName("nextChatPage"), [pageNumber, elapsed])
            else:
                messenger.send(self.uniqueName("doneChatPage"), [elapsed])
        elif pageNumber >= 0:
            messenger.send("nextChatPage", [pageNumber, elapsed])
        else:
            messenger.send("doneChatPage", [elapsed])

    def advancePageNumber(self):
        """
        Advances the page for the previously-spoken pageChat message.
        This is a distributed call.  This is normally called only in
        response to the user clicking on the next-page button for the
        message directed to himself.
        """
        if (
            self.__chatAddressee == base.localAvatar.doId
            and self.__chatPageNumber is not None
            and self.__chatPageNumber[0] == self.__chatParagraph
        ):
            pageNumber = self.__chatPageNumber[1]
            if pageNumber >= 0:
                pageNumber += 1
                if pageNumber >= self.nametag.getNumChatPages():
                    pageNumber = -1

                if self.__chatLocal:
                    self.setPageNumber(self.__chatParagraph, pageNumber)
                else:
                    self.b_setPageNumber(self.__chatParagraph, pageNumber)

    def __updatePageChat(self):
        """
        Updates the nametag to display the appropriate paging chat
        message, if all parameters are now available.
        """
        if self.__chatPageNumber is not None and self.__chatPageNumber[0] == self.__chatParagraph:
            pageNumber = self.__chatPageNumber[1]
            if pageNumber >= 0:
                if not self.__chatSet:
                    dialogue = self.__chatDialogueList[0] if len(self.__chatDialogueList) > 0 else None
                    if hasattr(base.cr, "chatLog"):
                        base.cr.chatLog.addToLog(f"{self.name}: {self.__chatMessage}")

                    self.setChatAbsolute(self.__chatMessage, self.__chatFlags, dialogue)
                    self.__chatSet = 1
                if pageNumber < self.nametag.getNumChatPages():
                    self.nametag.setPageNumber(pageNumber)
                    if pageNumber > 0:
                        if len(self.__chatDialogueList) > pageNumber:
                            dialogue = self.__chatDialogueList[pageNumber]
                        else:
                            dialogue = None
                        messenger.send("addChatHistory", [self.name, self.__chatMessage])
                        self.playCurrentDialogue(dialogue, self.__chatFlags)
                else:
                    self.clearChat()
            else:
                self.clearChat()

    def initializeNametag3d(self):
        """
        Put the 3-d nametag in the right place over the avatar's head.
        This is normally done at some point after initialization,
        after the NametagGroup in self.nametag has already been
        created.  This is mainly just responsible for finding the
        right node or nodes to parent the 3-d nametag to.
        """
        self.deleteNametag3d()

        nametagNode = self.nametag.getNametag3d()
        self.nametagNodePath = self.nametag3d.attachNewNode(nametagNode)

        for cJoint in self.getNametagJoints():
            cJoint.clearNetTransforms()
            cJoint.addNetTransform(nametagNode)

    def nametagAmbientLightChanged(self, newlight):
        """
        Get new ambient light when this avatar has changed locations/TODmanagers
        """
        self.nametag3d.setLightOff()
        if newlight:
            self.nametag3d.setLight(newlight)

    def deleteNametag3d(self):
        """
        Lose the 3-d nametag
        """
        if self.nametagNodePath:
            self.nametagNodePath.removeNode()
            self.nametagNodePath = None

    def initializeBodyCollisions(self, collIdStr):
        self.collTube = CollisionTube(0, 0, 0.5, 0, 0, self.height - self.getRadius(), self.getRadius())
        self.collNode = CollisionNode(collIdStr)
        self.collNode.addSolid(self.collTube)
        self.collNodePath = self.attachNewNode(self.collNode)

        if self.ghostMode:
            self.collNode.setCollideMask(GhostBitmask)
        else:
            self.collNode.setCollideMask(WallBitmask)

    def stashBodyCollisions(self):
        if hasattr(self, "collNodePath"):
            self.collNodePath.stash()

    def unstashBodyCollisions(self):
        if hasattr(self, "collNodePath"):
            self.collNodePath.unstash()

    def disableBodyCollisions(self):
        if hasattr(self, "collNodePath"):
            self.collNodePath.removeNode()
            del self.collNodePath

        self.collTube = None

    def addActive(self):
        """
        Adds the avatar to the list of currently-active avatars.
        """
        if base.wantNametags:
            assert self.notify.debug(f"Adding avatar {self.getName()}")

            with contextlib.suppress(ValueError):
                Avatar.ActiveAvatars.remove(self)

            Avatar.ActiveAvatars.append(self)
            self.nametag.manage(base.marginManager)

            self.accept(self.nametag.getUniqueId(), self.clickedNametag)

    def removeActive(self):
        """
        Removes the avatar from the list of currently-active avatars.
        """
        if base.wantNametags:
            assert self.notify.debug(f"Removing avatar {self.getName()}")
            try:
                Avatar.ActiveAvatars.remove(self)
            except ValueError:
                assert self.notify.warning(f"{self.getName()} was not present...")

            self.nametag.unmanage(base.marginManager)
            self.ignore(self.nametag.getUniqueId())

    def loop(self, animName, restart=1, partName=None, fromFrame=None, toFrame=None):
        return Actor.loop(self, animName, restart, partName, fromFrame, toFrame)

    def getDialogueSfx(self, sfxType, length):
        dialogueArray = self.getDialogueArray()
        if dialogueArray is None:
            return None

        sfxIndex = None
        if sfxType in ("statementA", "statementB"):
            sfxIndex = min(2, max(0, length - 1))
        elif sfxType == "question":
            sfxIndex = 3
        elif sfxType == "exclamation":
            sfxIndex = 4
        elif sfxType == "special":
            sfxIndex = 5
        else:
            self.notify.error("unrecognized dialogue type: ", sfxType)
        if sfxIndex is not None and sfxIndex < len(dialogueArray):
            return dialogueArray[sfxIndex]

        return None

    def playSfx(self, delay, dialogueItem):
        Sequence(Wait(delay), Func(base.playSfx, dialogueItem, node=self)).start()

    def playDialogue(self, sfxType, length, delay=0.0):
        """playDialogue(self, string, int)
        Play the specified type of dialogue for the specified time
        """

        self.playSfx(delay, self.getDialogueSfx(sfxType, length))
