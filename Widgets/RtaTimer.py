import tkinter as tk
import datetime
from Widgets import WidgetBase
from util import timeHelpers as timeh


class Widget(WidgetBase.WidgetBase):
    # main = None

    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.configure(
            bg=config["colours"]["bg"],
            padx=state.config["padx"]
        )
        self.main = tk.Label(
            self,
            bg=config["colours"]["bg"],
            fg=config["colours"]["main"],
            font=config["font"]
        )
        m = config["position"]
        if m == "left":
            self.main.grid(row=0, column=0, columnspan=12, sticky="W")
        elif m == "center-left":
            self.main.grid(row=0, column=2, columnspan=10, sticky="W")
        elif m == "center":
            self.main.grid(row=0, column=0, columnspan=12)
        elif m == "center-right":
            self.main.grid(row=0, column=0, columnspan=10, sticky="E")
        elif m == "right":
            self.main.grid(row=0, column=0, columnspan=12, sticky="E")

        self.resetUI()

    def onRestart(self):
        self.resetUI()

    def resetUI(self):
        self.setMainTime(self.currentRtaTime())
        self.main.configure(fg=self.config["colours"]["main"])

    def currentRtaTime(self):
        if not self.state.started:
            realTime = 0
        elif len(self.state.sessionTimes):
            realTime = (
                datetime.datetime.now(datetime.timezone.utc) -
                datetime.datetime.fromisoformat(
                        self.state.sessionTimes[0]["startTime"])
            ).total_seconds()
        else:
            realTime = (
                datetime.datetime.now(datetime.timezone.utc) -
                self.state.staticStartTime
            ).total_seconds()
        return realTime + timeh.stringToTime(self.state.offset)

    def frameUpdate(self):
        if not self.state.runEnded:
            self.setMainTime(self.currentRtaTime())
            self.main.configure(fg=self.timerColour())

    def setMainTime(self, time):
        self.main.configure(
            text=timeh.timeToString(
                time,
                {
                    "blankToDash": False,
                    "precision": self.config["precision"],
                    "showSign": time < 0
                }
            )
        )

    def timerColour(self):
        return self.config["colours"]["main"]
