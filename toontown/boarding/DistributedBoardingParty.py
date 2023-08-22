from direct.distributed import DistributedObject
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

from toontown.boarding import BoardingGroupInviterPanels, BoardingGroupShow, BoardingPartyBase, GroupInvitee, GroupPanel
from toontown.toonbase import TTLocalizer


class DistributedBoardingParty(DistributedObject.DistributedObject, BoardingPartyBase.BoardingPartyBase):
    notify = directNotify.newCategory("DistributedBoardingParty")

    InvitationFailedTimeout = 60.0

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        BoardingPartyBase.BoardingPartyBase.__init__(self)
        if __debug__:
            base.bparty = self
        self.groupInviteePanel = None
        self.groupPanel = None
        self.inviterPanels = BoardingGroupInviterPanels.BoardingGroupInviterPanels()
        self.lastInvitationFailedMessage = {}
        self.goToPreShowTrack = None
        self.goToShowTrack = None

    def generate(self):
        self.load()
        DistributedObject.DistributedObject.generate(self)
        base.localAvatar.boardingParty = self

    def delete(self):
        DistributedObject.DistributedObject.delete(self)

    def disable(self):
        self.finishGoToPreShowTrack()
        self.finishGoToShowTrack()
        self.forceCleanupInviteePanel()
        self.forceCleanupInviterPanels()
        self.inviterPanels = None
        if self.groupPanel:
            self.groupPanel.cleanup()
        self.groupPanel = None
        DistributedObject.DistributedObject.disable(self)
        BoardingPartyBase.BoardingPartyBase.cleanup(self)
        base.localAvatar.boardingParty = None
        self.lastInvitationFailedMessage = {}

    def getElevatorIdList(self):
        return self.elevatorIdList

    def setElevatorIdList(self, elevatorIdList):
        self.notify.debug("setElevatorIdList")
        self.elevatorIdList = elevatorIdList

    def load(self):
        """
        Load any assets here if required.
        """

    def postGroupInfo(self, leaderId, memberList, inviteeList, kickedList):
        """
        A group has changed so the AI is sending us new information on it
        """
        self.notify.debug("postgroupInfo")
        isMyGroup = 0
        removedMemberIdList = []
        oldGroupEntry = self.groupListDict.get(leaderId, [[], [], []])
        oldMemberList = oldGroupEntry[0]

        newGroupEntry = [memberList, inviteeList, kickedList]
        self.groupListDict[leaderId] = newGroupEntry

        if len(oldMemberList) != len(memberList):
            for oldMember in oldMemberList:
                if oldMember not in memberList and oldMember in self.avIdDict and self.avIdDict[oldMember] == leaderId:
                    self.avIdDict.pop(oldMember)
                    removedMemberIdList.append(oldMember)

        self.avIdDict[leaderId] = leaderId
        if leaderId == base.localAvatar.doId:
            isMyGroup = 1
        for memberId in memberList:
            self.avIdDict[memberId] = leaderId
            if memberId == base.localAvatar.doId:
                isMyGroup = 1

        if (newGroupEntry[0]) == [0] or (not newGroupEntry[0]):
            dgroup = self.groupListDict.pop(leaderId)
            for memberId in dgroup[0]:
                if memberId in self.avIdDict:
                    self.avIdDict.pop(memberId)

        if isMyGroup:
            self.notify.debug("new info posted on my group")
            if not self.groupPanel:
                self.groupPanel = GroupPanel.GroupPanel(self)
            messenger.send("updateGroupStatus")
            for removedMemberId in removedMemberIdList:
                removedMember = base.cr.identifyAvatar(removedMemberId)
                if removedMember:
                    removedMemberName = removedMember.name
                    messageText = TTLocalizer.BoardingMessageLeftGroup % (removedMemberName)
                    base.localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

        elif (base.localAvatar.doId in oldMemberList) and base.localAvatar.doId not in memberList:
            messenger.send("updateGroupStatus")
            if self.groupPanel:
                self.groupPanel.cleanup()
            self.groupPanel = None
        else:
            self.notify.debug("new info posted on some other group")

    def postInvite(self, leaderId, inviterId):
        """
        The AI tells us someone has been invited into a group
        """
        self.notify.debug("post Invite")
        if not base.cr.avatarFriendsManager.checkIgnored(inviterId):
            inviter = base.cr.doId2do.get(inviterId)
            if inviter:
                if self.inviterPanels.isInvitingPanelUp() or self.inviterPanels.isInvitationRejectedPanelUp():
                    self.inviterPanels.forceCleanup()
                self.groupInviteePanel = GroupInvitee.GroupInvitee()
                self.groupInviteePanel.make(self, inviter, leaderId)

    def postKick(self, leaderId):
        self.notify.debug("%s was kicked out of the Boarding Group by %s" % (base.localAvatar.doId, leaderId))
        base.localAvatar.setSystemMessage(0, TTLocalizer.BoardingMessageKickedOut, WhisperPopup.WTToontownBoardingGroup)

    def postSizeReject(self, leaderId, inviterId, inviteeId):
        self.notify.debug("%s was not invited because the group is full" % (inviteeId))

    def postKickReject(self, leaderId, inviterId, inviteeId):
        self.notify.debug("%s was not invited because %s has kicked them from the group" % (inviteeId, leaderId))

    def postInviteDelcined(self, inviteeId):
        self.notify.debug("%s delinced %s's Boarding Group invitation." % (inviteeId, base.localAvatar.doId))
        invitee = base.cr.doId2do.get(inviteeId)
        if invitee:
            self.inviterPanels.createInvitationRejectedPanel(self, inviteeId)

    def postInviteAccepted(self, inviteeId):
        self.notify.debug("%s accepted %s's Boarding Group invitation." % (inviteeId, base.localAvatar.doId))
        if self.inviterPanels.isInvitingPanelIdCorrect(inviteeId):
            self.inviterPanels.destroyInvitingPanel()

    def postInviteCanceled(self):
        self.notify.debug("The invitation to the Boarding Group was cancelled")
        if self.isInviteePanelUp():
            self.groupInviteePanel.cleanup()
            self.groupInviteePanel = None

    def postInviteNotQualify(self, avId, reason, elevatorId):
        messenger.send("updateGroupStatus")
        rejectText = ""

        avatar = base.cr.doId2do.get(avId)
        avatarNameText = avatar.name if avatar else ""
        if reason == BoardingPartyBase.BOARDCODE_PENDING_INVITE:
            rejectText = TTLocalizer.BoardingInviteePendingIvite % (avatarNameText)
        if reason == BoardingPartyBase.BOARDCODE_IN_ELEVATOR:
            rejectText = TTLocalizer.BoardingInviteeInElevator % (avatarNameText)
        if self.inviterPanels.isInvitingPanelIdCorrect(avId) or (avId == base.localAvatar.doId):
            self.inviterPanels.destroyInvitingPanel()
        self.showMe(rejectText)

    def postAlreadyInGroup(self):
        """
        The invitee is already part of a group and cannot accept another invitation.
        """
        self.showMe(TTLocalizer.BoardingAlreadyInGroup)

    def postGroupAlreadyFull(self):
        """
        The invitee cannot accept the invitation because the group is already full.
        """
        self.showMe(TTLocalizer.BoardingGroupAlreadyFull)

    def postSomethingMissing(self):
        """
        The AI determines that something is wrong and this cannot be accepted.
        Eg 1: The leader of the group is not there in the avIdDict.
        """
        self.showMe(TTLocalizer.BoardcodeMissing)

    def postRejectBoard(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        """
        Problem when the leader tried to enter the elevator detected on AI
        """
        self.showRejectMessage(elevatorId, reason, avatarsFailingRequirements, avatarsInBattle)
        self.enableGoButton()

    def postRejectGoto(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        """
        Problem when the leader tried to use a GO Button detected on AI.
        """
        self.showRejectMessage(elevatorId, reason, avatarsFailingRequirements, avatarsInBattle)

    def postMessageInvited(self, inviteeId, inviterId):
        """
        The AI tells all the members (except the inviter) in the Boarding Group that
        the inviter has invited the invitee.
        """
        inviterName = ""
        inviteeName = ""
        inviter = base.cr.doId2do.get(inviterId)
        if inviter:
            inviterName = inviter.name
        invitee = base.cr.doId2do.get(inviteeId)
        if invitee:
            inviteeName = invitee.name
        messageText = TTLocalizer.BoardingMessageInvited % (inviterName, inviteeName)
        base.localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

    def postMessageInvitationFailed(self, inviterId):
        """
        The AI tells the invitee that an inviter had tried to invite him to their
        Boarding Group, but failed for some reason.
        """
        inviterName = ""
        inviter = base.cr.doId2do.get(inviterId)
        if inviter:
            inviterName = inviter.name
        if self.invitationFailedMessageOk(inviterId):
            messageText = TTLocalizer.BoardingMessageInvitationFailed % (inviterName)
            base.localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

    def postMessageAcceptanceFailed(self, inviteeId, reason):
        """
        The AI tells the inviter that the invitee tried to accept the invitation
        because of the following reason.
        """
        inviteeName = ""
        messageText = ""
        invitee = base.cr.doId2do.get(inviteeId)
        if invitee:
            inviteeName = invitee.name

        if reason == BoardingPartyBase.INVITE_ACCEPT_FAIL_GROUP_FULL:
            messageText = TTLocalizer.BoardingMessageGroupFull % inviteeName

        base.localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

        if self.inviterPanels.isInvitingPanelIdCorrect(inviteeId):
            self.inviterPanels.destroyInvitingPanel()

    def invitationFailedMessageOk(self, inviterId):
        """
        Returns True if it is OK to display this message from this inviter.
        Returns False if this message should be suppressed because we just
        recently displaced this message from this inviter.
        This check is added so that the inviter can't spam the invitee.
        """
        now = globalClock.getFrameTime()
        lastTime = self.lastInvitationFailedMessage.get(inviterId, None)
        if lastTime:
            elapsedTime = now - lastTime
            if elapsedTime < self.InvitationFailedTimeout:
                return False

        self.lastInvitationFailedMessage[inviterId] = now
        return True

    def showRejectMessage(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        leaderId = base.localAvatar.doId
        rejectText = ""

        def getAvatarText(avIdList):
            """
            This function takes a list of avIds and returns a string of names.
            If there is only 1 person it returns "avatarOneName"
            If there are 2 people it returns "avatarOneName and avatarTwoName"
            If there are 3 or more people it returns "avatarOneName,  avatarTwoName and avatarThreeName"
            """
            avatarText = ""
            nameList = []
            for avId in avIdList:
                avatar = base.cr.doId2do.get(avId)
                if avatar:
                    nameList.append(avatar.name)
            if len(nameList) > 0:
                lastName = nameList.pop()
                avatarText = lastName
                if len(nameList) > 0:
                    secondLastName = nameList.pop()
                    for name in nameList:
                        avatarText = name + ", "
                    avatarText += secondLastName + " " + TTLocalizer.And + " " + lastName
            return avatarText

        if reason == BoardingPartyBase.BOARDCODE_SPACE:
            self.notify.debug("%s 's group cannot board there was not enough room" % (leaderId))
            rejectText = TTLocalizer.BoardcodeSpace

        elif reason == BoardingPartyBase.BOARDCODE_MISSING:
            self.notify.debug("%s 's group cannot board because something was missing" % (leaderId))
            rejectText = TTLocalizer.BoardcodeMissing
        base.localAvatar.elevatorNotifier.showMeWithoutStopping(rejectText)

    def postGroupDissolve(self, quitterId, leaderId, memberList, kick):
        self.notify.debug("%s group has dissolved" % (leaderId))

        isMyGroup = 0
        if base.localAvatar.doId in (quitterId, leaderId):
            isMyGroup = 1
        if leaderId in self.groupListDict:
            if leaderId == base.localAvatar.doId:
                isMyGroup = 1
                if leaderId in self.avIdDict:
                    self.avIdDict.pop(leaderId)
            self.groupListDict.pop(leaderId)

            for memberId in memberList:
                if memberId == base.localAvatar.doId:
                    isMyGroup = 1
                if memberId in self.avIdDict:
                    self.avIdDict.pop(memberId)

        if isMyGroup:
            self.notify.debug("new info posted on my group")
            messenger.send("updateGroupStatus")
            groupFormed = False
            if self.groupPanel:
                groupFormed = True
                self.groupPanel.cleanup()
            self.groupPanel = None

            if groupFormed:
                if leaderId == quitterId:
                    if base.localAvatar.doId != leaderId:
                        base.localAvatar.setSystemMessage(
                            0, TTLocalizer.BoardingMessageGroupDissolved, WhisperPopup.WTToontownBoardingGroup
                        )
                elif not kick and base.localAvatar.doId != quitterId:
                    quitter = base.cr.doId2do.get(quitterId)
                    if quitter:
                        quitterName = quitter.name
                        messageText = TTLocalizer.BoardingMessageLeftGroup % (quitterName)
                        base.localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)
                    else:
                        messageText = TTLocalizer.BoardingMessageGroupDisbandedGeneric
                        base.localAvatar.setSystemMessage(0, messageText, WhisperPopup.WTToontownBoardingGroup)

    def requestInvite(self, inviteeId):
        self.notify.debug("requestInvite %s" % (inviteeId))
        elevator = base.cr.doId2do.get(self.getElevatorIdList()[0])
        if not elevator:
            return

        if inviteeId in self.getGroupKickList(base.localAvatar.doId) and not self.isGroupLeader(base.localAvatar.doId):
            avatar = base.cr.doId2do.get(inviteeId)
            avatarNameText = avatar.name if avatar else ""
            rejectText = TTLocalizer.BoardingInviteeInKickOutList % (avatarNameText)
            self.showMe(rejectText)
            return

        if self.inviterPanels.isInvitingPanelUp():
            self.showMe(TTLocalizer.BoardingPendingInvite, pos=(0, 0, 0))
        elif len(self.getGroupMemberList(base.localAvatar.doId)) >= self.maxSize:
            self.showMe(TTLocalizer.BoardingInviteGroupFull)
        else:
            invitee = base.cr.doId2do.get(inviteeId)
            if invitee:
                self.inviterPanels.createInvitingPanel(self, inviteeId)
                self.sendUpdate("requestInvite", [inviteeId])

    def requestCancelInvite(self, inviteeId):
        self.sendUpdate("requestCancelInvite", [inviteeId])

    def requestAcceptInvite(self, leaderId, inviterId):
        self.notify.debug("requestAcceptInvite %s %s" % (leaderId, inviterId))
        self.sendUpdate("requestAcceptInvite", [leaderId, inviterId])

    def requestRejectInvite(self, leaderId, inviterId):
        self.sendUpdate("requestRejectInvite", [leaderId, inviterId])

    def requestKick(self, kickId):
        self.sendUpdate("requestKick", [kickId])

    def requestLeave(self):
        if self.goToShowTrack and self.goToShowTrack.isPlaying():
            return

        place = base.cr.playGame.getPlace()
        if place and place.getState() != "elevator" and base.localAvatar.doId in self.avIdDict:
            leaderId = self.avIdDict[base.localAvatar.doId]
            self.sendUpdate("requestLeave", [leaderId])

    def handleEnterElevator(self, elevator):
        """
        If you are the leader of the boarding group, do it the boarding group way.
        We come into this function only if the player is the leader of the boarding group.
        """
        if self.getGroupLeader(base.localAvatar.doId) == base.localAvatar.doId and base.localAvatar.hp > 0:
            self.cr.playGame.getPlace().detectedElevatorCollision(elevator)
            self.sendUpdate("requestBoard", [elevator.doId])
            elevatorId = elevator.doId
            if elevatorId in self.elevatorIdList:
                offset = self.elevatorIdList.index(elevatorId)
                if self.groupPanel:
                    self.groupPanel.scrollToDestination(offset)
                self.informDestChange(offset)
            self.disableGoButton()

    def informDestChange(self, offset):
        """
        This function is called from Group Panel when the leader changes the destination.
        """
        self.sendUpdate("informDestinationInfo", [offset])

    def postDestinationInfo(self, offset):
        """
        The destination has been changed by the leader. Change the GroupPanel of
        this client to reflect the change.
        """
        if self.groupPanel:
            self.groupPanel.changeDestination(offset)

    def enableGoButton(self):
        """
        Enables the GO Button in the Group Panel.
        """
        if self.groupPanel:
            self.groupPanel.enableGoButton()
            self.groupPanel.enableDestinationScrolledList()

    def disableGoButton(self):
        """
        Disables the GO Button in the Group Panel.
        """
        if self.groupPanel:
            self.groupPanel.disableGoButton()
            self.groupPanel.disableDestinationScrolledList()

    def isInviteePanelUp(self):
        """
        Helper function to determine whether any Group Invitee panel is up or not.
        """
        if self.groupInviteePanel:
            if not self.groupInviteePanel.isEmpty():
                return True
            self.groupInviteePanel = None
        return False

    def requestGoToFirstTime(self, elevatorId):
        """
        Request the AI if the leader and all the members can go directly to the elevator destination.
        This is the first request the leader makes to the AI.
        The AI responds back only to the leader with a rejectGoToRequest if anything goes wrong or
        responds back only to the leader with a acceptGoToFirstTime if everything goes well.
        """
        self.waitingForFirstResponse = True
        self.firstRequestAccepted = False
        self.sendUpdate("requestGoToFirstTime", [elevatorId])
        self.startGoToPreShow(elevatorId)

    def acceptGoToFirstTime(self, elevatorId):
        """
        The AI's response back to the leader's first request saying that everybody was accepted.
        Flag this response and use this response flag before we requestGoToSecondTime.
        """
        self.waitingForFirstResponse = False
        self.firstRequestAccepted = True

    def requestGoToSecondTime(self, elevatorId):
        """
        Request the AI if the leader and all the members can go directly to the elevator destination.
        This is the first request the leader makes to the AI.
        The AI responds back only to the leader with a rejectGoToRequest if anything goes wrong or
        responds back to all the members with a acceptGoToSecondTime if everything goes well.
        """
        if not self.waitingForFirstResponse:
            if self.firstRequestAccepted:
                self.firstRequestAccepted = False
                self.disableGoButton()
                self.sendUpdate("requestGoToSecondTime", [elevatorId])
        else:
            self.postRejectGoto(elevatorId, BoardingPartyBase.BOARDCODE_MISSING, [], [])
            self.cancelGoToElvatorDest()

    def acceptGoToSecondTime(self, elevatorId):
        """
        The AI's response to all the members of the group that everybody was accepted to
        Go directly to the elevator destination.
        Now all the members can start the GoToShow.
        """
        self.startGoToShow(elevatorId)

    def rejectGoToRequest(self, elevatorId, reason, avatarsFailingRequirements, avatarsInBattle):
        """
        The AI's response back to the leader's first request saying that something went wrong.
        Now the leader should stop GoToPreShow.
        """
        self.firstRequestAccepted = False
        self.waitingForFirstResponse = False
        self.cancelGoToElvatorDest()
        self.postRejectGoto(elevatorId, reason, avatarsFailingRequirements, avatarsInBattle)

    def startGoToPreShow(self, elevatorId):
        """
        This is where the first 3 seconds of GO Pre show happens only on the leader's client.
        GO Button becomes Cancel GO Button and the leader can't move.
        """
        self.notify.debug("Starting Go Pre Show.")

        place = base.cr.playGame.getPlace()
        if place:
            place.setState("stopped")

        goButtonPreShow = BoardingGroupShow.BoardingGroupShow(base.localAvatar)
        goButtonPreShowTrack = goButtonPreShow.getGoButtonPreShow()

        if self.groupPanel:
            self.groupPanel.changeGoToCancel()
            self.groupPanel.disableQuitButton()
            self.groupPanel.disableDestinationScrolledList()

        self.finishGoToPreShowTrack()
        self.goToPreShowTrack = Sequence()
        self.goToPreShowTrack.append(goButtonPreShowTrack)
        self.goToPreShowTrack.append(Func(self.requestGoToSecondTime, elevatorId))
        self.goToPreShowTrack.start()

    def finishGoToPreShowTrack(self):
        """
        Finish the goToPreShowTrack, if it is still going on.
        """
        if self.goToPreShowTrack:
            self.goToPreShowTrack.finish()
            self.goToPreShowTrack = None

    def startGoToShow(self, elevatorId):
        """
        This is where the 3 seconds of GO show happens. This is essentially the teleport track
        and then the client is taken to the elevator destination.
        """
        self.notify.debug("Starting Go Show.")

        base.localAvatar.boardingParty.forceCleanupInviterPanels()

        elevatorName = self.__getDestName(elevatorId)
        if self.groupPanel:
            self.groupPanel.disableQuitButton()
        goButtonShow = BoardingGroupShow.BoardingGroupShow(base.localAvatar)

        place = base.cr.playGame.getPlace()
        if place:
            place.setState("stopped")

        self.goToShowTrack = goButtonShow.getGoButtonShow(elevatorName)
        self.goToShowTrack.start()

    def finishGoToShowTrack(self):
        """
        Finish the goToShowTrack, if it is still going on.
        """
        if self.goToShowTrack:
            self.goToShowTrack.finish()
            self.goToShowTrack = None

    def cancelGoToElvatorDest(self):
        """
        The leader has decided to Cancel going to the elevator destination
        using the Cancel Go Button.
        """
        self.notify.debug("%s cancelled the GoTo Button." % (base.localAvatar.doId))
        self.firstRequestAccepted = False
        self.waitingForFirstResponse = False
        self.finishGoToPreShowTrack()
        place = base.cr.playGame.getPlace()
        if place:
            place.setState("walk")
        if self.groupPanel:
            self.groupPanel.changeCancelToGo()
            self.groupPanel.enableGoButton()
            self.groupPanel.enableQuitButton()
            self.groupPanel.enableDestinationScrolledList()

    def __getDestName(self, elevatorId):
        elevator = base.cr.doId2do.get(elevatorId)
        destName = ""
        if elevator:
            destName = elevator.getDestName()
        return destName

    def showMe(self, message, pos=None):
        """
        Making a version of elevatorNotifier.showMe. This version doesn't put the toon
        into stopped state while displaying the panel. At the same time, the OK button
        in the panel doesn't put the toon in the walk state.
        """
        base.localAvatar.elevatorNotifier.showMeWithoutStopping(message, pos)

    def forceCleanupInviteePanel(self):
        """
        Forcibly close the group invitee panel, with a reject as the default answer.
        """
        if self.isInviteePanelUp():
            self.groupInviteePanel.forceCleanup()
            self.groupInviteePanel = None

    def forceCleanupInviterPanels(self):
        """
        Forcibly cleanup the inviter panels, with a reject as the default answer.
        """
        if self.inviterPanels:
            self.inviterPanels.forceCleanup()
