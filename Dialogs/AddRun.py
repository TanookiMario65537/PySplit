import tkinter as tk
from Dialogs import BaseDialog
from Dialogs import Popup
from Components.SplitEditor import CoreSplitEditor
from DataClasses import SaveData


class SplitEditorP(Popup.Popup):
    def __init__(self, master, callback):
        super().__init__(
            master,
            {"accepted": callback},
            closeAction="accepted"
        )
        self.saveData = SaveData.SaveData("")
        self.editFrame = CoreSplitEditor.SplitEditor(
            self.window,
            self.saveData,
            {"save": self.save}
        )
        self.editFrame.pack(fill="both")

    def close(self, _=None):
        self.state.saveData.removeEdits()
        super().close()

    def setReturn(self):
        self.retVal["splitFile"] = self.editFrame.saveData.splitFile

    def save(self):
        self.setReturn()
        self.callbacks["accepted"](self.retVal)


class SplitEditorD(BaseDialog.Dialog):
    def __init__(self):
        super().__init__()
        self.saveData = SaveData.SaveData("")
        self.editFrame = CoreSplitEditor.SplitEditor(
            self.root,
            self.saveData,
            {"save": self.preSave}
        )
        self.editFrame.pack(side="bottom", fill="both")
        self.editFrame.editor.saveButton.options["save"] = self.preSave
        self.root.protocol("WM_DELETE_WINDOW", self.preFinish)
        self.warning = None
        self.note = None
        self.saved = False

    def setReturn(self):
        self.retVal["splitFile"] = self.saveData.splitFile

    def preFinish(self):
        if not self.saved:
            if not self.warning:
                self.warning = tk.Label(
                    self.root,
                    text="A run must be saved before the window is closed",
                    fg="red"
                )
                self.warning.pack(side="top")
            return
        self.finish()

    def preSave(self, *_):
        self.saved = True
        if not self.note:
            self.note = tk.Label(
                self.root,
                text="To start the run, close this window.",
                fg="green"
            )
            self.note.pack()
        if self.warning:
            self.warning.pack_forget()
            self.warning = None
