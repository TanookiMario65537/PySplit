from Widgets import InfoBase
from util import timeHelpers as timeh


class Widget(InfoBase.InfoBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.resetUI()

    def frameUpdate(self):
        if self.state.runEnded:
            return
        self.updateTime()

    def onRestart(self):
        self.resetUI()

    def resetUI(self):
        self.previousTime = timeh.sumTimeList(
            timeh.stringListToTimes(
                [run["playTime"] for run in self.state.saveData["runs"]]))
        self.header.configure(text="Total Play Time:")
        self.updateTime()

    def updateTime(self):
        self.info.configure(
            text=timeh.timeToString(
                timeh.add(
                    self.state.totalTime,
                    self.previousTime
                ),
                {"precision": self.config["precision"]}
            ))
