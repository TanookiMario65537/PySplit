from Widgets import WidgetBase
import datetime
import requests
import threading
import json
from util import pysplitToLss as convert


class Widget(WidgetBase.WidgetBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.configure(bg="black")

        self.splitWebhook = "https://dspc6ekj2gjkfp44cjaffhjeue0fbswr.lambda-url.eu-west-1.on.aws/"
        self.fileUploadBaseUrl = "https://2uxp372ks6nwrjnk6t7lqov4zu0solno.lambda-url.eu-west-1.on.aws/"
        self.uploadKey = config["uploadKey"]
        if not self.uploadKey and config["enabled"]:
            print("therun.gg plugin is enabled, but no upload key is provided.")
        self.liveEnabled = config["enabled"] and config["liveEnabled"] and self.uploadKey != ""
        self.splitEnabled = config["enabled"] and config["splitEnabled"] and self.uploadKey != ""
        self.wasJustResumed = False
        self.headers = {
            "Content-Type": "application/json",
            'Content-Disposition': 'attachment',
            'Accept': "*/*",
        }

    def _post_run_status(self):
        postSplits = requests.post(self.splitWebhook, json=self.jsonify(), headers=self.headers)
        print("Live status posted to therun.gg"
              if postSplits.status_code == 200
              else "Live status post failed")

    def post_run_status(self):
        if not self.liveEnabled:
            return
        thread = threading.Thread(target=self._post_run_status)
        thread.start()

    def _post_splits(self):
        if not self.uploadKey:
            return
        fileUploadUrl = f"{self.fileUploadBaseUrl}?filename={self.state.game}%20-%20{self.state.category}.lss&uploadKey={self.uploadKey}"

        print("Converted XML:")
        print(convert.pysplitToLss(self.state.saveData))
        urlGetRequest = requests.get(fileUploadUrl, headers=self.headers)
        lssPut = requests.put(
            json.loads(urlGetRequest.content.decode("utf8"))["url"],
            convert.pysplitToLss(self.state.saveData),
            headers=self.headers)
        print("Splits uploaded to therun.gg"
              if lssPut.status_code == 200
              else "Split upload failed")

    def post_splits(self):
        if not self.splitEnabled:
            return
        thread = threading.Thread(target=self._post_splits)
        thread.start()

    def clean_time_to_therun_api(self, time):
        return int(1000 * time) if type(time) in [float, int] else None

    def jsonify(self):
        is_reset = self.state.runEnded and self.state.splitnum < self.state.numSplits
        starttime = int((
            datetime.datetime.fromisoformat(self.state.sessionTimes[0]["startTime"])
            if len(self.state.sessionTimes)
            else self.state.staticStartTime
        ).timestamp() * 1000)
        endtime = int(self.state.currentTime().timestamp() * 1000)
        runData = []
        bestSegments = self.state.getComparison("default", "bestSegments")
        bestRun = self.state.getComparison("default", "bestRun")
        for i, name in enumerate(self.state.splitnames):
            runData.append({
                "name": convert.convertName(name),
                "splitTime": self.clean_time_to_therun_api(self.state.currentRun.totals[i]) if len(self.state.currentRun.totals) > i and not is_reset else None,
                "pbSplitTime": self.clean_time_to_therun_api(bestRun.times.totals[i]),
                "bestPossible": self.clean_time_to_therun_api(bestSegments.times.segments[i]),
                "comparisons": [{
                    "name": comparison.title,
                    "time": self.clean_time_to_therun_api(comparison.times.totals[i])
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
            "currentComparison": self.state.currentComparison.title,
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
        if self.state.splitnum == self.state.numSplits:
            self.post_splits()
        self.wasJustResumed = False

    def onPaused(self):
        if not self.state.paused:
            self.wasJustResumed = True
        self.post_run_status()

    def onSplitSkipped(self):
        self.post_run_status()
        if self.state.splitnum == self.state.numSplits:
            self.post_splits()
        self.wasJustResumed = False

    def onReset(self):
        self.post_run_status()
        self.post_splits()
