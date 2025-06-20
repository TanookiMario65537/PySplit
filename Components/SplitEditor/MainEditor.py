import tkinter as tk
import copy
from Components.SplitEditor import EntryGrid
from Components import SaveButton
from Components import ValidationEntry as VE
from util import timeHelpers as timeh


class Editor(tk.Frame):
    def __init__(self, master, state):
        super().__init__(master)
        self.saveData = copy.deepcopy(state.saveData)

        self.headerFrame = tk.Frame(self)
        self.headerFrame.pack(side="top", anchor="nw")

        self.offsetFrame = tk.Frame(self.headerFrame)
        self.offsetFrame.pack()

        offsetLabel = tk.Label(self.offsetFrame, text='Offset:')
        self.offsetField = VE.Entry(
            self.offsetFrame,
            self.saveData["offset"],
            {"validate": lambda x: timeh.validTime(x, True)}
        )
        offsetLabel.grid(row=0, column=0, sticky='w')
        self.offsetField.grid(row=0, column=1)

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
            <= len(self.saveData["defaultComparisons"].keys())
        ):
            self.deleteComparisonButton["state"] = "disabled"

        self.saveButton = SaveButton.SaveButton(
            self.buttonFrame,
            {
                "save": self.save,
                "valid": self.validSave,
                "invalidMsg": "Current data is invalid."
            }
        )
        self.saveButton.pack(side="bottom", fill="x")
        self.saveWarning = tk.Label(
            self.buttonFrame,
            text=(
                "Warning: some\n"
                "current values are\n"
                "invalid. For invalid\n"
                "values, the most\n"
                "recent valid value\n"
                "will be saved."
            ),
            fg="orange")

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
            <= len(self.saveData["defaultComparisons"].keys())
        ):
            self.deleteComparisonButton["state"] = "disabled"

    def updateDeleteState(self):
        if (
            not len(self.entries.rows)
            or self.entries.leftFrame.currentSplit < 0
        ):
            self.deleteSplitButton["state"] = "disabled"
        else:
            self.deleteSplitButton["state"] = "active"

    def validSave(self):
        pass

    def save(self, _):
        pass
