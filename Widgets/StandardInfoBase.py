from Widgets import InfoBase


class StandardInfoBase(InfoBase.InfoBase):
    def __init__(self, parent, state, config, header):
        super().__init__(parent, state, config)
        self.header.configure(text=header)
        self.resetUI()

    def hide(self):
        self.info.configure(text="")

    def onSplit(self):
        if self.shouldHide():
            self.hide()
        else:
            self.updateInfo()

    def onComparisonChanged(self):
        if self.shouldHide():
            self.hide()
        else:
            self.updateInfo()

    def onRestart(self):
        self.resetUI()

    def resetUI(self):
        self.info.configure(text="")

    def updateInfo(self):
        pass
