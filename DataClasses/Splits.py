import copy

class SplitList:
    def __init__(self,state):
        self.splits, self.groups = self.parseSplits(state.splitnames)
        self.visibleSplits = 0
        self.visuallyActive = 0
        self.numSplits = len(state.splitnames)
        self.typeChecker = TypeChecker()
        self.currentSplits = []
        self.activeIndex = 0
        self.state = state
        self.setOpenOnEnd = True

    def parseSplits(self,names):
        """
        Parses all the splits and split groups from the list of split names.
        """
        splits = []
        groups = []
        groupStart = -1
        for i in range(len(names)):
            if names[i][0:2] == "- ":
                truename = names[i][2:]
                if groupStart < 0:
                    groupStart = i
                if "{" in names[i] and "}" in names[i]:
                    groups.append(SplitGroup(groupStart,i,names[i].split("{")[1].split("}")[0]))
                    truename = truename.split("{")[0]
                    groupStart = -1
                splits.append(Split(i,truename,True))
            else:
                splits.append(Split(i,names[i]))
                groupStart = -1
        return splits, groups

    def setVisualConfig(self,numSplits,visuallyActive,setOpenOnEnd):
        """
        Sets information needed for choosing how many splits to show, the ideal
        location for the current split, and whether to leave the current group
        open at the end.
        """
        self.visibleSplits = numSplits
        self.visuallyActive = visuallyActive
        self.setOpenOnEnd = setOpenOnEnd

    def updateCurrent(self,currentSplit):
        """
        Updates the current split list and the index of the current active
        split. The split list is a mix of SplitGroups, Splits, and EmptySplits.

        Parameters:
            currentSplit - The index of the current split

        Returns:
            None
        """
        self.setOpen(currentSplit)
        if currentSplit == self.numSplits and len(self.groups) and self.groups[-1].end == self.numSplits - 1:
            if self.setOpenOnEnd:
                group = copy.deepcopy(self.groups[-1])
            else:
                group = None
        else:
            group = copy.deepcopy(self.findGroup(currentSplit))
        subs = []
        if group:
            subs = self.splits[group.start:group.end+1]
        available = self.synthesizeSplits(subs)
        if currentSplit == self.numSplits:
            self.activeIndex = self.numSplits
            if group and group.count >= self.visibleSplits:
                self.currentSplits = [group] + available[len(available)-self.visibleSplits+1:]
            else:
                self.currentSplits = available[len(available)-self.visibleSplits:]
        else:
            availableIndex = self.findSplit(available,currentSplit)
            topSplitIndex = self.trueTopSplitIndex(availableIndex,len(available))
            if group:
                groupIndex = self.groupIndex(available,group)
                if groupIndex < topSplitIndex:
                    subActiveIndex = self.visuallyActive
                    if subActiveIndex > self.visibleSplits/2:
                        subActiveIndex = subActiveIndex - 1
                    count = group.count
                    if self.groupIndex(self.groups,group) == len(self.groups) - 1:
                        count = count - 1
                    subTopIndex = self.subTopIndex(\
                        availableIndex-groupIndex,\
                        count,
                        self.visibleSplits-2,\
                        subActiveIndex\
                    )
                    self.activeIndex = availableIndex - (groupIndex + subTopIndex - 1)
                    self.currentSplits = [group] + available[groupIndex+subTopIndex:groupIndex+subTopIndex+self.visibleSplits-1] + [available[-1]]
                    return
            self.activeIndex = availableIndex - topSplitIndex
            self.currentSplits = available[topSplitIndex:topSplitIndex+self.visibleSplits-1] + [available[-1]]

    def findGroup(self,index):
        """
        Finds the SplitGroup at the given index.

        Returns:
            The SplitGroup if the split at the given index is in a group.
            None otherwise.
        """
        for group in self.groups:
            if group.start <= index and group.end >= index:
                return group
        return None

    def findSplit(self,available,index):
        """
        Finds the index of the given split in the list of available splits.

        Parameters:
            available - The list of available splits.
            index - The index of the current split.

        Returns:
            The index of the current split within the available splits.
        """
        for i in range(len(available)):
            split = available[i]
            if not self.typeChecker.isNormal(split):
                continue
            if split.index == index:
                return i
        return -1

    def groupIndex(self,available,group):
        """
        Finds the index of a group in the list of available splits.

        Parameters:
            available - The list of available splits.
            group - The group.

        Returns:
            The index of the group in the list of splits. -1 if the group is not
            in the list.
        """
        for i in range(len(available)):
            split = available[i]
            if not self.typeChecker.isGroup(split):
                continue
            if split.start == group.start:
                return i
        return -1

    def setOpen(self,index):
        """
        Sets the group at the given index to be open and all other groups to be
        closed. If there is no group at this index, all groups will be set to
        closed.
        """
        for group in self.groups:
            if group.start <= index and group.end >= index:
                group.open = True
            else:
                group.open = False

    def synthesizeSplits(self,openSubsplits):
        """
        Adds the open subsplits to the top level splits to generate a list of
        possibly visible splits. Fills out empty splits if there is more space
        than there are splits.

        Parameters:
            openSubsplits - The list of splits in the currently open group.

        Returns:
            A list of splits, including all the top level splits plus the given
            open subsplits in the appropriate location after their associated
            group split and before the next one. Empty splits are filled in if
            necessary.
        """
        topLevel = self.getTopLevelSplits()
        if not len(openSubsplits):
            while len(topLevel) < self.visibleSplits:
                topLevel.insert(len(topLevel)-1,EmptySplit())
            return topLevel

        i = 0
        while i < len(topLevel) and len(openSubsplits):
            split = topLevel[i]
            if self.typeChecker.isNormal(split):
                if openSubsplits[0].index < split.index:
                    topLevel.insert(i,copy.deepcopy(openSubsplits.pop(0)))
            elif self.typeChecker.isGroup(split):
                if openSubsplits[0].index < split.start:
                    topLevel.insert(i,copy.deepcopy(openSubsplits.pop(0)))
            i = i + 1
        topLevel = topLevel + copy.deepcopy(openSubsplits)
        while len(topLevel) < self.visibleSplits:
            topLevel.insert(len(topLevel)-1,EmptySplit())
        return topLevel

    def getTopLevelSplits(self):
        """
        Get the splits at the top level. Top level splits are SplitGroups and
        splits that exist outside a group.

        Returns:
            The list of top level splits.
        """
        topLevel = []
        i = 0
        while i < len(self.splits):
            group = copy.deepcopy(self.findGroup(i))
            if group:
                topLevel.append(group)
                i = group.end
            else:
                topLevel.append(copy.deepcopy(self.splits[i]))
            i = i + 1
        return topLevel

    def trueTopSplitIndex(self,current,available):
        """
        Determines the index of the split that should be at the top of the
        window.

        Parameters:
            current - The current split index within the available splits
                (returned by trueTopSplitIndex).
            available - The list of available splits.

        Returns:
            The index that should be at the top of the window.
        """
        return self.subTopIndex(
            current,
            available,
            self.visibleSplits,
            self.visuallyActive)

    def subTopIndex(self,current,available,visible,visuallyActive):
        """
        Determines the index of the split that should be at the top of the
        window, given an explicit number of visible splits and the index of the
        currently active one.

        Parameters:
            current - The current split index within the available splits
                (returned by trueTopSplitIndex).
            available - The list of available splits.
            visible - The number of visible splits.
            visuallyActive - The ideal location of the current split within the
                window.

        Returns:
            The index that should be at the top of the window.
        """
        if current <= visuallyActive - 1:
            return 0
        elif current >= available - (visible-visuallyActive):
            return available - (visible - 1)
        else:
            return current - (visuallyActive - 1)

    def __str__(self):
        string = ""
        for split in self.splits:
            string = string + str(split) + "\n"
        for group in self.groups:
            string = string + str(group) + "\n"
        return string

class Split:
    def __init__(self,index,name,isSub=False):
        self.index = index
        self.name = name
        self.subsplit = isSub

    def __str__(self):
        return "Name: " + self.name + " | Index: " + str(self.index)

class SplitGroup:
    def __init__(self,start,end,name):
        self.start = start
        self.end = end
        self.name = name
        self.count = end - start + 1
        self.open = False

    def __str__(self):
        return "Name: " + self.name + " | Indexes: " + str(self.start) + "-" + str(self.end) + " | Open: " + str(self.open)

class EmptySplit:
    def __init__(self):
        pass

    def __str__(self):
        return "Empty split"

class TypeChecker():
    def __init__(self):
        pass

    def isNormal(self,obj):
        return type(obj) == Split

    def isGroup(self,obj):
        return type(obj) == SplitGroup

    def isEmpty(self,obj):
        return type(obj) == EmptySplit
