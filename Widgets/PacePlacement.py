from Widgets import StandardInfoBase
from util import timeHelpers as timeh


class Widget(StandardInfoBase.StandardInfoBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config, "Pace Placement")

    def onStarted(self):
        self.updateInfo()

    def ordinal(self, n: int):
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix

    def updateInfo(self):
        paceComparisons = []
        splitnum = max([
            i if not timeh.isBlank(self.state.currentRun.totals[i]) else -1
            for i in range(self.state.saveData.count)
        ])
        for i, run in enumerate(self.state.saveData.data["runs"]):
            if splitnum == -1:
                paceComparisons.append(False)
            else:
                time = timeh.stringToTime(run["totals"][splitnum])
                if timeh.isBlank(time):
                    continue
                paceComparisons.append(
                    timeh.greater(
                        self.state.currentRun.totals[splitnum],
                        time
                    )
                )
        self.info.configure(
            text=f"{self.ordinal(len([p for p in paceComparisons if p])+1)}"
            f" of {len(paceComparisons)+1}"
        )
