from Widgets import InfoBase
from util import timeHelpers as timeh


class Widget(InfoBase.InfoBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.resetUI()

    def resetUI(self):
        self.header.configure(text="Personal Best:")
        self.setInfo()

    def onSplit(self):
        if self.state.runEnded:
            self.setInfo(new=self.state.isPB())

    def setInfo(self, new=False):
        if new:
            time = (
                self.state.currentRun
                .totals[self.state.currentRun.lastNonBlank()]
            )
        else:
            time = (
                self.state.getComparison("default", "bestRun")
                    .times.totals[-1]
            )
        self.info.configure(
            text=timeh.timeToString(
                time,
                {"precision": self.config["precision"]}
            )
        )
