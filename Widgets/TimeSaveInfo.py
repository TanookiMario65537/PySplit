from Widgets import InfoBase
from util import timeHelpers as timeh


class Widget(InfoBase.InfoBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.resetUI()

    def resetUI(self):
        self.header.configure(text="Possible Time Save:")
        self.setInfo()

    def hide(self):
        self.info.configure(text="-")

    def onRestart(self):
        self.updateIfNecessary()

    def onSplit(self):
        self.updateIfNecessary()

    def onComparisonChanged(self):
        self.updateIfNecessary()

    def onSplitSkipped(self):
        self.updateIfNecessary()

    def updateIfNecessary(self):
        if self.state.runEnded:
            return
        if self.shouldHide():
            self.hide()
            return
        self.setInfo()

    def setInfo(self):
        self.info.configure(
            text=timeh.timeToString(
                timeh.difference(
                    self.state.currentComparison
                        .times.segments[self.state.splitnum],
                    self.state.getComparison("default", "bestSegments")
                        .times.segments[self.state.splitnum]
                ),
                {
                    "precision": self.config["precision"],
                    "noPrecisionOnMinute": self.config["noPrecisionOnMinute"]
                }
            ))
