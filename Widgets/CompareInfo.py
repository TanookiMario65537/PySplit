from Widgets import InfoBase


class Widget(InfoBase.InfoBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.resetUI()

    def resetUI(self):
        self.header.configure(text="Comparing Against:")
        self.info.configure(text=self.state.currentComparison.title)

    def onComparisonChanged(self):
        self.resetUI()
