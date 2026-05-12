import tkinter as tk
from Components.SplitEditor import EntryRow
from Components.SplitEditor import HeaderRow
from Components.SplitEditor import LeftFrame
from Components import ScrollableFrame
from Components import Notifier
from util import timeHelpers as timeh


class EntryGrid(ScrollableFrame.ScrollableFramePin, Notifier.Notifier):
    def __init__(self, parent, saveData, parentObj):
        ScrollableFrame.ScrollableFramePin.__init__(
            self,
            parent,
            width=600,
            height=300
        )
        Notifier.Notifier.__init__(self)
        self.saveData = saveData
        self.saveData.addListener(self, self.saveDataUpdated)
        self.bind("<Destroy>", self.unregisterListener)
        self.editor = parentObj

        self.rightFrame = tk.Frame(self.main())
        self.rightFrame.pack(side="left", fill="y")

        self.cornerLabel = tk.Label(
            self.corner(),
            text="Split Names"
        )
        self.cornerLabel.pack(
            side="right",
            fill="both"
        )

        self.rows = []
        self.comparisons = []
        self.rowLayout = []
        self.connectedRows = {}

    def unregisterListener(self, event):
        if event.widget is self:
            self.saveData.removeListener(self)

    def insertPinnedX(self, *_):
        self.headerRow = HeaderRow.HeaderRow(self.pinnedY(), self)
        self.headerRow.addListener(self, self.headerUpdated)
        self.headerRow.pack(side="top", fill="both")

    def insertPinnedY(self, *_):
        self.leftFrame = LeftFrame.LeftFrame(self.pinnedX(), self)
        self.leftFrame.addListener(self, self.leftFrameUpdated)
        self.leftFrame.pack(side="left", fill="both")

    def insertFollowup(self):
        self.saveDataUpdated({"type": "init"})

    def headerUpdated(self, changeData):
        if changeData["type"] == "validChanged":
            self.notifyListeners({
                "type": "validChanged",
                "data": {
                    "location": "header",
                    "index": changeData["data"]["index"]
                }
            })

    def leftFrameUpdated(self, changeData):
        if changeData["type"] == "validChanged":
            self.notifyListeners({
                "type": "validChanged",
                "data": {
                    "location": "names",
                    "index": changeData["data"]["index"]
                }
            })

    def rowUpdated(self, changeData):
        index = self.connectedRows[changeData["sender"]]["index"]
        if changeData["type"] == "validChanged":
            self.notifyListeners({
                "type": "validChanged",
                "data": {
                    "location": "times",
                    "column": changeData["data"]["index"],
                    "row": index
                }
            })

    def saveDataUpdated(self, changeData):
        # Get the list of editable comparisons
        self.comparisons = (
            self.saveData.defaultComparisons(self.saveData.data)
            + self.saveData.customComparisons(self.saveData.data)
        )

        # Make sure each row has the correct number of columns
        if (
            changeData["type"]
            in ["comparisonAdded", "comparisonRemoved", "init"]
        ):
            while self.headerRow.count < len(self.comparisons):
                self.headerRow.addHeader(
                    self.comparisons[self.headerRow.count].title
                )
            while self.headerRow.count > len(self.comparisons):
                self.headerRow.removeHeaders()
            for row in self.rows:
                while len(row.pairs) < len(self.comparisons):
                    row.addComparison()
                while len(row.pairs) > len(self.comparisons):
                    row.removeComparison()

        if changeData["type"] == "comparisonAdded":
            self.updateAllCellData()

        # Make sure there are the right number of rows
        if (
            changeData["type"]
            in ["splitAdded", "splitRemoved", "init", "subrunChanged"]
        ):
            self.updateRowLayout()
            self.updateAllCellData()

    def updateAllCellData(self):
        for i in range(len(self.rows)):
            for j, cmp in enumerate(self.comparisons):
                self.rows[i].updateEntry(j, cmp.times.segments[i])
                self.rows[i].updateLabel(j, cmp.times.totals[i])

    def computeRowLayout(self):
        """
        The grid has two types of rows - "empty" and "data". Empty rows are
        exactly as they sound. They have no content, and the height is forced
        to match the height of the rows in the grid that actually show
        something (the data rows). Each data row includes the split index for
        the data it should show - its index in the list is the row in which it
        will be shown.

        The grid shows empty rows beside the split name for a subrun, and data
        rows everywhere else.
        """
        newRowLayout = []
        lastSubrun = None
        currentSubrun = None
        for i, split in enumerate(self.saveData.splits):
            currentSubrun = (
                split.subrunPath[0]
                if split.subrunPath
                else None
            )
            if (
                (lastSubrun != currentSubrun)
                and (currentSubrun is not None)
            ):
                newRowLayout.append(("empty", -1))
            newRowLayout.append(("data", i))
            lastSubrun = currentSubrun
        return newRowLayout

    def updateRowLayout(self):
        newRowLayout = self.computeRowLayout()

        """
        For any rows in the new layout that also existed in the old layout,
        make sure that the correct rows are in the correct places. Do nothing
        for empty rows, as the only thing they need is to ensure the row height
        is correct - they don't actually have a frame.
        """
        for i in range(min(len(newRowLayout), len(self.rowLayout))):
            # Check if something changed.
            if (
                (newRowLayout[i][0] != self.rowLayout[i][0])
                or (newRowLayout[i][1] != self.rowLayout[i][1])
            ):
                if newRowLayout[i][1] >= len(self.rows):
                    """
                    There wasn't an existing row for this data index. Since all
                    empty rows have a data index of -1, this will only be true
                    for data rows.
                    """
                    self.addRow(i, newRowLayout[i][0])
                elif newRowLayout[i][0] == "data":
                    """
                    If there was already a data row at the right index, but it
                    was in a different visual position, move it to the correct
                    position.
                    """
                    self.moveRow(i, newRowLayout[i])

        """
        Make sure that every data row we need in the new row layout has been
        created.
        """
        i = len(self.rowLayout)
        while i < len(newRowLayout):
            if newRowLayout[i][1] >= len(self.rows):
                self.addRow(i, newRowLayout[i][0])
            elif newRowLayout[i][0] == "data":
                self.moveRow(i, newRowLayout[i])
            i += 1

        """
        Remove any rows that aren't necessary. The last row in newRowLayout
        will always be a data row, and the index it points to is the number of
        data rows we should have.
        """
        i = len(self.rows) - 1
        while len(newRowLayout) and (i > newRowLayout[-1][1]):
            self.removeRow()
            i -= 1

        self.adjustRowHeights(len(self.rowLayout), len(newRowLayout))
        self.rowLayout = newRowLayout

    def adjustRowHeights(self, oldSize, newSize):
        """
        Make sure all the rows have the correct height. This ensures that even
        the empty rows (which have no frame at all) take up the appropriate
        amount of space.
        """
        for i in range(newSize):
            if self.rightFrame.rowconfigure(i)["minsize"] != 25:
                self.rightFrame.rowconfigure(i, weight=1, minsize=25)
        for i in range(newSize, max(newSize, oldSize)):
            if self.rightFrame.rowconfigure(i)["minsize"] != 0:
                self.rightFrame.rowconfigure(i, weight=1, minsize=0)

    def addRow(self, rowIndex, rowType):
        if rowType != "data":
            return
        self.rows.append(
            EntryRow.EntryRow(self.rightFrame, self, len(self.comparisons))
        )
        self.connectedRows[self.rows[-1]] = {"index": len(self.rows) - 1}
        self.rows[-1].addListener(self, self.rowUpdated)
        self.rows[-1].grid(row=rowIndex, column=0, sticky="nswe")
        self.notifyListeners({
            "type": "validChanged",
            "data": {
                "location": "grid",
                "count": 0
            }
        })

    def moveRow(self, rowIndex, rowInfo):
        row = self.rows[rowInfo[1]]
        row.grid_forget()
        row.grid(
            row=rowIndex,
            column=0,
            sticky="nswe"
        )

    def removeRow(self):
        self.rows[-1].grid_forget()
        del self.connectedRows[self.rows[-1]]
        del self.rows[-1]

    def addSplit(self):
        index = self.leftFrame.currentSplit
        if index < 0:
            index = len(self.rows)
        self.saveData.addSplit(index)

    def removeSplit(self):
        index = self.leftFrame.currentSplit
        if index < 0:
            return
        self.saveData.removeSplit(index)

    def addComparison(self):
        self.saveData.addComparison()

    def removeComparison(self):
        self.saveData.removeComparison()

    def updateComparisonValue(self, row, comparison, time):
        self.comparisons[comparison].times.update(
            timeh.stringToTime(time),
            self.rows.index(row),
            "segment")
        self.saveData.updateComparison(
            row,
            comparison,
            self.comparisons[comparison]
        )

    def errorList(self):
        errors = []
        if (
            not hasattr(self, "headerRow")
            or not hasattr(self, "leftFrame")
            or not hasattr(self, "rows")
        ):
            return [{"type": "init"}]
        errors.extend(self.headerRow.errorList())
        errors.extend(self.leftFrame.errorList())
        if not len(self.rows):
            errors.append({"type": "length"})
        for i, row in enumerate(self.rows):
            errors.extend([
                {**error, **{"row": i}}
                for j, error in enumerate(row.errorList())
            ])
        return errors
