from Widgets import InfoBase
from util import timeHelpers as timeh

class Widget(InfoBase.InfoBase):
    def __init__(self,parent,state,config):
        super().__init__(parent,state,config)
        self.resetUI()

    def hide(self):
        self.info.configure(text="-")

    def frameUpdate(self):
        if self.state.runEnded:
            return
        if self.shouldHide():
            self.hide()
            return
        bestSegments = self.state.getComparison("default", "bestSegments")
        if not timeh.greater(bestSegments.segments[self.state.splitnum],self.state.segmentTime):
            self.info.configure(
                text=timeh.timeToString(
                    timeh.add(
                        timeh.difference(self.state.segmentTime, bestSegments.segments[self.state.splitnum]),
                        self.state.bptList.total
                    ),
                    {"precision": self.config["precision"]}
                ))

    def onSplit(self):
        self.updateTime()

    def onRestart(self):
        self.resetUI()

    def resetUI(self):
        self.header.configure(text="Best Possible Time:")
        self.updateTime()

    def onComparisonChanged(self):
        self.updateTime()

    def updateTime(self):
        if self.shouldHide():
            self.hide()
            return
        self.info.configure(\
            text=\
                timeh.timeToString(\
                    self.state.bptList.total,\
                    {\
                        "precision": self.config["precision"]\
                    }\
                )\
        )
