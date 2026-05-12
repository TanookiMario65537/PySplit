import tkinter as tk
from Components.SplitEditor import EntryGrid
from Components import SaveButton
from Components import ValidationEntry as VE
from util import timeHelpers as timeh


class Editor(tk.Frame):
    def __init__(self, master, saveData):
        super().__init__(master)
        self.saveData = saveData

        self.headerFrame = tk.Frame(self)
        self.headerFrame.pack(side="top", anchor="nw")

        self.offsetFrame = tk.Frame(self.headerFrame)
        self.offsetFrame.pack()

        gameLabel = tk.Label(self.offsetFrame, text='Game:')
        self.gameEntry = VE.Entry(
            self.offsetFrame,
            self.saveData.data["game"],
            {"validate": lambda x: x != ""}
        )

        cateLabel = tk.Label(self.offsetFrame, text='Category:')
        self.cateEntry = VE.Entry(
            self.offsetFrame,
            self.saveData.data["category"],
            {"validate": lambda x: x != ""}
        )

        gameLabel.grid(row=0, column=0, sticky='w')
        self.gameEntry.grid(row=0, column=1)
        self.gameEntry.addListener(self, self.updateGame)
        cateLabel.grid(row=1, column=0, sticky='w')
        self.cateEntry.grid(row=1, column=1)
        self.cateEntry.addListener(self, self.updateCategory)

        offsetLabel = tk.Label(self.offsetFrame, text='Offset:')
        self.offsetField = VE.Entry(
            self.offsetFrame,
            self.saveData.data["offset"],
            {"validate": lambda x: timeh.validTime(x, True)}
        )
        offsetLabel.grid(row=2, column=0, sticky='w')
        self.offsetField.grid(row=2, column=1)
        self.offsetField.addListener(self, self.updateOffset)
        self.bind("<Destroy>", self.unregisterListener)

        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(side="right", fill="y")

        self.entries = EntryGrid.EntryGrid(self, self.saveData, self)
        self.entries.pack(side="left")

        self.addSplitButton = tk.Button(
            self.buttonFrame,
            text="Add Split",
            command=self.addSplit
        )
        self.addSplitButton.pack(fill="x")

        self.deleteSplitButton = tk.Button(
            self.buttonFrame,
            text="Delete Split",
            command=self.deleteSplit,
            state="disabled"
        )
        self.deleteSplitButton.pack(fill="x")

        self.addComparisonButton = tk.Button(
            self.buttonFrame,
            text="Add Comparison",
            command=self.addComparison
        )
        self.addComparisonButton.pack(fill="x")

        self.deleteComparisonButton = tk.Button(
            self.buttonFrame,
            text="Delete Comparison",
            command=self.deleteComparison
        )
        self.deleteComparisonButton.pack(fill="x")
        if (
            len(self.entries.comparisons)
            <= len(self.saveData.data["defaultComparisons"].keys())
        ):
            self.deleteComparisonButton["state"] = "disabled"

        self.saveAsButton = SaveButton.SaveButton(
            self.buttonFrame,
            {
                "text": "Save As",
                "save": self.saveAs,
            }
        )
        self.saveButton = SaveButton.SaveButton(
            self.buttonFrame,
            {
                "save": self.save,
            }
        )
        self.saveButton.pack(side="bottom", fill="x")
        self.saveAsButton.pack(side="bottom", fill="x")

    def unregisterListener(self, event):
        if event.widget is self:
            self.offsetField.removeListener(self)
            self.gameEntry.removeListener(self)
            self.cateEntry.removeListener(self)

    def errorList(self):
        errors = []
        if not self.gameEntry.isValid:
            errors.append({"type": "game"})
        if not self.cateEntry.isValid:
            errors.append({"type": "category"})
        if not self.offsetField.isValid:
            errors.append({"type": "offset"})
        errors.extend(self.entries.errorList())
        return errors

    def getOffset(self):
        return self.offsetField.getText()

    def addSplit(self, _=None):
        self.entries.addSplit()
        self.deleteSplitButton["state"] = "active"

    def deleteSplit(self, _=None):
        self.entries.removeSplit()
        self.updateDeleteState()

    def addComparison(self, _=None):
        self.entries.addComparison()
        self.deleteComparisonButton["state"] = "active"

    def deleteComparison(self, _=None):
        self.entries.removeComparison()
        if (
            len(self.entries.comparisons)
            <= len(self.saveData.data["defaultComparisons"].keys())
        ):
            self.deleteComparisonButton["state"] = "disabled"

    def updateGame(self, changeData):
        if changeData["type"] == "textChanged":
            self.saveData.updateGame(changeData["data"])

    def updateCategory(self, changeData):
        if changeData["type"] == "textChanged":
            self.saveData.updateCategory(changeData["data"])

    def updateOffset(self, changeData):
        if changeData["type"] == "textChanged":
            self.saveData.updateOffset(changeData["data"])

    def updateDeleteState(self):
        if (
            not len(self.entries.rows)
            or self.entries.leftFrame.currentSplit < 0
        ):
            self.deleteSplitButton["state"] = "disabled"
        else:
            self.deleteSplitButton["state"] = "active"

    def saveAs(self, _):
        self.save()

    def save(self, _):
        pass
