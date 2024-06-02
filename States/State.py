import os
import datetime
from timeit import default_timer as timer
from util import fileio
from util import timeHelpers as timeh
from DataClasses import SyncedTimeList as STL
from States import BaseState

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
        if self.saveData:
            self.loadSplits(self.saveData)

    def loadSplits(self, saveData):
        super().loadSplits(saveData)
        self.offset = saveData["offset"]
        self.currentBests = STL.SyncedTimeList(segments=timeh.stringListToTimes(self.saveData["defaultComparisons"]["bestSegments"]["segments"]))
        self.bestExits = STL.SyncedTimeList(
            totals=[timeh.listMin([timeh.stringToTime(run["totals"][i]) for run in self.saveData["runs"]]) for i in range(len(self.splitnames))]
        )
        self.comparisons = []
        self.setComparisons()

    ##########################################################
    ## Initialize the comparisons, BPT list, and current run.
    ##########################################################
    def setComparisons(self):
        self.bptList = STL.BptList(segments=timeh.stringListToTimes(self.saveData["defaultComparisons"]["bestSegments"]["segments"]))

        for key in self.saveData["defaultComparisons"].keys():
            if key == "bestRun":
                self.pb_index = len(self.comparisons)
            saveKey = list(self.saveData["defaultComparisons"][key].keys())[1]
            initData = {}
            initData[saveKey] = self.saveData["defaultComparisons"][key][saveKey]
            cmp = STL.SyncedTimeList(**initData)
            self.comparisons.append(STL.Comparison(
                self.saveData["defaultComparisons"][key]["name"],
                cmp.totals,
                "default",
                name=key
             ))

        self.comparisons.extend(self.generateComparisons())

        for i in range(len(self.saveData["customComparisons"])):
            self.comparisons.append(STL.Comparison(
                self.saveData["customComparisons"][i]["name"],
                self.saveData["customComparisons"][i]["totals"],
                "custom"
             ))

        self.numComparisons = len(self.comparisons)
        if self.compareNum >= self.numComparisons:
            self.compareNum = self.numComparisons - 1
        self.currentComparison = self.comparisons[self.compareNum]
        
        self.currentRun = STL.SyncedTimeList(
            totals=[timeh.blank() for _ in range(self.numSplits)])

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
        if len(self.splitnames) and not timeh.isBlank(self.bestExits.totals[-1]) and not timeh.isBlank(self.bptList.total):
            pbTime = timeh.stringToTime(self.saveData["defaultComparisons"]["bestRun"]["totals"][-1])
            comparison_list.append(STL.Comparison(
                "Balanced",
                [timeh.blank() if timeh.isBlank(time) else time*pbTime/self.bptList.total for time in self.currentBests.totals],
                "generated"
            ))

        # Last Run
        if len(self.saveData["runs"]):
            comparison_list.append(STL.Comparison(
                "Last Run",
                self.saveData["runs"][-1]["totals"],
                "run"
            ))

        # Compute averages
        computedAverage = []
        for i in range(len(self.splitnames)):
            average = []
            for j in range(len(self.saveData["runs"])):
                time = timeh.stringToTime(
                    self.saveData["runs"][j]["totals"][i])
                if not timeh.isBlank(time):
                    average.append(time)
            averageTime = timeh.sumTimeList(average)
            computedAverage.append(
                timeh.blank() if timeh.isBlank(averageTime)
                else averageTime/len(average))

        comparison_list.append(STL.Comparison(
            "Average",
            computedAverage,
            "generated"
        ))

        # Add best exits
        comparison_list.append(STL.Comparison(
            "Best Exit",
            self.bestExits.totals,
            "generated"
        ))

        # Add blanks
        comparison_list.append(STL.Comparison(
            "Blank",
            [timeh.blank() for _ in self.splitnames],
            "generated"
        ))

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

    ##########################################################
    ## Sets the segment and total times. Should be used only
    ## for frame updates.
    ## Parameter: time - the current time according to the
    ##                   system clock
    ##########################################################
    def setTimes(self, time):
        self.segmentTime = time - self.splitstarttime
        self.totalTime = time - self.starttime

    ##########################################################
    ## Does all the state updates necessary to end a split. Uses
    ## the system clock at the exact time that the button/key was
    ## pressed for higher accuracy than the frame timer.
    ## 
    ## Parameters: time - the current system time
    ##########################################################
    def completeSegment(self, total, system_time):
        splitTime = timeh.difference(total, self.currentRun.totals[self.splitnum-1]) if self.splitnum > 0 else total
        self.currentRun.update(total, self.splitnum)
        self.bptList.update(total, self.splitnum)

        for i in range(self.numComparisons):
            self.comparisons[i].update(total, self.splitnum)
        if timeh.isBlank(self.currentBests.segments[self.splitnum]) or not timeh.greater(self.currentRun.segments[self.splitnum], self.currentBests.segments[self.splitnum]):
            self.currentBests.update(splitTime, self.splitnum)
        if timeh.isBlank(self.bestExits.totals[self.splitnum]) or not timeh.greater(total,self.bestExits.totals[self.splitnum]):
            self.bestExits.update(total, self.splitnum)
        self.splitnum = self.splitnum + 1
        self.splitstarttime = system_time
        if self.splitnum >= len(self.splitnames):
            self.staticEndTime = datetime.datetime.now().replace(tzinfo=datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)
            self.runEnded = True
            self.localSave()

    ##########################################################
    ## Does all the state updates necessary to skip a split.
    ## 
    ## Parameters: time - the current system time
    ##########################################################
    def skipSegment(self, system_time):
        self.currentRun.update(timeh.blank(), self.splitnum)
        for i in range(self.numComparisons):
            self.comparisons[i].update(timeh.blank(), self.splitnum)
        self.splitnum = self.splitnum + 1
        self.splitstarttime = system_time
        if self.splitnum >= len(self.splitnames):
            self.staticEndTime = datetime.datetime.now().replace(tzinfo=datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)
            self.runEnded = True
            self.localSave()

    ##########################################################
    ## Unpause
    ##
    ## Parameters: time - the current system time
    ##########################################################
    def endPause(self,time):
        self.paused = False
        elapsed = time - self.pauseTime
        self.starttime = self.starttime + elapsed
        self.splitstarttime = self.splitstarttime + elapsed
        self.pauseTime = 0

    ##########################################################
    ## Pause
    ## 
    ## Parameters: time - the current system time
    ##########################################################
    def startPause(self,time):
        self.paused = True
        self.pauseTime = time

    ##########################################################
    ## Determines whether the current run is a PB or not
    ##
    ## Returns: True if the current run is a PB, False if not
    ##########################################################
    def isPB(self):
        pbcmp = self.comparisons[self.pb_index]
        if self.currentRun.lastNonBlank() > pbcmp.lastNonBlank():
            return True
        if self.currentRun.lastNonBlank() < pbcmp.lastNonBlank():
            return False
        if timeh.greater(0, pbcmp.diffs.totals[pbcmp.lastNonBlank()]):
            return True
        return False

    ##########################################################
    ## Cleans the state when the user wants to restart the run.
    ##########################################################
    def cleanState(self):
        self._cleanState()
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
        self.staticStartTime = datetime.datetime.now().replace(tzinfo=datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)
        self.starttime = time - timeh.stringToTime(self.offset)
        self.splitstarttime = time - timeh.stringToTime(self.offset)
        self.started = True

    def onSplit(self):
        if not self.started or self.paused or self.runEnded:
            return 1

        retVal = 0
        if self.splitnames[self.splitnum][-3:] == "[P]" and not self.splitnum == len(self.splitnames) and not self.paused:
            retVal = retVal + 3

        current = timer()
        self.completeSegment(current - self.starttime, current)
        if self.splitnum == len(self.splitnames):
            retVal = retVal + 4
        elif self.splitnum == len(self.splitnames) - 1:
            retVal = retVal + 5
        return retVal

    def onComparisonChanged(self,rotation):
        self.compareNum = (self.compareNum+rotation)%self.numComparisons
        self.currentComparison = self.comparisons[self.compareNum]

    def setComparison(self,num):
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
        self.staticEndTime = datetime.datetime.now().replace(tzinfo=datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)
        self.runEnded = True
        self.localSave()

    def onRestart(self):
        if not self.runEnded:
            return 1
        self.cleanState()
        self.setComparisons()

    def shouldFinish(self):
        return not self.started or self.paused or self.runEnded

    ##########################################################
    ## Updates the local versions of the data files.
    ##########################################################
    def localSave(self):
        self.saveData["splitNames"] = self.splitnames
        self.saveData["defaultComparisons"]["bestSegments"]["segments"] = timeh.timesToStringList(self.currentBests.segments)
        if self.isPB():
            self.saveData["defaultComparisons"]["bestRun"]["totals"] = timeh.timesToStringList(self.currentRun.totals)

        self.saveData["runs"].append({
            "startTime": self.staticStartTime.isoformat(),
            "endTime": self.staticEndTime.isoformat(),
            "totals": timeh.timesToStringList(self.currentRun.totals)
        })
        self.unSaved = True

    ##########################################################
    ## Export the locally saved data. Only do this after a local
    ## save.
    ##########################################################
    def saveTimes(self):
        fileio.writeSplitFile(
            self.splitFile,
            self.saveData)
        self.unSaved = False

    ##########################################################
    ## Determines if a partial save exists for the current
    ## run.
    ##########################################################
    def hasPartialSave(self):
        return os.path.exists(self.partialSaveFile())

    ##########################################################
    ## Deletes the current partial save file.
    ##########################################################
    def deletePartialSave(self):
        if self.hasPartialSave():
            os.remove(self.partialSaveFile())

    ##########################################################
    ## Determines if a partial save exists for the current
    ## run.
    ##########################################################
    def saveType(self):
        if self.paused:
            return 1
        elif self.unSaved:
            return 2
        else:
            return 0

    ##########################################################
    ## Loads a state saved partway through a run.
    ##########################################################
    def partialLoad(self):
        loadedState = fileio.readJson(self.partialSaveFile())
        for total in loadedState["splits"]["totals"]:
            if (timeh.isBlank(total)):
                self.skipSegment(timer())
            else:
                self.completeSegment(total, timer())
        self.staticStartTime = datetime.datetime.fromisoformat(loadedState["startTime"])
        self.starttime = self.pauseTime - loadedState["times"]["total"]
        self.splitstarttime = self.pauseTime - loadedState["times"]["segment"]
        return loadedState

    ##########################################################
    ## Compute the save file name for partial saves.
    ##########################################################
    def partialSaveFile(self):
        return self.config["baseDir"] + "/" + self.game + "/." + self.category + ".psave"

    ##########################################################
    ## Convert the current run's data into a dictionary. Used
    ## for saving a partially completed run.
    ########################################################## 
    def dataMap(self):
        dataMap = {}
        dataMap["startTime"] = self.staticStartTime.isoformat()
        dataMap["times"] = {"segment": self.segmentTime, "total": self.totalTime}
        dataMap["splits"] = {
            "segments": self.currentRun.segments[:self.currentRun.lastNonBlank()+1],
            "totals": self.currentRun.totals[:self.currentRun.lastNonBlank()+1]
        }
        return dataMap

    ##########################################################
    ## Save the current state partway through a run.
    ########################################################## 
    def partialSave(self):
        print("Writing partial save to", self.partialSaveFile())
        fileio.writeJson(self.partialSaveFile(), self.dataMap())
