import tkinter as tk
from Components import LayoutSelector
from Dialogs import BaseDialog
from Dialogs import Popup


class LayoutDialog(BaseDialog.Dialog):
    layoutVar = None
    session = None

    def __init__(self, callback, session):
        super().__init__()
        self.callback = callback
        self.session = session

        self.layouts = LayoutSelector.Selector(self.root)
        self.layouts.pack()
        self.retVal["layoutName"] = self.session.layoutName
        self.layouts.layoutVar.set(self.session.layoutName)

        confirm = tk.Button(
            self.root,
            fg="black",
            bg="steel blue",
            text="Confirm Selection",
            command=self.accept)
        confirm.pack(fill="x")

    def accept(self):
        super().accept()
        self.callback(self.retVal)

    def setReturn(self):
        self.retVal["layoutName"] = self.layouts.layoutName


class LayoutPopup(Popup.Popup):
    layoutVar = None
    session = None

    def __init__(self,master,callback,session):
        super().__init__(master,{"accepted": callback})
        self.session = session

        self.window.configure(bg="black")
        self.window.title("Choose Layout")

        self.layouts = LayoutSelector.Selector(self.window)
        self.layouts.pack()
        self.retVal["layoutName"] = self.session.layoutName
        self.layouts.layoutVar.set(self.session.layoutName)

        confirm = tk.Button(self.window,fg="black",bg="steel blue",text="Confirm Selection",command=self.accept)
        confirm.pack(fill="x")

    def setReturn(self):
        self.retVal["layoutName"] = self.layouts.layoutName
