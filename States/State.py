import os
import datetime
from timeit import default_timer as timer
import copy
from util import fileio
from util import timeHelpers as timeh
from DataClasses import SyncedTimeList as STL
from States import BaseState
import logging

logger = logging.getLogger(__name__)


class State(BaseState.State):
    pauseTime = 0
    splitstarttime = 0
    # offset = 0

    # bptList = None
    # currentBests = None
    # bestExits = None

    # currentRun = None

    comparisons = []
    # currentComparison = None
    compareNum = 1
    numComparisons = 0

    def __init__(self, splitFile):
        super().__init__(splitFile)
        self.loadingPartial = False
        if self.saveData:
            self.loadSplits(self.saveData)
        self.sessionTimes = []

    def loadSplits(self, saveData):
        super().loadSplits(saveData)
        self.offset = saveData["offset"]
        self.currentBests = STL.SyncedTimeList(
            segments=timeh.stringListToTimes(
                self.saveData["defaultComparisons"]["bestSegments"]["segments"]
            )
        )
        self.bestExits = STL.SyncedTimeList(
            totals=[
                timeh.listMin(
                    [
                        timeh.stringToTime(run["totals"][i])
                        for run in self.saveData["runs"]
                    ]
                )
                for i in range(len(self.splitnames))
            ]
        )
        self.comparisons = []
        self.setComparisons()

    def setComparisons(self):
        """
        Initialize the comparisons, BPT list, and current run.
        """
        self.bptList = STL.BptList(
            segments=timeh.stringListToTimes(
                self.saveData["defaultComparisons"]["bestSegments"]["segments"]
            )
        )

        for key in self.saveData["defaultComparisons"].keys():
            if key == "bestRun":
                self.pb_index = len(self.comparisons)
            saveKey = list(self.saveData["defaultComparisons"][key].keys())[1]
            initData = {}
            initData[saveKey] = (
                self.saveData["defaultComparisons"][key][saveKey]
            )
            cmp = STL.SyncedTimeList(**initData)
            self.comparisons.append(
                STL.Comparison(
                    self.saveData["defaultComparisons"][key]["name"],
                    cmp.totals,
                    "default",
                    name=key
                 )
            )

        self.comparisons.extend(self.generateComparisons())

        for comparison in self.saveData["customComparisons"]:
            if len(comparison["totals"]) == len(self.splitnames):
                self.comparisons.append(
                    STL.Comparison(
                        comparison["name"],
                        comparison["totals"],
                        "custom"
                    )
                )
            else:
                logger.warning(
                    f"Comparison \"{comparison["name"]}\" is invalid."
                    f"It has {len(comparison["totals"])} splits,"
                    f"but this run has {len(self.splitnames)} splits."
                )

        self.numComparisons = len(self.comparisons)
        if self.compareNum >= self.numComparisons:
            self.compareNum = self.numComparisons - 1
        self.currentComparison = self.comparisons[self.compareNum]

        self.currentRun = STL.SyncedTimeList(
            totals=[timeh.blank() for _ in range(self.numSplits)]
        )

    def generateComparisons(self):
        """
        Generates the following comparisons:
          Balanced
          Last Run
          Average
          Best Exit
          Blank
        """
        comparison_list = []

        # Balanced
        if (
            len(self.splitnames)
            and not timeh.isBlank(self.bestExits.totals[-1])
            and not timeh.isBlank(self.bptList.total)
        ):
            pbTime = timeh.stringToTime(
                self.saveData["defaultComparisons"]["bestRun"]["totals"][-1]
            )
            comparison_list.append(
                STL.Comparison(
                    "Balanced",
                    [
                        timeh.blank()
                        if timeh.isBlank(time)
                        else time*pbTime/self.bptList.total
                        for time in self.currentBests.totals
                    ],
                    "generated"
                )
            )

        # Last Run
        if len(self.saveData["runs"]):
            comparison_list.append(
                STL.Comparison(
                    "Last Run",
                    self.saveData["runs"][-1]["totals"],
                    "run"
                )
            )

        # Compute averages
        computedAverage = []
        for i in range(len(self.splitnames)):
            average = []
            for j in range(len(self.saveData["runs"])):
                time = timeh.stringToTime(
                    self.saveData["runs"][j]["totals"][i]
                )
                if not timeh.isBlank(time):
                    average.append(time)
            averageTime = timeh.sumTimeList(average)
            computedAverage.append(
                timeh.blank()
                if timeh.isBlank(averageTime)
                else averageTime/len(average)
            )

        comparison_list.append(
            STL.Comparison(
                "Average",
                computedAverage,
                "generated"
            )
        )

        # Add best exits
        comparison_list.append(
            STL.Comparison(
                "Best Exit",
                self.bestExits.totals,
                "generated"
            )
        )

        # Add blanks
        comparison_list.append(
            STL.Comparison(
                "Blank",
                [timeh.blank() for _ in self.splitnames],
                "generated"
            )
        )

        return comparison_list

    def getComparison(self, ctype: str, name: str) -> STL.Comparison | None:
        """
        Returns a comparison by type and name. Returns None if there is no
        match.
        """
        for comparison in self.comparisons:
            if comparison.ctype == ctype and comparison.name == name:
                return comparison
        return None

    def setTimes(self, time):
        """
        Sets the segment and total times. Should be used only
        for frame updates.
        Parameter: time - the current time according to the
                          system clock
        """
        self.segmentTime = timeh.difference(
            time,
            self.splitstarttime
        )
        self.totalTime = time - self.starttime

    def undoSegment(self):
        """
        Does all the state updates necessary to undo a split.
        """
        self.currentRun.resetValue(self.splitnum-1)
        self.bptList.resetValue(self.splitnum-1)

        for i in range(self.numComparisons):
            self.comparisons[i].resetValue(self.splitnum-1)
        self.currentBests.resetValue(self.splitnum-1)
        self.bestExits.resetValue(self.splitnum-1)
        self.splitnum = self.splitnum - 1
        self.splitstarttime = timeh.add(
            self.starttime,
            self.currentRun.totals[self.splitnum - 1]
            if self.splitnum > 0
            else 0
        )
        if self.splitnum == len(self.splitnames) - 1:
            self.playTime = 0
            self.staticEndTime = 0
            self.runEnded = False
            self.saveData = self.oldSaveData
        self.partialSave()

    def completeSegment(self, total, system_time):
        """
        Does all the state updates necessary to end a split. Uses
        the system clock at the exact time that the button/key was
        pressed for higher accuracy than the frame timer.

        Parameters: time - the current system time
        """
        splitTime = (
            timeh.difference(
                total,
                self.currentRun.totals[self.splitnum-1]
            )
            if self.splitnum > 0
            else total
        )
        self.currentRun.update(total, self.splitnum)
        self.bptList.update(total, self.splitnum)

        for i in range(self.numComparisons):
            self.comparisons[i].update(total, self.splitnum)
        if (
            timeh.isBlank(self.currentBests.segments[self.splitnum])
            or not timeh.greater(
                self.currentRun.segments[self.splitnum],
                self.currentBests.segments[self.splitnum]
            )
        ):
            self.currentBests.update(splitTime, self.splitnum)
        if (
            timeh.isBlank(self.bestExits.totals[self.splitnum])
            or not timeh.greater(total, self.bestExits.totals[self.splitnum])
        ):
            self.bestExits.update(total, self.splitnum)
        self.splitstarttime = system_time
        self.segmentFollowup(system_time)

    def skipSegment(self, system_time):
        """
        Does all the state updates necessary to skip a split.

        Parameters: system_time - the current system time
        """
        self.currentRun.update(timeh.blank(), self.splitnum)
        for i in range(self.numComparisons):
            self.comparisons[i].update(timeh.blank(), self.splitnum)
        self.splitstarttime = timeh.blank()
        self.segmentFollowup(system_time)

    def segmentFollowup(self, system_time):
        """
        Performs final state updates common to both completeSegment and
        skipSegment. Updates the current split number and split start time,
        then:

        1. If the run is completed, marks the run as ended, sets play time and
        end time, and removes the partial save file.
        2. If the run is not completed, makes a partial save file.

        Parameters:
            system_time - The current system time as used by the associated
                split-ending function.
        """
        self.splitnum = self.splitnum + 1
        if self.splitnum >= len(self.splitnames):
            self.playTime = system_time - self.starttime
            self.staticEndTime = self.currentTime()
            self.runEnded = True
            self.localSave()
        else:
            self.partialSave()

    def endPause(self, time):
        """
        Unpause

        Parameters: time - the current system time
        """
        self.paused = False
        elapsed = time - self.pauseTime
        self.starttime = self.starttime + elapsed
        self.splitstarttime = self.splitstarttime + elapsed
        self.pauseTime = 0

    def startPause(self, time):
        """
        Pause

        Parameters: time - the current system time
        """
        self.paused = True
        self.pauseTime = time

    def isPB(self):
        """
        Determines whether the current run is a PB or not

        Returns: True if the current run is a PB, False if not
        """
        pbcmp = self.comparisons[self.pb_index]
        if self.currentRun.lastNonBlank() > pbcmp.lastNonBlank():
            return True
        if self.currentRun.lastNonBlank() < pbcmp.lastNonBlank():
            return False
        if timeh.greater(0, pbcmp.diffs.totals[pbcmp.lastNonBlank()]):
            return True
        return False

    def cleanState(self):
        """
        Cleans the state when the user wants to restart the run.
        """
        self._cleanState()
        self.sessionTimes = []
        self.playTime = 0
        self.pauseTime = 0
        self.splitstarttime = 0
        self.comparisons = []

    def frameUpdate(self):
        time = timer()
        if not self.started:
            return 1
        if self.runEnded:
            return 2
        if self.paused:
            time = self.pauseTime
        self.setTimes(time)

    def onStarted(self):
        time = timer()
        if self.started:
            return 1
        self.staticStartTime = self.currentTime()
        self.starttime = time - timeh.stringToTime(self.offset)
        self.splitstarttime = time - timeh.stringToTime(self.offset)
        self.started = True

    def onSplit(self):
        if not self.started or self.paused or self.runEnded:
            return 1

        retVal = 0
        if (
            self.splitnames[self.splitnum][-3:] == "[P]"
            and not self.splitnum == len(self.splitnames)
            and not self.paused
        ):
            retVal = retVal + 3

        current = timer()
        self.completeSegment(current - self.starttime, current)
        if self.splitnum == len(self.splitnames):
            retVal = retVal + 4
        elif self.splitnum == len(self.splitnames) - 1:
            retVal = retVal + 5
        return retVal

    def onUndoSegment(self):
        if not self.started or self.paused or self.splitnum == 0:
            return 1

        retVal = 0

        self.undoSegment()
        if self.splitnum == len(self.splitnames) - 1:
            retVal = retVal | 2
        return retVal

    def onComparisonChanged(self, rotation):
        self.compareNum = (self.compareNum+rotation) % self.numComparisons
        self.currentComparison = self.comparisons[self.compareNum]

    def setComparison(self, num):
        if num >= self.numComparisons:
            num = 2
        self.compareNum = num
        self.currentComparison = self.comparisons[self.compareNum]

    def onPaused(self):
        time = timer()
        if not self.started or self.runEnded:
            return 1
        if self.paused:
            self.endPause(time)
        else:
            self.startPause(time)

    def onSplitSkipped(self):
        if not self.started or self.runEnded or self.paused:
            return 1
        self.skipSegment(timer())

    def onReset(self):
        if not self.started or self.runEnded:
            return 1
        time = timer()
        self.playTime = time - self.starttime
        self.staticEndTime = self.currentTime()
        self.runEnded = True
        self.localSave()

    def onRestart(self):
        if not self.runEnded:
            return 1
        self.cleanState()
        self.setComparisons()

    def shouldFinish(self):
        return not self.started or self.paused or self.runEnded

    def currentTime(self):
        return datetime.datetime.now(datetime.timezone.utc)

    def localSave(self):
        """
        Updates the local versions of the data files.
        """
        self.oldSaveData = copy.deepcopy(self.saveData)
        self.saveData["splitNames"] = self.splitnames
        self.saveData["defaultComparisons"]["bestSegments"]["segments"] = (
            timeh.timesToStringList(self.currentBests.segments)
        )
        if self.isPB():
            self.saveData["defaultComparisons"]["bestRun"]["totals"] = (
                timeh.timesToStringList(self.currentRun.totals)
            )

        self.saveData["runs"].append({
            "sessions": self.sessionTimes + [{
                "startTime": self.staticStartTime.isoformat(
                    timespec="microseconds"
                ),
                "endTime": self.staticEndTime.isoformat(
                    timespec="microseconds"
                )
             }],
            "playTime": timeh.timeToString(self.playTime),
            "totals": timeh.timesToStringList(self.currentRun.totals)
        })
        self.unSaved = True

    def saveTimes(self):
        """
        Export the locally saved data. Only do this after a local
        save.
        """
        fileio.writeSplitFile(
            self.splitFile,
            self.saveData)
        self.unSaved = False

    def hasPartialSave(self):
        """
        Determines if a partial save exists for the current
        run.
        """
        return os.path.exists(self.partialSaveFile())

    def deletePartialSave(self):
        """
        Deletes the current partial save file.
        """
        if self.hasPartialSave():
            os.remove(self.partialSaveFile())

    def saveType(self):
        """
        Determines if a partial save exists for the current
        run.
        """
        if self.paused:
            return 1
        elif self.unSaved:
            return 2
        else:
            return 0

    def partialLoad(self):
        """
        Loads a state saved partway through a run.
        """
        self.loadingPartial = True
        loadedState = fileio.readJson(self.partialSaveFile())
        for total in loadedState["splits"]["totals"]:
            if (timeh.isBlank(total)):
                self.skipSegment(timer())
            else:
                self.completeSegment(total, timer())
        self.staticStartTime = self.currentTime()
        self.starttime = self.pauseTime - loadedState["times"]["total"]
        self.splitstarttime = self.pauseTime - loadedState["times"]["segment"]
        self.totalTime = loadedState["times"]["total"]
        self.segmentTime = loadedState["times"]["segment"]
        self.sessionTimes = loadedState["sessions"]
        self.loadingPartial = False
        return loadedState

    def partialSaveFile(self):
        """
        Compute the save file name for partial saves.
        """
        # This should never happen, but leave it as a failsafe
        # so we don't throw an IndexError.
        if not self.splitFile.endswith(".pysplit"):
            return os.path.join(
                self.config["baseDir"],
                self.game,
                "." + self.category + ".psave"
            )
        return os.path.join(
            os.path.dirname(self.splitFile),
            "."
            + os.path.basename(self.splitFile).split(".pysplit")[0]
            + ".psave"
        )

    def dataMap(self):
        """
        Convert the current run's data into a dictionary. Used
        for saving a partially completed run.
        """
        return {
            "sessions": self.sessionTimes + [{
                "startTime": self.staticStartTime.isoformat(
                    timespec="microseconds"
                ),
                "endTime": self.currentTime().isoformat(
                    timespec="microseconds"
                )
            }],
            "times": {
                "segment": self.segmentTime,
                "total": self.totalTime
            },
            "splits": {
                "totals": self.currentRun.totals[
                    :self.currentRun.lastNonBlank()+1
                ]
            }
        }

    def partialSave(self):
        """
        Save the current state partway through a run.
        """
        if self.loadingPartial:
            return
        # This ensures the segment and total times are always correct when we
        # make a partial save, instead of relying on frame updates to ensure
        # these times are correct. Don't update if paused because it
        # effectively negates the pause.
        if not self.paused:
            self.setTimes(timer())
        logger.info(f"Writing partial save to {self.partialSaveFile()}")
        fileio.writeJson(self.partialSaveFile(), self.dataMap())
