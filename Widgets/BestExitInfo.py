from Widgets import InfoBase
from util import timeHelpers as timeh

class Widget(InfoBase.InfoBase):
    def __init__(self,parent,state,config):
        super().__init__(parent,state,config)
        self.resetUI()

    def hide(self):
        self.info.configure(text="",fg=self.config["colours"]["text"])

    def onSplit(self):
        if self.shouldHide():
            self.hide()
            return
        self.updateBestExit(self.state.splitnum-1)

    def onComparisonChanged(self):
        if not self.state.splitnum:
            return
        if self.shouldHide():
            self.hide()
        else:
            self.updateBestExit(self.state.splitnum-1)

    def onRestart(self):
        self.resetUI()

    def resetUI(self):
        self.header.configure(text="Best Exit?")
        self.info.configure(text="")

    def updateBestExit(self,splitnum):
        bestExits = self.state.getComparison("generated", "Best Exit")
        if not timeh.greater(bestExits.diffs.totals[splitnum],0)\
            or (timeh.isBlank(bestExits.times.totals[splitnum])
            and not timeh.isBlank(self.state.currentRun.totals[splitnum])):
            self.info.configure(text="Yes",fg=self.config["colours"]["yes"])
        else:
            self.info.configure(text="No",fg=self.config["colours"]["no"])
