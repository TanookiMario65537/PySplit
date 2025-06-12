import tkinter as tk
from util import timeHelpers as timeh
from Widgets import WidgetBase


class Widget(WidgetBase.WidgetBase):
    # game = None
    # category = None
    # sessions = None
    # completion = None

    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        bg = config["colours"]["bg"]
        font = config["font"]
        textColour = config["colours"]["text"]

        self.configure(bg=bg)
        self.game = tk.Label(self, bg=bg, font=font, fg=textColour)
        self.category = tk.Label(self, bg=bg, font=font, fg=textColour)
        self.sessions = tk.Label(self, bg=bg, font=font, fg=textColour)
        self.completion = tk.Label(self, bg=bg, font=font, fg=textColour)

        self.game.grid(row=0, column=0, columnspan=12, sticky='WE')
        self.category.grid(row=1, column=0, columnspan=12, sticky='WE')
        self.completion.grid(
            row=1,
            column=10,
            columnspan=2,
            sticky='E',
            ipadx=10
        )
        self.sessions.grid(
            row=0,
            column=10,
            columnspan=2,
            sticky='E',
            ipadx=10
        )

        self.resetUI()

    def resetUI(self):
        self.game.configure(text=self.state.game)
        self.category.configure(text=self.state.category)
        self.setSessions()
        self.setAttemptCounter()

    def onSplit(self):
        self.setSessions()
        self.setAttemptCounter()

    def onReset(self):
        self.setSessions()
        self.setAttemptCounter()

    def setSessions(self):
        if not self.config["showSessions"]:
            return
        if len(self.state.sessionTimes):
            self.sessions.configure(
                text="Session "+str(len(self.state.sessionTimes)+1)
            )
        else:
            self.sessions.configure(text="")

    def setAttemptCounter(self):
        text = ""
        if not self.config["showAttempts"]:
            return
        if self.config["showCompletions"]:
            text += str(
                len(
                    [
                        run
                        for run in self.state.saveData["runs"]
                        if not timeh.isBlank(
                            timeh.stringToTime(run["totals"][-1])
                        )
                    ]
                )
            )+"/"
        text += str(len(self.state.saveData["runs"]))
        self.completion.configure(text=text)
