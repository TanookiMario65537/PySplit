import tkinter as tk
from Components import Notifier


class Entry(tk.Entry, Notifier.Notifier):
    def __init__(self, parent, val, cbs, **kwargs):
        tk.Entry.__init__(self, parent, **kwargs)
        Notifier.Notifier.__init__(self)
        self.followup = None
        self.isValid = False
        self.listeners = {}
        self.var = tk.StringVar(self, val)
        self["textvariable"] = self.var
        self.trace = self.var.trace('w', self.doValidation)
        self.val = val
        self.validate = cbs["validate"]
        self.doValidation()
        if "followup" in cbs.keys():
            self.followup = cbs["followup"]

    def addListener(self, listener, callback):
        """
        Add to the function here so that the grid parent can update it's
        validity as soon as it connects.
        """
        super().addListener(listener, callback)
        callback({
            "sender": self,
            "type": "validChanged",
            "data": self.isValid,
        })

    def doValidation(self, *_):
        val = self.var.get()
        oldValid = self.isValid
        if self.validate(val):
            self.val = val
            self.isValid = True
            self.notifyListeners({
                "type": "textChanged",
                "data": self.val
            })
            self["bg"] = "white"
            if not oldValid:
                self.notifyListeners({
                    "type": "validChanged",
                    "data": self.isValid
                })
            if self.followup:
                self.followup(val)
        else:
            self["bg"] = "#ff6666"
            self.isValid = False
            if oldValid:
                self.notifyListeners({
                    "type": "validChanged",
                    "data": self.isValid
                })

    def getText(self):
        return self.var.get()

    def setText(self, text, validate=False):
        self.val = text
        if not validate:
            self.var.trace_vdelete("w", self.trace)
        self.var.set(text)
        if not validate:
            self.trace = self.var.trace('w', self.doValidation)
