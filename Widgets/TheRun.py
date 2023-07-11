from Widgets import WidgetBase
import datetime
import requests


class TheRun(WidgetBase.WidgetBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.configure(bg="black")

        self.splitWebhook = "https://dspc6ekj2gjkfp44cjaffhjeue0fbswr.lambda-url.eu-west-1.on.aws/"
        self.uploadKey = config["uploadKey"]
        if not self.uploadKey and self.enabled:
            print("therun.gg plugin is enabled, but no upload key is provided.")
        self.enabled = config["enabled"] and self.uploadKey != ""
        self.wasJustResumed = False
        self.headers = {
            "Content-Type": "application/json",
            'Content-Disposition': 'attachment',
            'Accept': "*/*",
        }

    def post_run_status(self):
        if not self.enabled:
            return
        postSplits = requests.post(self.splitWebhook, json=self.jsonify(), headers=self.headers)
        print("Live status posted to therun.gg"
              if postSplits.status_code == 200
              else "Live status post failed")

    def clean_time_to_therun_api(self, time):
        return int(1000 * time) if type(time) in [float, int] else None

    def jsonify(self):
        is_reset = self.state.runEnded and self.state.splitnum < self.state.numSplits
        starttime = int(self.state.staticStartTime.timestamp() * 1000)
        endtime = int(datetime.datetime.now().replace(tzinfo=datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo).timestamp() * 1000)
        runData = []
        for i, name in enumerate(self.state.splitnames):
            runData.append({
                "name": name,
                "splitTime": self.clean_time_to_therun_api(self.state.currentRun.totals[i]) if len(self.state.currentRun.totals) > i and not is_reset else None,
                "pbSplitTime": self.clean_time_to_therun_api(self.state.comparisons[2].totals[i]),
                "bestPossible": self.clean_time_to_therun_api(self.state.comparisons[0].segments[i]),
                "comparisons": [{
                    "name": comparison.totalHeader,
                    "time": self.clean_time_to_therun_api(comparison.totals[i])
                } for comparison in self.state.comparisons]
            })
        return {
            "metadata": {
              "game": self.state.game,
              "category": self.state.category
            },
            "currentTime": self.clean_time_to_therun_api(self.state.totalTime),
            "currentSplitName": self.state.splitnames[self.state.splitnum] if self.state.splitnum < self.state.numSplits else "",
            "currentSplitIndex": self.state.splitnum if not is_reset else -1,
            "currentComparison": self.state.currentComparison.totalHeader,
            "startTime": f"/Date({starttime})/",
            "endTime": f"/Date({endtime})/",
            "isPaused": self.state.paused,
            "wasJustResumed": self.wasJustResumed,
            "uploadKey": self.uploadKey,
            "runData": runData
        }

    def onStarted(self):
        self.post_run_status()

    def onSplit(self):
        self.post_run_status()
        self.wasJustResumed = False

    def onPaused(self):
        if not self.state.paused:
            self.wasJustResumed = True
        self.post_run_status()

    def onSplitSkipped(self):
        self.post_run_status()
        self.wasJustResumed = False

    def onReset(self):
        self.post_run_status()
