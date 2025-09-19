from Widgets import WidgetBase
from Components import SegmentRow
from DataClasses import Splits
from util import timeHelpers as timeh


class Widget(WidgetBase.WidgetBase):
    rows = []
    numRows = 0
    updateFrame = 0

    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.rows = []
        self.trimmedTextCache = {}
        self.resetUI()

    def resetUI(self):
        self.splits = Splits.SplitList(self.state)
        oldNumSplits = len(self.rows)
        self.splits.setVisualConfig(
            self.config["numSplits"],
            self.config["activeSplit"],
            self.config["setOpenOnEnd"]
        )
        self.currentViewSplit = self.state.splitnum
        self.viewMoved = False
        self.splits.updateCurrent(self.currentViewSplit, self.state.splitnum)
        self.numRows = self.splits.visibleSplits

        if oldNumSplits < self.numRows:
            for i in range(oldNumSplits, self.numRows):
                row = SegmentRow.SegmentRow(
                    self,
                    self.config["main"]["colours"]["bg"],
                    self.config["main"]["font"],
                    self.config["main"]["colours"]["text"],
                    self.state.config["padx"]
                )
                row.grid(row=i, column=0, columnspan=12, sticky='NSWE')
                self.rowconfigure(i, weight=1)
                self.rows.append(row)
        elif oldNumSplits > self.numRows:
            for i in range(oldNumSplits-1, self.numRows-1, -1):
                self.rows[i].grid_forget()
                self.rows[i].destroy()
                self.rows.pop(-1)

        self.setAllHeaders()
        self.setAllComparisons()
        self.setHighlight()
        self.rows[-1].setHeader(fg=self.config["endColour"])
        self.rows[-1].setComparison(fg=self.config["endColour"])

    def moveView(self, **kwargs):
        self.currentViewSplit = max(
            min(
                self.currentViewSplit + kwargs["movement"],
                self.state.numSplits - 1
            ),
            0
        )
        self.viewMoved = True
        self.updateCompleteView()
        if self.state.splitnum < self.state.numSplits - 1:
            self.setLastDiff()

    def onRestart(self):
        self.currentViewSplit = 0
        self.viewMoved = False
        self.splits.updateCurrent(self.currentViewSplit, self.state.splitnum)
        self.updateFrame = 0
        self.setAllHeaders()
        self.setAllDiffs()
        self.setAllComparisons()
        self.setHighlight()

    def onResize(self):
        self.trimmedTextCache = {}
        self.setAllHeaders()

    def frameUpdate(self):
        if self.state.paused:
            return
        if not self.state.runEnded:
            self.rows[self.splits.currentSplitIndex].setDiff(
                **self.diffProps()
            )
        if (
            not self.state.runEnded
            and (self.splits.openGroupIndex != -1)
            and (
                self.splits.currentSplits[self.splits.openGroupIndex].start
                <= self.state.splitnum
            )
            and (
                self.splits.currentSplits[self.splits.openGroupIndex].end
                >= self.state.splitnum
            )
        ):
            self.rows[self.splits.openGroupIndex].setDiff(
                **self.groupTimerProps()
            )

    def onSplit(self):
        self.toNextSplit()

    def onSplitSkipped(self):
        self.toNextSplit()

    def onComparisonChanged(self):
        self.setMainHeaders()
        self.setAllDiffs()
        self.setAllComparisons()

    def toNextSplit(self):
        self.currentViewSplit = self.state.splitnum
        self.viewMoved = False
        self.updateCompleteView()

    def updateCompleteView(self):
        self.splits.updateCurrent(self.currentViewSplit, self.state.splitnum)
        self.setHighlight()
        self.setAllHeaders()
        self.setAllDiffs()
        self.setMainComparisons()
        if self.state.runEnded:
            self.setLastComparison()

    def subAdjuster(self, isSub):
        if not isSub:
            return ""
        return "    "

    def setAndCacheHeaderText(self, index, text):
        trimmedText = self.trimmedTextCache.get(text, None)
        if trimmedText is None:
            self.rows[index].setHeaderText(text, False)
            self.trimmedTextCache[text] = self.rows[index].header["text"]
        else:
            self.rows[index].setHeaderText(trimmedText, True)

    def setMainHeaders(self):
        try:
            for i in range(self.numRows-1):
                split = self.splits.currentSplits[i]
                if self.splits.typeChecker.isEmpty(split):
                    self.setAndCacheHeaderText(i, "")
                else:
                    if self.splits.typeChecker.isNormal(split):
                        isSub = split.subsplit
                    else:
                        isSub = False
                    self.setAndCacheHeaderText(
                        i,
                        self.subAdjuster(isSub)+split.name
                    )
        except Exception:
            pass

    def setLastHeader(self):
        try:
            split = self.splits.currentSplits[-1]
            if self.splits.typeChecker.isNormal(split):
                isSub = split.subsplit
            else:
                isSub = False
            self.setAndCacheHeaderText(
                -1,
                self.subAdjuster(isSub)+self.splits.currentSplits[-1].name
            )
        except Exception:
            pass

    def setAllHeaders(self):
        self.setMainHeaders()
        self.setLastHeader()

    def formatDiff(self, time):
        return timeh.timeToString(
            time,
            {
                "showSign": True,
                "precision": self.config["diff"]["precision"],
                "noPrecisionOnMinute":
                    self.config["diff"]["noPrecisionOnMinute"]
            }
        )

    def setMainDiffs(self):
        for i in range(self.numRows-1):
            split = self.splits.currentSplits[i]
            if self.splits.typeChecker.isEmpty(split):
                self.rows[i].setDiff(text="")
            elif self.splits.typeChecker.isGroup(split):
                if (split.end < self.state.splitnum):
                    if split.start > 0:
                        groupChange = timeh.difference(
                            timeh.difference(
                                self.state.currentRun.totals[split.end],
                                self.state.currentRun.totals[split.start-1]
                                if self.state.splitnum > 0
                                else 0
                            ),
                            timeh.difference(
                                self.state.currentComparison
                                    .times.totals[split.end],
                                self.state.currentComparison
                                    .times.totals[split.start-1]
                                if self.state.splitnum > 0
                                else 0
                            )
                        )
                        if timeh.isBlank(groupChange):
                            diffColour = (
                                self.config["diff"]
                                ["colours"]["skipped"]
                            )
                        else:
                            diffColour = self.getCurrentDiffColour(
                                groupChange,
                                self.state.currentComparison
                                    .diffs.totals[split.end]
                            )
                    else:
                        diffColour = self.getCurrentDiffColour(
                            timeh.blank(),
                            self.state.currentComparison
                                .diffs.totals[split.end]
                        )
                    self.rows[i].setDiff(
                        text=self.formatDiff(
                            groupChange
                            if split.end >= self.currentViewSplit
                            and split.start <= self.currentViewSplit
                            else self.state.currentComparison
                                .diffs.totals[split.end]
                        ),
                        fg=diffColour
                    )
                elif split.start < self.state.splitnum:
                    self.rows[i].setDiff(**self.groupTimerProps())
                else:
                    self.rows[i].setDiff(text="")
            else:
                if (split.index < self.state.splitnum):
                    self.rows[i].setDiff(
                        text=self.formatDiff(
                            self.state.currentComparison
                                .diffs.totals[split.index]
                        ),
                        fg=self.findDiffColour(split.index)
                    )
                elif (split.index == self.state.splitnum):
                    self.rows[i].setDiff(**self.diffProps())
                else:
                    self.rows[i].setDiff(text="")

    def setLastDiff(self):
        if self.splits.currentSplitIndex == self.numRows-1:
            self.rows[-1].setDiff(**self.diffProps())
        elif self.state.runEnded:
            self.rows[-1].setDiff(
                text=self.formatDiff(
                    self.state.currentComparison
                    .diffs.totals[-1]
                ),
                fg=self.findDiffColour(-1)
            )
        else:
            self.rows[-1].setDiff(text="")

    def setAllDiffs(self):
        self.setMainDiffs()
        self.setLastDiff()

    def formatComparison(self, time):
        return timeh.timeToString(
            time,
            {
                "precision": self.config["main"]["precision"],
                "noPrecisionOnMinute":
                    self.config["main"]["noPrecisionOnMinute"]
            }
        )

    def groupTimerProps(self):
        split = self.splits.currentSplits[self.splits.openGroupIndex]
        return {
            "text": self.formatComparison(
                timeh.difference(
                    self.state.totalTime,
                    self.state.currentRun.totals[split.start-1]
                    if split.start > 0
                    else 0
                )
            ),
            "fg": "grey"
        }

    def setMainComparisons(self):
        for i in range(self.numRows-1):
            split = self.splits.currentSplits[i]

            if self.splits.typeChecker.isEmpty(split):
                self.rows[i].setComparison(text="")

            elif self.splits.typeChecker.isGroup(split):
                totalList = (
                    self.state.currentRun.totals
                    if split.end < self.state.splitnum
                    else self.state.currentComparison.times.totals
                )
                if (split.end < self.currentViewSplit):
                    self.rows[i].setComparison(
                        text=self.formatComparison(totalList[split.end])
                    )
                elif split.start <= self.currentViewSplit:
                    startTime = (
                        totalList[split.start-1] if split.start > 0 else 0
                    )
                    self.rows[i].setComparison(
                        text=self.formatComparison(
                            totalList[split.end] - startTime
                        )
                    )
                else:
                    self.rows[i].setComparison(
                        text=self.formatComparison(totalList[split.end])
                    )
            else:
                if (split.index < self.state.splitnum):
                    self.rows[i].setComparison(
                        text=self.formatComparison(
                            self.state.currentRun.totals[split.index]
                        )
                    )
                else:
                    self.rows[i].setComparison(
                        text=self.formatComparison(
                            self.state.currentComparison
                                .times.totals[split.index]
                        )
                    )

    def setLastComparison(self):
        if self.state.runEnded:
            self.rows[-1].setComparison(
                text=timeh.timeToString(
                    self.state.currentRun.totals[-1],
                    {
                        "precision": self.config["main"]["precision"],
                        "noPrecisionOnMinute":
                            self.config["main"]["noPrecisionOnMinute"]
                    }
                )
            )
        else:
            self.rows[-1].setComparison(
                text=timeh.timeToString(
                    self.state.currentComparison.times.totals[-1],
                    {
                        "precision": self.config["main"]["precision"],
                        "noPrecisionOnMinute":
                            self.config["main"]["noPrecisionOnMinute"]
                    }
                )
            )

    def setAllComparisons(self):
        self.setMainComparisons()
        self.setLastComparison()

    def diffProps(self):
        if (
            not self.state.runEnded
            and (
                not timeh.greater(
                    self.state.currentComparison.times
                        .totals[self.state.splitnum],
                    self.state.totalTime
                )
                or not timeh.greater(
                    self.state.getComparison("default", "bestSegments")
                        .times.segments[self.state.splitnum],
                    self.state.segmentTime
                )
            )
            and (self.splits.currentSplitIndex > -1)
        ):
            return {
                "text": timeh.timeToString(
                    timeh.difference(
                        self.state.totalTime,
                        self.state.currentComparison
                            .times.totals[self.state.splitnum]
                    ),
                    {
                        "showSign": True,
                        "precision": self.config["diff"]["precision"],
                        "noPrecisionOnMinute":
                            self.config["diff"]["noPrecisionOnMinute"]
                    }
                ),
                "fg": self.getCurrentDiffColour(
                    timeh.difference(
                        self.state.segmentTime,
                        self.state.currentComparison
                            .times.segments[self.state.splitnum]
                    ),
                    timeh.difference(
                        self.state.totalTime,
                        self.state.currentComparison
                            .times.totals[self.state.splitnum]
                    )
                )
            }
        return {
            "text": ""
        }

    def getCurrentDiffColour(self, segmentDiff, totalDiff):
        if timeh.greater(0, totalDiff):
            # if comparison segment is blank or current segment is
            # ahead
            if timeh.greater(0, segmentDiff):
                return self.config["diff"]["colours"]["aheadGaining"]
            else:
                return self.config["diff"]["colours"]["aheadLosing"]
        else:
            # if comparison segment is blank or current segment is
            # behind
            if timeh.greater(segmentDiff, 0):
                return self.config["diff"]["colours"]["behindLosing"]
            else:
                return self.config["diff"]["colours"]["behindGaining"]

    def findDiffColour(self, splitIndex):
        # Either the split in this run is blank, or we're comparing
        # to something that's blank
        bestSegments = self.state.getComparison("default", "bestSegments")
        if (
            timeh.isBlank(self.state.currentRun.totals[splitIndex])
            or timeh.isBlank(
                self.state.currentComparison.times.totals[splitIndex]
            )
        ):
            return self.config["diff"]["colours"]["skipped"]
        # This split is the best ever. Mark it with the gold colour
        elif (
            not timeh.isBlank(bestSegments.diffs.segments[splitIndex])
            and timeh.greater(0, bestSegments.diffs.segments[splitIndex])
        ):
            return self.config["diff"]["colours"]["gold"]
        else:
            return self.getCurrentDiffColour(
                self.state.currentComparison.diffs.segments[splitIndex],
                self.state.currentComparison.diffs.totals[splitIndex]
            )

    def setHighlight(self):
        for i in range(self.numRows):
            self.setBackground(i)
            self.setTextColour(i)

    def setBackground(self, index):
        props = {}
        if index == self.splits.activeIndex and not self.viewMoved:
            props["bg"] = self.config["activeHighlight"]["colours"]["bg"]
        else:
            props["bg"] = self.config["main"]["colours"]["bg"]
        if (
            self.splits.typeChecker.isGroup(self.splits.currentSplits[index])
            and self.splits.currentSplits[index].open
        ):
            props["relief"] = "sunken"
            props["borderwidth"] = 1
            props["highlightthickness"] = 0
            props["highlightbackground"] = self.config["main"]["colours"]["bg"]
        elif index == self.splits.activeIndex and self.viewMoved:
            props["relief"] = "flat"
            props["highlightthickness"] = 2
            props["highlightbackground"] = (
                self.config["activeHighlight"]["colours"]["bg"]
            )
        else:
            props["relief"] = "flat"
            props["borderwidth"] = 0
            props["highlightthickness"] = 0
            props["highlightbackground"] = self.config["main"]["colours"]["bg"]
        self.rows[index].configure(**props)
        self.rows[index].setHeader(bg=props["bg"])
        self.rows[index].setDiff(bg=props["bg"])
        self.rows[index].setComparison(bg=props["bg"])

    def setTextColour(self, index):
        if index == self.splits.activeIndex:
            colour = self.config["activeHighlight"]["colours"]["text"]
        elif index < self.numRows-1:
            colour = self.config["main"]["colours"]["text"]
        else:
            colour = self.config["endColour"]
        self.rows[index].setHeader(fg=colour)
        split = self.splits.currentSplits[index]
        if (
            self.splits.typeChecker.isGroup(split)
            and (split.start <= self.currentViewSplit)
            and (split.end >= self.currentViewSplit)
        ):
            self.rows[index].setComparison(fg="grey")
        else:
            self.rows[index].setComparison(fg=colour)
