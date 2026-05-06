from Dialogs import Popup
from Components.SplitEditor import CoreSplitEditor


class SplitEditor(Popup.Popup):
    def __init__(self, master, callback, state):
        super().__init__(master, {"accepted": callback})
        self.state = state

        self.editor = CoreSplitEditor.SplitEditor(
            self.window,
            state.saveData,
            {"save": self.save}
        )
        self.editor.pack()

    def close(self, _=None):
        self.state.saveData.removeEdits()
        super().close()

    def save(self):
        self.retVal["saveData"] = self.state.saveData.data
        self.callbacks["accepted"](self.retVal)
