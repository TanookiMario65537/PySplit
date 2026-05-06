import tkinter as tk
from pathlib import Path
from Dialogs import fileDialogs
from util import readConfig as rc
from Components.SplitEditor import MainEditor


class SplitEditor(tk.Frame):
    def __init__(self, master, saveData, callbacks={}):
        super().__init__(master)
        self.config = rc.getUserConfig()

        self.saveData = saveData
        self.editor = MainEditor.Editor(
            self,
            self.saveData
        )
        self.editor.pack(side="bottom")
        self.editor.saveButton.options["save"] = self.save
        self.editor.saveAsButton.options["save"] = self.saveAs

        self.editor.offsetField.addListener(self, self.updateValid)
        self.editor.gameEntry.addListener(self, self.updateValid)
        self.editor.cateEntry.addListener(self, self.updateValid)
        self.editor.entries.addListener(self, self.updateValid)

        self.callbacks = callbacks

    def unregisterListeners(self, event):
        if event.widget is not self:
            return
        self.editor.offsetField.removeListener(self)
        self.editor.gameEntry.removeListener(self)
        self.editor.cateEntry.removeListener(self)

    def updateValid(self, changeData):
        if changeData["type"] != "validChanged":
            return
        errorList = self.editor.errorList()
        if len(errorList):
            self.editor.saveButton.button["state"] = "disabled"
            self.editor.saveAsButton.button["state"] = "disabled"
        else:
            if not self.saveData.splitFile:
                self.editor.saveButton.button["state"] = "disabled"
            else:
                self.editor.saveButton.button["state"] = "active"
            self.editor.saveAsButton.button["state"] = "active"

    def saveAs(self):
        defaultFile = (
            Path(self.config["baseDir"])
            / self.saveData.data["game"]
            / (self.saveData.data["category"] + ".pysplit")
        )
        splitFile = fileDialogs.chooseSaveFile(self.config, defaultFile)
        if not splitFile:
            return
        if self.saveData.containsSubRun(splitFile):
            fileDialogs.resursionWarning()
            return
        self.saveData.setSplitFile(splitFile)
        self.save()

    def save(self):
        self.saveData.save()
        if self.callbacks.get("save", None) is not None:
            self.callbacks.get("save", None)()
