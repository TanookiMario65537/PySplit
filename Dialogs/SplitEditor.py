from Dialogs import Popup
from Components.SplitEditor import MainEditor
from util import fileio
import copy


class SplitEditor(Popup.Popup):
    def __init__(self, master, callback, state):
        super().__init__(master, {"accepted": callback})
        self.state = state

        self.editor = MainEditor.Editor(self.window, state)
        self.editor.pack()
        self.editor.saveButton.options["save"] = self.save
        self.editor.saveButton.options["valid"] = self.validSave

    def validSave(self):
        self.editor.saveWarning.pack_forget()
        check1 = len(self.editor.entries.rows) > 0
        check2 = self.editor.entries.leftFrame.isValid()
        if not check1:
            self.editor.saveButton.options["invalidMsg"] =\
                "This run has no splits."
        elif not check2:
            self.editor.saveButton.options["invalidMsg"] =\
                "All split names\nmust be non-empty."
        elif self.editor.entries.shouldWarn():
            self.editor.saveWarning.pack(side="bottom", fill="both")

        return check1 and check2

    def save(self):
        saveData = copy.deepcopy(self.state.saveData)
        saveData.update(self.editor.entries.generateGrid())
        old = self.editor.entries.oldSplitLocations
        for i, run in enumerate(saveData["runs"]):
            totals = []
            for j in range(len(saveData["splitNames"])):
                if j in old:
                    totals.append(run["totals"][old.index(j)])
                else:
                    totals.append("-")
            saveData["runs"][i]["totals"] = totals
        self.retVal = saveData
        fileio.writeSplitFile(
            self.state.splitFile,
            saveData)
        self.callbacks["accepted"](self.retVal)
