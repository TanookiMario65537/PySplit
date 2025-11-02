from Widgets import StandardInfoBase
from util import timeHelpers as timeh


class Widget(StandardInfoBase.StandardInfoBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config, "Best Exit?")

    def updateInfo(self):
        splitnum = self.state.splitnum - 1
        bestExits = self.state.getComparison("generated", "Best Exit")
        if (
            not timeh.greater(bestExits.diffs.totals[splitnum], 0)
            or
            (
                timeh.isBlank(bestExits.times.totals[splitnum])
                and not timeh.isBlank(self.state.currentRun.totals[splitnum])
            )
        ):
            self.info.configure(text="Yes", fg=self.config["colours"]["yes"])
        else:
            self.info.configure(text="No", fg=self.config["colours"]["no"])
