import tkinter as tk
from tkinter import ttk
from util import fileio


class Frame(tk.Frame):
    def __init__(self, parent, callback, splitFile):
        super().__init__(parent)
        for i in range(3):
            self.columnconfigure(i, weight=1)

        self.saveData = fileio.readSplitFile(splitFile)
        self.splitVar = tk.StringVar()
        self.splitVar.trace('w', self.setName)
        self.splitCombo = ttk.Combobox(
            self,
            values=self.saveData["splitNames"],
            state="readonly",
            textvariable=self.splitVar)
        splitLabel = tk.Label(self, text="Segment Name:")
        self.split = ""

        confirm = tk.Button(
            self,
            fg="black",
            bg="steel blue",
            text="Confirm Selection",
            command=callback)

        self.splitCombo.grid(row=0, column=1, columnspan=2, sticky="WE")
        splitLabel.grid(row=0, column=0, sticky="W")
        confirm.grid(row=1, column=0, columnspan=3, sticky="WE")

    def setName(self, *_):
        self.split = self.splitVar.get()

    def updateNameCombo(self):
        self.splitCombo["values"] = self.saveData["splitNames"]
