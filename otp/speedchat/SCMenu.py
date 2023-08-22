from direct.showbase.PythonUtil import makeList
from direct.task import Task
from panda3d.core import NodePath

from otp.speedchat.SCConstants import *
from otp.speedchat.SCObject import SCObject
from toontown.toonbase import TTLSpeedChat


class SCMenu(SCObject, NodePath):
    """SCMenu is a menu of SCElements"""

    SpeedChatRolloverTolerance = 0.08

    SerialNum = 0

    BackgroundModelName = None
    GuiModelName = None

    def __init__(self, holder=None):
        SCObject.__init__(self)

        self.SerialNum = SCMenu.SerialNum
        SCMenu.SerialNum += 1

        node = hidden.attachNewNode(f"SCMenu{self.SerialNum}")
        NodePath.__init__(self, node)

        self.setHolder(holder)

        self.FinalizeTaskName = f"SCMenu{self.SerialNum}_Finalize"
        self.ActiveMemberSwitchTaskName = f"SCMenu{self.SerialNum}_SwitchActiveMember"

        self.bg = loader.loadModel(self.BackgroundModelName)

        def findNodes(names, model=self.bg):
            results = []
            for name in names:
                for nm in makeList(name):
                    node = model.find(f"**/{nm}")
                    if not node.isEmpty():
                        results.append(node)
                        break
            return results

        (
            self.bgTop,
            self.bgBottom,
            self.bgLeft,
            self.bgRight,
            self.bgMiddle,
            self.bgTopLeft,
            self.bgBottomLeft,
            self.bgTopRight,
            self.bgBottomRight,
        ) = findNodes(
            [("top", "top1"), "bottom", "left", "right", "middle", "topLeft", "bottomLeft", "topRight", "bottomRight"]
        )

        self.bg.reparentTo(self, -1)

        self.__members = []

        self.activeMember = None
        self.activeCandidate = None

        self.width = 1

        self.inFinalize = 0

    def destroy(self):
        SCObject.destroy(self)
        del self.bgTop
        del self.bgBottom
        del self.bgLeft
        del self.bgRight
        del self.bgMiddle
        del self.bgBottomLeft
        del self.bgTopRight
        del self.bgBottomRight
        self.bg.removeNode()
        del self.bg

        self.holder = None
        for member in self.__members:
            member.destroy()
        del self.__members
        self.removeNode()

        taskMgr.remove(self.FinalizeTaskName)
        taskMgr.remove(self.ActiveMemberSwitchTaskName)

    def clearMenu(self):
        """This will empty our menu, and destroy all of the current
        member elements."""
        while len(self):
            item = self[0]
            del self[0]
            item.destroy()

    def rebuildFromStructure(self, structure, title=None):
        """This will destroy the current content of this menu and replace
        it with the tree described by 'structure'."""
        self.clearMenu()

        if title:
            holder = self.getHolder()
            if holder:
                holder.setTitle(title)

        self.appendFromStructure(structure)

    def appendFromStructure(self, structure):
        """This will add the tree elements described by 'structure' to the
        existing menu elements.

        structure should be a list of Python objects that represent SpeedChat
        elements. Here is the mapping of Python objects to SpeedChat elements:

        Integers represent static-text terminal elements. They should be valid
        indices into OTPLocalizer.SpeedChatStaticText.

        Lists represent menus: the format is
         [menuType, title, elem1, elem2, ..]
        'menuType' is the desired menu class (if omitted, defaults to SCMenu).
        'title' is the text that should appear on the menu's holder element.
        elem1, etc. are the elements that should appear in the menu.

        Emotes are attached to terminal elements using dictionaries:
         {terminal:emoteId}
        """

        from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
        from otp.speedchat.SCMenuHolder import SCMenuHolder

        def addChildren(menu, childList):
            """this recursive function adds children to an SCMenu
            according to the specification in 'childList'. See above
            for the format of childList (it matches the format of
            'structure')."""
            for child in childList:
                emote = None
                if isinstance(child, tuple):
                    child, emote = child

                if isinstance(child, type(0)):
                    if child not in TTLSpeedChat.SpeedChatStaticText:
                        continue
                    terminal = SCStaticTextTerminal(child)
                    if emote is not None:
                        terminal.setLinkedEmote(emote)
                    menu.append(terminal)
                elif isinstance(child, type([])):
                    if isinstance(child[0], type("")):
                        holderTitle = child[0]
                        subMenu = SCMenu()
                        subMenuChildren = child[1:]
                    else:
                        menuType, holderTitle = child[0], child[1]
                        subMenu = menuType()
                        subMenuChildren = child[2:]
                    if emote:
                        self.notify.warning(f"tried to link emote {emote} to a menu holder")
                    holder = SCMenuHolder(holderTitle, menu=subMenu)
                    menu.append(holder)
                    addChildren(subMenu, subMenuChildren)
                else:
                    raise ValueError("error parsing speedchat structure. invalid child: %s ")

        addChildren(self, structure)
        addChildren = None

    def enterVisible(self):
        SCObject.enterVisible(self)
        self.privScheduleFinalize()

        for member in self:
            if member.isViewable() and not member.isVisible():
                member.enterVisible()

    def exitVisible(self):
        SCObject.exitVisible(self)
        self.privCancelFinalize()
        self.__cancelActiveMemberSwitch()
        self.__setActiveMember(None)
        for member in self:
            if member.isVisible():
                member.exitVisible()

    """ The 'holder' is an element that 'owns' this menu; if 'None', this
    is a free-standing menu. """

    def setHolder(self, holder):
        self.holder = holder

    def getHolder(self):
        return self.holder

    def isTopLevel(self):
        return self.holder is None

    def memberSelected(self, member):
        """non-terminal member elements should call this when they are
        clicked on; immediately makes them the active member."""
        assert member in self

        self.__cancelActiveMemberSwitch()

        self.__setActiveMember(member)

    def __setActiveMember(self, member):
        """this function actually does the work of switching the active
        member."""
        if self.activeMember is member:
            return
        if self.activeMember is not None:
            self.activeMember.exitActive()
        self.activeMember = member
        if self.activeMember is not None:
            self.activeMember.reparentTo(self)
            self.activeMember.enterActive()

    """ Member elements will call these functions to inform us that they
    have gained/lost the input focus. Based on calls to these functions,
    we will instruct our elements to go active or inactive. """

    def memberGainedInputFocus(self, member):
        """member elements will call this function to let us know that
        they have gained the input focus"""
        assert member in self

        self.__cancelActiveMemberSwitch()

        if member is self.activeMember:
            return

        if (
            (self.activeMember is None)
            or (SCMenu.SpeedChatRolloverTolerance == 0)
            or (member.posInParentMenu < self.activeMember.posInParentMenu)
        ):
            self.__setActiveMember(member)
        else:

            def doActiveMemberSwitch(task, member=member):
                self.activeCandidate = None
                self.__setActiveMember(member)
                return Task.done

            minFrameRate = 1.0 / SCMenu.SpeedChatRolloverTolerance
            if globalClock.getAverageFrameRate() > minFrameRate:
                taskMgr.doMethodLater(
                    SCMenu.SpeedChatRolloverTolerance, doActiveMemberSwitch, self.ActiveMemberSwitchTaskName
                )
                self.activeCandidate = member
            else:
                self.__setActiveMember(member)

    def __cancelActiveMemberSwitch(self):
        """Call this to clean up a delayed active-member switch without
        switching to the candidate. Okay to call even if there currently
        is no candidate.
        """
        taskMgr.remove(self.ActiveMemberSwitchTaskName)
        self.activeCandidate = None

    def memberLostInputFocus(self, member):
        """member elements will call this function to let us know that
        they have lost the input focus"""
        assert member in self

        if member is self.activeCandidate:
            self.__cancelActiveMemberSwitch()

        if member is not self.activeMember:
            """this can occur now that we delay switching of the active
            member to ensure that the user actually wants the switch
            to occur."""
            assert not member.isActive()
        elif not member.hasStickyFocus():
            self.__setActiveMember(None)

    def memberViewabilityChanged(self, member):
        """member elements will call this if their viewability state
        changes."""

        self.invalidate()

    def invalidate(self):
        """Call this if something has changed and we should reconstruct
        ourselves:
        - member added
        - member removed
        - member visibility state change
        etc.
        """
        SCObject.invalidate(self)

        if self.isVisible():
            self.privScheduleFinalize()

    def privScheduleFinalize(self):
        def finalizeMenu(task):
            self.finalize()
            return Task.done

        taskMgr.remove(self.FinalizeTaskName)
        taskMgr.add(finalizeMenu, self.FinalizeTaskName, priority=SCMenuFinalizePriority)

    def privCancelFinalize(self):
        taskMgr.remove(self.FinalizeTaskName)

    def isFinalizing(self):
        return self.inFinalize

    def finalize(self):
        if not self.isDirty():
            return

        self.inFinalize = 1

        SCObject.finalize(self)

        visibleMembers = []
        for member in self:
            if member.isViewable():
                visibleMembers.append(member)
                member.reparentTo(self)
            else:
                member.reparentTo(hidden)
                if self.activeMember is member:
                    self.__setActiveMember(None)

        maxWidth = 0.0
        maxHeight = 0.0
        for member in visibleMembers:
            width, height = member.getMinDimensions()
            maxWidth = max(maxWidth, width)
            maxHeight = max(maxHeight, height)

        holder = self.getHolder()
        if holder is not None:
            widthToCover = holder.getMinSubmenuWidth()
            maxWidth = max(maxWidth, widthToCover)

        memberWidth, memberHeight = maxWidth, maxHeight
        self.width = maxWidth

        for i in range(len(visibleMembers)):
            member = visibleMembers[i]
            member.setPos(0, 0, -i * maxHeight)
            member.setDimensions(memberWidth, memberHeight)
            member.finalize()

        if len(visibleMembers) > 0:
            z1 = visibleMembers[0].getZ(aspect2d)
            visibleMembers[0].setZ(-maxHeight)
            z2 = visibleMembers[0].getZ(aspect2d)
            visibleMembers[0].setZ(0)

            actualHeight = (z2 - z1) * len(visibleMembers)

            bottomZ = self.getZ(aspect2d) + actualHeight
            if bottomZ < -1.0:
                overlap = bottomZ - (-1.0)
                self.setZ(aspect2d, self.getZ(aspect2d) - overlap)
            if self.getZ(aspect2d) > 1.0:
                self.setZ(aspect2d, 1.0)

        sX = memberWidth
        sZ = memberHeight * len(visibleMembers)
        self.bgMiddle.setScale(sX, 1, sZ)
        self.bgTop.setScale(sX, 1, 1)
        self.bgBottom.setScale(sX, 1, 1)
        self.bgLeft.setScale(1, 1, sZ)
        self.bgRight.setScale(1, 1, sZ)
        self.bgBottomLeft.setZ(-sZ)
        self.bgBottom.setZ(-sZ)
        self.bgTopRight.setX(sX)
        self.bgRight.setX(sX)
        self.bgBottomRight.setX(sX)
        self.bgBottomRight.setZ(-sZ)
        sB = 0.15
        self.bgTopLeft.setSx(aspect2d, sB)
        self.bgTopLeft.setSz(aspect2d, sB)
        self.bgBottomRight.setSx(aspect2d, sB)
        self.bgBottomRight.setSz(aspect2d, sB)
        self.bgBottomLeft.setSx(aspect2d, sB)
        self.bgBottomLeft.setSz(aspect2d, sB)
        self.bgTopRight.setSx(aspect2d, sB)
        self.bgTopRight.setSz(aspect2d, sB)
        self.bgTop.setSz(aspect2d, sB)
        self.bgBottom.setSz(aspect2d, sB)
        self.bgLeft.setSx(aspect2d, sB)
        self.bgRight.setSx(aspect2d, sB)

        r, g, b = self.getColorScheme().getFrameColor()
        a = self.getColorScheme().getAlpha()
        self.bg.setColorScale(r, g, b, a)

        if self.activeMember is not None:
            self.activeMember.reparentTo(self)

        self.validate()

        self.inFinalize = 0

    def append(self, element):
        if isinstance(self.__members, tuple):
            self.__members = list(self.__members)
        self.__members.append(element)
        self.privMemberListChanged(added=[element])

    def extend(self, elements):
        self += elements

    def index(self, element):
        return self.__members.index(element)

    def __len__(self):
        return len(self.__members)

    def __getitem__(self, index):
        return self.__members[index]

    def __setitem__(self, index, value):
        if isinstance(self.__members, tuple):
            self.__members = list(self.__members)
        removedMember = self.__members[index]
        self.__members[index] = value
        self.privMemberListChanged(added=list(value), removed=removedMember)

    def __delitem__(self, index):
        if isinstance(self.__members, tuple):
            self.__members = list(self.__members)
        removedMember = self.__members[index]
        del self.__members[index]
        self.privMemberListChanged(removed=[removedMember])

    def __getslice__(self, i, j):
        if isinstance(self.__members, tuple):
            self.__members = list(self.__members)
        return self.__members[i:j]

    def __setslice__(self, i, j, s):
        if isinstance(self.__members, tuple):
            self.__members = list(self.__members)
        removedMembers = self.__members[i:j]
        self.__members[i:j] = list(s)
        self.privMemberListChanged(added=list(s), removed=removedMembers)

    def __delslice__(self, i, j):
        if isinstance(self.__members, tuple):
            self.__members = list(self.__members)
        removedMembers = self.__members[i:j]
        del self.__members[i:j]
        self.privMemberListChanged(removed=removedMembers)

    def __iadd__(self, other):
        if isinstance(self.__members, tuple):
            self.__members = list(self.__members)
        if isinstance(other, SCMenu):
            otherMenu = other
            other = otherMenu.__members
            del otherMenu[:]
        self.__members += list(other)
        self.privMemberListChanged(added=list(other))
        return self

    def privMemberListChanged(self, added=None, removed=None):
        assert added or removed

        if removed is not None:
            for element in removed:
                if element is self.activeMember:
                    self.__setActiveMember(None)
                if element.getParentMenu() is self:
                    if element.isVisible():
                        element.exitVisible()
                    element.setParentMenu(None)
                    element.reparentTo(hidden)

        if added is not None:
            for element in added:
                self.privAdoptSCObject(element)
                element.setParentMenu(self)

        if self.holder is not None:
            self.holder.updateViewability()

        for i in range(len(self.__members)):
            self.__members[i].posInParentMenu = i

        self.invalidate()

    def privSetSettingsRef(self, settingsRef):
        SCObject.privSetSettingsRef(self, settingsRef)
        for member in self:
            member.privSetSettingsRef(settingsRef)

    def invalidateAll(self):
        SCObject.invalidateAll(self)
        for member in self:
            member.invalidateAll()

    def finalizeAll(self):
        SCObject.finalizeAll(self)
        for member in self:
            member.finalizeAll()

    def getWidth(self):
        return self.width

    def __str__(self):
        return f"{self.__class__.__name__}: menu{self.SerialNum}"
