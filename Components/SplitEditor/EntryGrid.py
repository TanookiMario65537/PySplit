import tkinter as tk
from Components.SplitEditor import EntryRow
from Components.SplitEditor import HeaderRow
from Components.SplitEditor import LeftFrame
from Components import ScrollableFrame
from DataClasses import SyncedTimeList as STL
from util import timeHelpers as timeh


class EntryGrid(ScrollableFrame.ScrollableFramePin):
    def __init__(self, parent, saveData, parentObj):
        super().__init__(parent, width=600, height=300)
        self.editor = parentObj
        self.defaultComparisonOrder = list(
            saveData["defaultComparisons"].keys())
        self.splitNames = saveData["splitNames"]
        self.oldSplitLocations = list(range(len(saveData["splitNames"])))

        self.rightFrame = tk.Frame(self.main())
        self.rightFrame.pack(side="left", fill="y")
        self.headers = []
        for key in self.defaultComparisonOrder:
            self.headers.extend([
                saveData["defaultComparisons"][key]["name"],
                saveData["defaultComparisons"][key]["name"] + " Totals"
            ])
        for cmp in saveData["customComparisons"]:
            self.headers.extend([
                cmp["name"],
                cmp["name"] + " Totals"
            ])

        self.cornerLabel = tk.Label(
            self.corner(),
            text="Split Names")
        self.cornerLabel.pack(
            side="right",
            fill="both")

        self.rows = []
        self.originals = list(range(len(saveData["splitNames"])))
        self.comparisons = []
        for key in self.defaultComparisonOrder:
            saveKey = list(saveData["defaultComparisons"][key].keys())[1]
            initData = {}
            initData[saveKey] = saveData["defaultComparisons"][key][saveKey]
            self.comparisons.append(STL.SyncedTimeList(**initData))
        self.comparisons.extend([STL.SyncedTimeList(totals=cmp["totals"]) for cmp in saveData["customComparisons"]])
        for i in range(len(saveData["splitNames"])):
            cmpRow = []
            for cmp in self.comparisons:
                cmpRow.extend([
                    timeh.timeToString(cmp.segments[i]),
                    timeh.timeToString(cmp.totals[i])
                ])
            row = EntryRow.EntryRow(
                self.rightFrame,
                self,
                cmpRow)
            row.pack(
                side="top",
                fill="both")
            self.rows.append(row)

    def shouldWarn(self):
        return any([row.shouldWarn() for row in self.rows])\
            or self.leftFrame.shouldWarn()

    def splitUpdated(self):
        self.editor.updateDeleteState()

    def insertPinnedX(self, *_):
        self.headerRow = HeaderRow.HeaderRow(self.pinnedY(), self.headers)
        self.headerRow.pack(side="top", fill="both")

    def insertPinnedY(self, *_):
        self.leftFrame = LeftFrame.LeftFrame(
            self.pinnedX(),
            self.splitNames,
            self)
        self.leftFrame.pack(side="left", fill="both")

    def addSplit(self):
        index = self.leftFrame.currentSplit
        if index < 0:
            index = len(self.rows)

        for i in range(len(self.oldSplitLocations)):
            if self.oldSplitLocations[i] is None:
                continue
            if self.oldSplitLocations[i] >= index:
                self.oldSplitLocations[i] += 1

        self.leftFrame.addSplit(index)
        newComparisons = []
        for comparison in self.comparisons:
            comparison.insert(timeh.blank(), index, "total")
            newComparisons.extend([
                '-',
                timeh.timeToString(comparison.totals[index])
            ])
        self.rows.insert(
            index,
            EntryRow.EntryRow(self.rightFrame, self, newComparisons))

        for i in range(index+1, len(self.rows)):
            self.rows[i].pack_forget()
        for i in range(index, len(self.rows)):
            self.rows[i].pack(side="top", fill="both")
        for i in range(len(self.originals)):
            if self.originals[i] >= index:
                self.originals[i] = self.originals[i] + 1

    def removeSplit(self):
        currentSplit = self.leftFrame.currentSplit
        if currentSplit < 0:
            return

        for i in range(len(self.oldSplitLocations)):
            if self.oldSplitLocations[i] is None:
                continue
            if self.oldSplitLocations[i] > currentSplit:
                self.oldSplitLocations[i] += -1
            elif self.oldSplitLocations[i] == currentSplit:
                self.oldSplitLocations[i] = None

        self.leftFrame.removeSplit()
        self.rows[currentSplit].pack_forget()
        del self.rows[currentSplit]
        for comparison in range(len(self.comparisons)):
            self.comparisons[comparison].remove(currentSplit, "total")
            self.updateComparison(comparison, ["entry"])

        for i in range(len(self.originals)):
            if self.originals[i] > currentSplit:
                self.originals[i] = self.originals[i] - 1
            elif self.originals[i] == currentSplit:
                self.originals[i] = -1

    def addComparison(self):
        self.headerRow.addHeaders(["New Comparison", "New Comparison Totals"])
        for row in self.rows:
            row.addComparison()
        self.comparisons.append(STL.SyncedTimeList(totals=[timeh.blank() for _ in self.rows]))

    def removeComparison(self):
        if len(self.comparisons) <= len(self.defaultComparisonOrder):
            return
        del self.comparisons[-1]
        self.headerRow.removeHeaders(2)
        for row in self.rows:
            row.removeComparison(1)

    def updateComparisonValue(self, row, comparison, time):
        self.comparisons[comparison].update(
            self.rows.index(row),
            timeh.stringToTime(time),
            "segment")
        self.updateComparison(comparison, ["label"])

    def updateComparison(self, comparison, columns=[]):
        for i in range(len(self.rows)):
            if "label" in columns:
                self.rows[i].updateLabel(
                    comparison,
                    self.comparisons[comparison].totals[i])
            if "entry" in columns:
                self.rows[i].updateEntry(
                    comparison,
                    self.comparisons[comparison].segments[i])

    def createBestSegmentSave(self, comparison):
        return {
            "name": self.headerRow.headers()[2*comparison],
            "segments": timeh.timesToStringList(
                self.comparisons[comparison].segments)
        }

    def createComparisonSave(self, comparison):
        return {
            "name": self.headerRow.headers()[2*comparison],
            "totals": timeh.timesToStringList(
                self.comparisons[comparison].totals)
        }

    def generateGrid(self):
        newSaveData = {
            "defaultComparisons": {},
            "customComparisons": [],
            "splitNames": []
        }
        for i in range(len(self.defaultComparisonOrder)):
            key = self.defaultComparisonOrder[i]
            newSaveData["defaultComparisons"][key] = self.createBestSegmentSave(i) if key == "bestSegments" else self.createComparisonSave(i)
        for i in range(len(self.defaultComparisonOrder), len(self.comparisons)):
            newSaveData["customComparisons"].append(
                self.createComparisonSave(i))
        newSaveData["splitNames"] = self.leftFrame.splitNames()
        return newSaveData
