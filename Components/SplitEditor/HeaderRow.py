import tkinter as tk
from Components import ValidationEntry as VE


class HeaderRow(tk.Frame):
    cellWidth = 10
    blankIndex = 4

    def __init__(self, parent, headerRow):
        super().__init__(parent)
        self.entries = []
        for i in range(len(headerRow)):
            self.addHeader(headerRow[i])

    def headers(self):
        return [self.entries[i].val for i in range(len(self.entries))]

    def addHeaders(self, newHeaders):
        for header in newHeaders:
            self.addHeader(header)

    def addHeader(self, text):
        entry = VE.Entry(
            self,
            text,
            {"validate": lambda name: name.find(",") < 0},
            width=self.cellWidth
        )
        entry.pack(side="left")
        self.entries.append(entry)

    def removeHeaders(self, num):
        for _ in range(num):
            self.entries[-1].pack_forget()
            del self.entries[-1]
