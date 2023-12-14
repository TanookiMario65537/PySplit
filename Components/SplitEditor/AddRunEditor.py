import tkinter as tk
import os
from Components.SplitEditor import EntryGrid
from Components.SplitEditor import MainEditor
from Dialogs import fileDialogs
from States import State
from util import fileio
from util import readConfig as rc

class SplitEditor(tk.Frame):
    def __init__(self,master):
        super().__init__(master)
        self.config = rc.getUserConfig()
        self.splitFile = ""

        selection = tk.Frame(self)
        for i in range(3):
            selection.columnconfigure(i, weight=1)

        self.gameVar = tk.StringVar()
        self.gameVar.trace('w', self.setGame)
        gameLabel = tk.Label(selection, text='Game:')
        gameEntry = tk.Entry(selection, textvariable=self.gameVar)

        self.cateVar = tk.StringVar()
        self.cateVar.trace('w', self.setCategory)
        cateLabel = tk.Label(selection, text='Category:')
        cateEntry = tk.Entry(selection, textvariable=self.cateVar)

        gameLabel.grid(row=0, column=0, sticky='w')
        gameEntry.grid(row=0, column=1)
        cateLabel.grid(row=1, column=0, sticky='w')
        cateEntry.grid(row=1, column=1)
        selection.pack(side="top", anchor='w')

        self.editor = MainEditor.Editor(
            self,
            State.State(""))
        self.editor.pack(side="bottom")
        self.editor.saveButton.options["save"] = self.save
        self.editor.saveButton.options["valid"] = self.validSave
        self.localEntries = EntryGrid.EntryGrid(self.editor, fileio.newComparisons(),self.editor) 

        self.savedGame = ""
        self.savedCategory = ""

    def setGame(self, *_):
        self.game = self.gameVar.get()

    def setCategory(self, *_):
        self.category = self.cateVar.get()

    def hasSaved(self,game,category):
        return game == self.savedGame and category == self.savedCategory

    def validSave(self):
        self.editor.saveWarning.pack_forget()
        check1 = self.game and self.category
        check2 = self.editor.entries.leftFrame.isValid()
        check3 = len(self.editor.entries.rows) > 0
        if not check1:
            self.editor.saveButton.options["invalidMsg"] = "Runs must have a\nnon-empty game and\ncategory."
        elif not check2:
            self.editor.saveButton.options["invalidMsg"] = "All split names\nmust be non-empty."
        elif not check3:
            self.editor.saveButton.options["invalidMsg"] = "This run has no splits."
        elif self.editor.entries.shouldWarn():
            self.editor.saveWarning.pack(side="bottom",fill="both")

        return check1 and check2 and check3

    def save(self):
        game = self.game
        category = self.category
        saveData = self.editor.entries.generateGrid()
        saveData["version"] = "1.1"
        saveData["game"] = game
        saveData["category"] = category
        saveData["runs"] = []
        defaultFile = os.path.join(
            self.config["baseDir"],
            game,
            category + ".pysplit")
        self.splitFile = fileDialogs.addNewRun(self.config, defaultFile)
        if not self.splitFile:
            return
        fileio.writeSplitFile(
            self.splitFile,
            saveData)
        self.savedGame = game
        self.savedCategory = category
