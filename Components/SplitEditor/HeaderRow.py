import tkinter as tk
from Components import ValidationEntry as VE
from Components import Notifier


class HeaderRow(tk.Frame, Notifier.Notifier):
    cellWidth = 10
    blankIndex = 4

    def __init__(self, parent, parentObj):
        tk.Frame.__init__(self, parent)
        Notifier.Notifier.__init__(self)
        self.grid = parentObj
        self.connectedNames = {}
        self.bind("<Destroy>", self.unregisterListener)
        self.entries = []
        self.labels = []

    def unregisterListener(self, event):
        if event.widget is self:
            for entry in self.connectedNames.keys():
                entry.removeListener(self)

    def entryChanged(self, changeData):
        """
        validChanged is emitted immediately when VE.Entry is created. In this
        specific instance, the object isn't in self.connectedNames yet, but we
        still want the "validChanged" signal to trickle up to the top level so
        it can check whether the save button should be enabled or not at
        initialization.
        """
        try:
            index = self.connectedNames[changeData["sender"]]["index"]
        except KeyError:
            index = -1
        if changeData["type"] == "textChanged":
            if (
                changeData["data"]
                == self.grid.saveData.data["splitNames"][index]
            ):
                return
            self.grid.saveData.updateComparisonName(
                index,
                changeData["data"]
            )
        elif changeData["type"] == "validChanged":
            self.notifyListeners({
                "type": "validChanged",
                "data": {
                    "valid": changeData["data"],
                    "index": index
                }
            })

    def headers(self):
        return [self.entries[i].val for i in range(len(self.entries))]

    def addHeader(self, text):
        entry = VE.Entry(
            self,
            text,
            {"validate": lambda name: len(name) > 0},
            width=self.cellWidth
        )
        label = tk.Label(
            self,
            text="Totals",
            width=self.cellWidth,
            anchor="e"
        )
        entry.addListener(self, self.entryChanged)
        self.connectedNames[entry] = {"index": len(self.entries)}
        self.columnconfigure(2*len(self.entries), weight=1, minsize=90)
        self.columnconfigure(2*len(self.entries)+1, weight=1, minsize=90)
        entry.grid(row=0, column=2*len(self.entries), sticky="nsew")
        label.grid(row=0, column=2*len(self.entries)+1, sticky="nsew")
        self.entries.append(entry)
        self.labels.append(label)

    def removeHeaders(self, num=1):
        for _ in range(num):
            self.entries[-1].grid_forget()
            self.labels[-1].grid_forget()
            del self.connectedNames[self.entries[-1]]
            del self.entries[-1]
            del self.labels[-1]

    def errorList(self):
        errors = []
        for i, entry in enumerate(self.entries):
            if not entry.isValid:
                errors.append({"type": "header", "index": i})
        return errors

    @property
    def count(self):
        return int(len(self.entries))
