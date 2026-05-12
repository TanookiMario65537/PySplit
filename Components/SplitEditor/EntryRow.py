import tkinter as tk
from Components import ValidationEntry as VE
from Components import Notifier
from util import timeHelpers as timeh


class EntryRow(tk.Frame, Notifier.Notifier):
    cellWidth = 10

    def __init__(self, parent, parentObj, comparisonCount):
        tk.Frame.__init__(self, parent)
        Notifier.Notifier.__init__(self)
        self.parent = parentObj
        self.connectedNames = {}
        self.pairs = []
        for i in range(comparisonCount):
            self.addComparison()

    def generalPair(self, index, times):
        return [
            VE.Entry(
                self,
                timeh.trimTime(times[0]),
                {
                    "validate": lambda time: timeh.validTime(time),
                    "followup": lambda time, timeIndex=index: (
                        self.parent.updateComparisonValue(
                            self,
                            timeIndex,
                            time
                        )
                    )
                },
                width=self.cellWidth,
                justify="right"
            ),
            tk.Label(
                self,
                text=timeh.trimTime(times[1]),
                width=self.cellWidth,
                anchor="e"
            )
        ]

    def blankPair(self, times):
        return [
            tk.Label(
                self,
                text=timeh.trimTime(times[0]),
                width=self.cellWidth,
                anchor="e"
            ),
            tk.Label(
                self,
                text=timeh.trimTime(times[1]),
                width=self.cellWidth,
                anchor="e"
            )
        ]

    def updateEntry(self, index, time):
        self.pairs[index][0].setText(
            timeh.timeToString(time, {"precision": 2})
        )

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
        if changeData["type"] == "validChanged":
            self.notifyListeners({
                "type": "validChanged",
                "data": {
                    "valid": changeData["data"],
                    "index": index
                }
            })

    def addComparison(self):
        pair = self.generalPair(len(self.pairs), ['-', '-'])
        i = self.columnIndex(len(self.pairs))
        self.columnconfigure(i, weight=1, minsize=90)
        self.columnconfigure(i+1, weight=1, minsize=90)
        pair[0].grid(row=0, column=i, sticky="nsew")
        pair[1].grid(row=0, column=i+1, sticky="nsew")
        pair[0].addListener(self, self.entryChanged)
        self.connectedNames[pair[0]] = {"index": len(self.pairs)}
        self.pairs.append(pair)

    def removeComparison(self):
        self.pairs[-1][0].grid_forget()
        self.pairs[-1][1].grid_forget()
        del self.connectedNames[self.pairs[-1][0]]
        del self.pairs[-1]

    def updateLabel(self, index, time):
        self.pairs[index][1]["text"] = (
            timeh.timeToString(time, {"precision": 2})
        )

    def columnIndex(self, index):
        return 2*index

    def comparisonIndex(self, index):
        return int(index/2)

    def errorList(self):
        errors = []
        for i, pair in enumerate(self.pairs):
            if not pair[0].isValid:
                errors.append({"type": "comparison", "column": i})
        return errors
