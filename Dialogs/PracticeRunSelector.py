import tkinter as tk
from Components import PracticeSelectorFrame
from Dialogs import BaseDialog
from Dialogs import Popup

class RunSelector(BaseDialog.Dialog):
    def __init__(self, splitFile, callback):
        super().__init__()
        self.root.title("Choose Split")
        self.callback = callback

        self.content = PracticeSelectorFrame.Frame(
            self.root,
            self.accept,
            splitFile)
        self.content.pack(fill="x")
        self.root.configure(bg="black")
        self.error = None

    def accept(self):
        if not self.content.split:
            if not self.error:
                self.error = tk.Label(self.root,bg="black",fg="white",text="A split must be selected.")
                self.error.pack(fill="x")
            return
        super().accept()
        self.callback(self.retVal)

    def setReturn(self):
        self.retVal["split"] = self.content.split

class SelectorP(Popup.Popup):
    def __init__(self,master,callback,session):
        super().__init__(master,{"accepted": callback})
        self.window.title("Choose Split")

        self.content = PracticeSelectorFrame.Frame(
            self.window,
            self.accept,
            session.splitFile)
        self.content.splitVar.set(session.split)
        self.content.pack(fill="x")

        self.error = None

    def accept(self):
        if not self.content.split:
            if not self.error:
                self.error = tk.Label(self.window,bg="black",fg="white",text="A split must be selected.")
                self.error.pack(fill="x")
            return
        super().accept()

    def setReturn(self):
        self.retVal["split"] = self.content.split
