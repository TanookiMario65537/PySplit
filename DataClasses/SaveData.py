import copy
import re
from pathlib import Path
from util import fileio
from util import readConfig as rc
from util import timeHelpers as timeh
from DataClasses import SyncedTimeList as STL
from Components import Notifier
import logging

logger = logging.getLogger(__name__)


class CacheError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class SaveDataCache:
    def __init__(self):
        self._cache = {}
        self._cacheUpdateStacks = {}
        self._savePoints = {}
        self.clearEmptySplits()

    def clearEmptySplits(self):
        self._cache[""] = fileio.newComparisons()
        self._cacheUpdateStacks[""] = [{
            "type": "load",
            "data": fileio.newComparisons()
        }]
        self._savePoints[""] = -1

    def getSaveData(self, splitFile):
        return self._cache.get(splitFile, fileio.newComparisons())

    def hasSplitFile(self, splitFile):
        return splitFile in self._cache.keys()

    def isSaved(self, splitFile):
        return (
            self._savePoints[splitFile]
            == (len(self._cacheUpdateStacks[splitFile]) - 1)
        )

    def loadSaveData(self, splitFile):
        if not splitFile:
            return
        if splitFile in self._cache.keys():
            return
        self.updateSaveData(
            splitFile,
            fileio.readSplitFile(splitFile),
            "load"
        )
        self._savePoints[splitFile] = (
            len(self._cacheUpdateStacks[splitFile]) - 1
        )

    def pushUpdateStack(self, splitFile, info):
        stack = self._cacheUpdateStacks.get(splitFile, [])
        self._cacheUpdateStacks[splitFile] = stack + [info]
        if not len(stack):
            self._savePoints[splitFile] = -1

    def removeSplitFile(self, splitFile):
        del self._cache[splitFile]
        del self._cacheUpdateStacks[splitFile]
        del self._savePoints[splitFile]

    def removeUnsavedChanges(self, splitFile):
        """
        Should only ever be used for the top level split file.
        """
        i = len(self._cacheUpdateStacks[splitFile]) - 1
        while (
            i > 0
            and self._cacheUpdateStacks[splitFile][i]["type"] == "edit"
            and i > self._savePoints[splitFile]
        ):
            self._cacheUpdateStacks[splitFile].pop()
            i -= 1
        self._cache[splitFile] = self._cacheUpdateStacks[splitFile][-1]["data"]

    def save(self, splitFile):
        fileio.writeSplitFile(
            splitFile,
            self.getSaveData(splitFile)
        )
        self._savePoints[splitFile] = (
            len(self._cacheUpdateStacks[splitFile]) - 1
        )

    def undoUpdate(self, splitFile):
        if splitFile not in self._cacheUpdateStacks.keys():
            return {
                "type": "empty",
                "data": {}
            }
        # This should never happen, because it's only called after undoing the
        # last split, and this means there is (at minimum) one entry for the
        # load and one for the end of the run. Ultimately this exception is for
        # development only, and if it is raised something is very wrong.
        if len(self._cacheUpdateStacks[splitFile]) < 2:
            raise CacheError(
                f"Cache stack for {splitFile} has less than 2 entries."
            )
        self._cache[splitFile] = self._cacheUpdateStacks[splitFile][-2]["data"]
        return self._cacheUpdateStacks[splitFile].pop(-1)

    def updateSaveData(self, splitFile, saveData, save_type):
        self._cache[splitFile] = saveData
        self.pushUpdateStack(
            splitFile,
            {
                "type": save_type,
                "data": saveData
            }
        )


class Split:
    def __init__(self, index, name):
        self.name = name
        self.index = index
        match = re.match(r'(.*)\[P\]', name)
        self.pauseAtEnd = match is not None
        match = re.match(r'(.*)\[(\d+)\]', name)
        if match is None:
            self.showCollectibleCount = False
            self.collectibleCount = 0
        else:
            self.showCollectibleCount = True
            self.collectibleCount = int(match.group(2))
        self.inGroup = name.startswith("- ")
        match = re.match(r'(.*)\{(.*)\}$', name)
        self.isGroupEnd = match is not None
        self.groupName = match.group(2).strip() if self.isGroupEnd else ""
        self.subrunPath = []
        self.trimmedName = (name[2:] if self.inGroup else name[:]).replace(
            "[P]", ""
        ).replace(
            f"[{self.collectibleCount}]", ""
        ).replace(
            "{"f"{self.groupName}""}", ""
        ).strip()
        self.update_repr()

    def __copy__(self):
        newObj = type(self)(self.index, self.name)
        newObj.update_props(**{
            "pauseAtEnd": self.pauseAtEnd,
            "collectibleCount": self.collectibleCount,
            "showCollectibleCount": self.showCollectibleCount,
            "inGroup": self.inGroup,
            "isGroupEnd": self.isGroupEnd,
            "groupName": self.groupName,
            "trimmedName": self.trimmedName,
            "subrunPath": copy.deepcopy(self.subrunPath),
        })
        return newObj

    def __str__(self):
        return self._str

    def __repr__(self):
        return self._repr

    def update_props(self, **kwargs):
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)
            else:
                raise AttributeError(f"Split has no property {key}.")
        self.update_repr()

    def update_repr(self):
        self._str = ""
        self._str += f"{self.trimmedName}"
        self._str += " [P]" if self.pauseAtEnd else ""
        self._str += (
            f" [{self.collectibleCount}]"
            if self.showCollectibleCount
            else ""
        )

        # _repr is meant to resemble the string that would be saved in the
        # split file.
        self._repr = ""
        self._repr += "- " if self.inGroup else ""
        self._repr += self._str
        self._repr += " {" + self.groupName + "}" if self.isGroupEnd else ""


class SaveData(Notifier.Notifier):
    # This is a shared cache for all SaveData instances.
    _dataCache = SaveDataCache()
    _topLevelSaveData = None
    _config = None

    def __init__(self, splitFile, groupName="", startSplit=0, subrunPath=[]):
        super().__init__()
        if self._topLevelSaveData is None:
            self._topLevelSaveData = self
        if self._config is None:
            self._config = rc.getUserConfig()
        self.startSplit = startSplit
        self.groupName = groupName
        filePath = Path(splitFile)
        if not filePath.is_absolute():
            filePath = Path(self._config["baseDir"]) / filePath
        self._splitFile = str(filePath.resolve())
        self._dataCache.loadSaveData(self._splitFile)
        self._erroredComparisons = []
        self.subrunPath = copy.deepcopy(subrunPath)
        self.collapsed = False
        self.listeners = {}
        self.parseSplits()

    def parseSplits(self, data=None):
        """
        Set the data here to use a specific saveData object. Only do this if
        that data object will be saved later, otherwise the UI will show data
        parsed from something that doesn't actually match the saved splits.
        """
        self._splits = []
        self._subruns = []
        self._splitIndexToRunInfo = {}
        if data is None:
            data = self.currentSaveData()
        for i, splitName in enumerate(data["splitNames"]):
            md = self.parseMarkdown(splitName)
            if md["isMd"]:
                if self.containsSelfReferencePath(
                    md["fileName"],
                    self.subrunPath
                ):
                    raise RecursionError(
                        "Top-level split file loaded in subrun."
                    )
                subrunPath = (
                    copy.deepcopy(self.subrunPath) + [len(self._subruns)]
                )
                self._subruns.append(SaveData(
                    md["fileName"],
                    groupName=md["groupName"],
                    startSplit=len(self._splits),
                    subrunPath=subrunPath
                ))
                self._subruns[-1].collapsed = md["collapsed"]
                self._splitIndexToRunInfo[i] = {
                    "isRun": True,
                    "runIndex": len(self._subruns)-1,
                    "collapsed": self._subruns[-1].collapsed,
                    "startSplit": len(self._splits),
                    "count": self._subruns[-1].count,
                }
                if len(self._splits):
                    previousSplit = self._splits[-1]
                    startIndex = previousSplit.index + 1
                    startCollectibles = previousSplit.collectibleCount
                else:
                    startIndex = 0
                    startCollectibles = 0
                for i, split in enumerate(self._subruns[-1]._splits):
                    newSplit = copy.copy(split)
                    props = {
                        "index": startIndex + i,
                        "collectibleCount": (
                            startCollectibles + newSplit.collectibleCount
                        ),
                        "subrunPath": (
                             [len(self._subruns)-1] + newSplit.subrunPath
                        )
                    }
                    if self._subruns[-1].collapsed:
                        props["inGroup"] = True
                        props["groupName"] = md["groupName"]
                        props["isGroupEnd"] = i == self._subruns[-1].count - 1
                    newSplit.update_props(**props)
                    self._splits.append(newSplit)
            else:
                self._splitIndexToRunInfo[i] = {
                    "isRun": False,
                    "runIndex": -1,
                    "startSplit": len(self._splits),
                    "collapsed": True,
                    "count": 1,
                }
                self._splits.append(Split(len(self._splits), splitName))
                self._splits[-1].subrunPath = copy.deepcopy(self.subrunPath)
                if not self._splits[-1].showCollectibleCount:
                    self._splits[-1].collectibleCount = (
                        self._splits[-2].collectibleCount
                        if len(self._splits) > 1
                        else 0
                    )
                    self._splits[-1].update_repr()
        self._splitNames = [str(split) for split in self._splits]
        self._splitCount = len(self._splits)

    # External properties
    @property
    def count(self) -> int:
        return self._splitCount

    @property
    def splitNames(self) -> list[str]:
        return self._splitNames

    @property
    def splits(self) -> list[Split]:
        return self._splits

    @property
    def data(self):
        return self.currentSaveData()

    @property
    def splitFile(self):
        return self._splitFile

    def currentSaveData(self):
        return self._dataCache.getSaveData(self._splitFile)

    def currentSaveDataSafe(self):
        return copy.deepcopy(self.currentSaveData())

    # Utility functions
    def subrunCollapsed(self, splitIndex):
        """
        Determines if a current index has a collapsed subrun.
        Return True by default (i.e. when there is no run for that index)
        because collapsed is the default state.

        Expects the splits to be parsed, otherwise _splitIndexToRunInfo will
        not be populated.
        """
        if splitIndex < 0 or splitIndex >= self._splitCount:
            return True
        return self._splitIndexToRunInfo[splitIndex]["collapsed"]

    def splitNameCollapsed(self, index):
        md = self.parseMarkdown(self.data["splitNames"][index])
        return (not md["isMd"]) or md["collapsed"]

    def parseMarkdown(self, splitName):
        match = re.match(r'^\[([^\]]+)\]\(([^\)]+.pysplit)\)$', splitName)
        if match is None:
            return {
                "isMd": False
            }
        else:
            return {
                "isMd": True,
                "groupName": match.group(1),
                "fileName": match.group(2),
                "collapsed": not match.group(1).endswith("*")
            }

    def containsSelfReferenceFile(self, fileName):
        return fileName == self._topLevelSaveData._splitFile

    def containsSelfReferenceName(self, splitName):
        md = self.parseMarkdown(splitName)
        return (
            md["isMd"]
            and (md["fileName"] == self._topLevelSaveData._splitFile)
        )

    def containsSelfReferencePath(self, fileName, path):
        if self._splitFile == fileName:
            return True
        if not len(path) or (path[0] <= len(self._subruns)):
            return False
        if self._subruns[path[0]].containsSelfReferencePath(
            fileName,
            path[1:]
        ):
            return True
        return False

    def containsSubRun(self, fileName):
        for run in self._subruns:
            if run.splitFile == fileName:
                return True
            if run.containsSubRun(fileName):
                return True
        return False

    def removeEdits(self):
        self._dataCache.removeUnsavedChanges(self._splitFile)
        self.parseSplits()

    # External "API"
    def addRun(self, state):
        """
        At the end of a run, adds the completed runs to the save data.
        Goes through and recursively updates all subruns as well.
        """
        saveData = self.currentSaveDataSafe()

        # Actually need to check golds here, since "state.currentBests" is
        # relative to the top level run
        bests = saveData["defaultComparisons"]["bestSegments"]["segments"]
        startTime = (
            0 if self.startSplit == 0
            else state.currentRun.totals[self.startSplit - 1]
        )
        subrun = STL.SyncedTimeList(
            totals=[
                timeh.difference(time, startTime)
                for time in state.currentRun.totals[
                    self.startSplit:self.startSplit+self.count
                ]
            ]
        )
        for i in range(self.count):
            currentTime = subrun.segments[i]
            diff = timeh.difference(
                timeh.stringToTime(bests[i]),
                currentTime
            )
            if not timeh.isBlank(diff) and (diff > 0):
                bests[i] = timeh.timeToString(currentTime)
        saveData["defaultComparisons"]["bestSegments"]["segments"] = bests

        # If this run is a PB, update PB
        subPb = STL.SyncedTimeList(
            totals=saveData["defaultComparisons"]["bestRun"]["totals"]
        )
        isPb = False
        if subrun.lastNonBlank() > subPb.lastNonBlank():
            isPb = True
        if subrun.lastNonBlank() < subPb.lastNonBlank():
            isPb = False
        if timeh.greater(
            subPb.totals[subPb.lastNonBlank()],
            subrun.totals[subrun.lastNonBlank()]
        ):
            isPb = True
        if isPb:
            saveData["defaultComparisons"]["bestRun"]["totals"] = (
                timeh.timesToStringList(subrun.totals)
            )

        # Need to adjust the sessions and trim the totals
        sessionList = copy.deepcopy(state.sessionTimes) + [{
            "startTime": state.staticStartTime.isoformat(
                timespec="microseconds"
            ),
            "endTime": state.staticEndTime.isoformat(
                timespec="microseconds"
            )
        }]
        runStart = (
            sessionList[0]["startTime"]
            if self.startSplit == 0
            else state.currentRun.isoTimes[self.startSplit-1]
        )
        runEnd = (
            sessionList[-1]["endTime"]
            if self.startSplit + self.count == state.saveData.count
            else state.currentRun.isoTimes[self.startSplit+self.count-1]
        )
        count = 0
        while count < len(sessionList):
            if count == 0:
                if (
                    (runStart >= sessionList[0]["startTime"])
                    and (runStart < sessionList[0]["endTime"])
                ):
                    count += 1
                else:
                    sessionList.pop(0)
            else:
                if runEnd < sessionList[count]["startTime"]:
                    sessionList = sessionList[:count]
                    break
                else:
                    count += 1
        sessionList[0]["startTime"] = runStart
        sessionList[-1]["endTime"] = runEnd
        saveData["runs"].append({
            "sessions": sessionList,
            "playTime": timeh.timeToString(subrun.totals[-1]),
            "totals": timeh.timesToStringList(subrun.totals)
        })
        self._dataCache.updateSaveData(self._splitFile, saveData, "run")

        # Update all subruns
        for subrun in self._subruns:
            subrun.addRun(state)

    def save(self):
        """
        Export the locally saved data. Only do this after a local
        save.
        """
        if not self._dataCache.isSaved(self._splitFile):
            self._dataCache.save(self._splitFile)
        for run in self._subruns:
            run.save()

    def undoLastUpdate(self):
        """
        This reverts the last update recursively for all runs. Importantly,
        this means that if there are n copies of a single run in this run (for
        a 10xAny% or something), this will undo n updates on that run. As a
        result, it must be used carefully. Currently, it is only used to undo
        the last split of a run, and it works as expected in that case.
        """
        self._dataCache.undoUpdate(self._splitFile)
        for run in self._subruns:
            run.undoLastUpdate()

    # Generate all the comparisons.
    def getComparisons(self, state, splitIndex):
        saveData = self.currentSaveData()

        comparisons = []
        comparisons.extend(self.defaultComparisons(saveData))
        comparisons.extend(self.generatedComparisons(saveData, state))
        comparisons.extend(self.customComparisons(saveData))
        if self.startSplit > 0:
            startTime = state.currentRun.totals[self.startSplit-1]
        else:
            startTime = 0
        for i in range(min(
            state.currentRun.lastNonBlank() - self.startSplit+1,
            self.count
        )):
            for cmp in comparisons:
                cmp.update(
                    timeh.difference(state.currentRun.totals[i], startTime),
                    i+self.startSplit
                )
        comparisons.extend(self.subRunComparisons(saveData, state, splitIndex))

        return comparisons

    def defaultComparisons(self, saveData):
        comparisons = []
        for key in saveData["defaultComparisons"].keys():
            timeKey = "segments" if key.endswith("Segments") else "totals"
            initData = {}
            initData[timeKey] = (
                saveData["defaultComparisons"][key][timeKey]
            )
            comparisons.append(
                STL.Comparison(
                    saveData["defaultComparisons"][key]["name"],
                    [],
                    "default",
                    name=key,
                    timeData=initData
                 )
            )
        return comparisons

    def generatedComparisons(self, saveData, state):
        comparisons = []
        if not saveData["splitNames"]:
            return []

        # Balanced
        pbTime = timeh.stringToTime(
            saveData["defaultComparisons"]["bestRun"]["totals"][-1]
        )
        bptList = STL.BptList(
            segments=timeh.stringListToTimes(
                saveData["defaultComparisons"]["bestSegments"]["segments"]
            )
        )
        currentBests = STL.SyncedTimeList(
            segments=timeh.stringListToTimes(
                saveData["defaultComparisons"]["bestSegments"]["segments"]
            )
        )
        if (
            self.count
            and not timeh.isBlank(pbTime)
            and not timeh.isBlank(bptList.total)
        ):
            comparisons.append(
                STL.Comparison(
                    "Balanced",
                    [
                        timeh.blank()
                        if timeh.isBlank(time)
                        else time*pbTime/bptList.total
                        for time in currentBests.totals
                    ],
                    "generated"
                )
            )

        # Last Run
        if len(saveData["runs"]):
            comparisons.append(
                STL.Comparison(
                    "Last Run",
                    saveData["runs"][-1]["totals"],
                    "run"
                )
            )

        # Compute averages
        computedAverage = []
        for i in range(self.count):
            average = []
            for j in range(len(saveData["runs"])):
                time = timeh.stringToTime(
                    saveData["runs"][j]["totals"][i]
                )
                if not timeh.isBlank(time):
                    average.append(time)
            averageTime = timeh.sumTimeList(average)
            computedAverage.append(
                timeh.blank()
                if timeh.isBlank(averageTime)
                else averageTime/len(average)
            )

        comparisons.append(
            STL.Comparison(
                "Average",
                computedAverage,
                "generated"
            )
        )

        # Add best exits
        bestExits = STL.SyncedTimeList(
            totals=[
                timeh.listMin(
                    [
                        timeh.stringToTime(run["totals"][i])
                        for run in saveData["runs"]
                    ]
                )
                for i in range(self.count)
            ]
        )
        comparisons.append(
            STL.Comparison(
                "Best Exit",
                bestExits.totals,
                "generated"
            )
        )

        # Add blanks
        comparisons.append(
            STL.Comparison(
                "Blank",
                [timeh.blank() for _ in range(self.count)],
                "generated"
            )
        )

        return comparisons

    def customComparisons(self, saveData):
        comparisons = []
        for comparison in saveData["customComparisons"]:
            if len(comparison["totals"]) == self.count:
                comparisons.append(
                    STL.Comparison(
                        comparison["name"],
                        comparison["totals"],
                        "custom"
                    )
                )
            elif comparison["name"] not in self._erroredComparisons:
                logger.warning(
                    f"Comparison \"{comparison["name"]}\" is invalid."
                    f"It has {len(comparison["totals"])} splits,"
                    f"but this run has {self.count} splits."
                )
                self._erroredComparisons.append(comparison["name"])
        return comparisons

    def subRunComparisons(self, saveData, state, index):
        subcomparisons = []
        runIndex = -1
        # This can probably just use
        #   self._subruns[self._splits[state.splitnum]]
        # but this is fine and I can't be bothered to test it.
        for i, run in enumerate(self._subruns):
            if (
                (index >= run.startSplit)
                and (index < run.startSplit + run.count)
            ):
                subcomparisons = run.getComparisons(
                    state,
                    index - run.startSplit
                )
                cmpRun = run
                runIndex = i
        if not len(subcomparisons):
            return []
        comparisons = []
        preRun = [timeh.blank() for _ in range(max(cmpRun.startSplit-1, 0))]
        if cmpRun.startSplit > 0:
            startTime = state.currentRun.totals[cmpRun.startSplit-1]
            preRun.append(startTime)
        else:
            startTime = 0
        postRun = [
            timeh.blank()
            for _ in range(max(self.count-(cmpRun.startSplit+cmpRun.count), 0))
        ]
        for cmp in subcomparisons:
            if cmp.name == "Blank":
                continue
            times = (
                copy.deepcopy(preRun)
                + [timeh.add(startTime, time) for time in cmp.times.totals]
                + copy.deepcopy(postRun)
            )
            comparisons.append(STL.Comparison(
                cmp.title,
                times,
                cmp.ctype,
                name=cmp.name,
                subrunPath=(
                    [{"index": runIndex, "name": cmpRun.groupName}]
                    + cmp.subrunPath
                )
            ))
        return comparisons

    # Editing API.
    # Edits the top-level run only.
    # For use with the split editor.
    def addSplit(self, index):
        newSaveData = self.currentSaveDataSafe()
        newSaveData["splitNames"].insert(index, "")
        for key, cmp in newSaveData["defaultComparisons"].items():
            timeKey = "segments" if key.endswith("Segments") else "totals"
            cmp[timeKey].insert(index, "-")
        for cmp in newSaveData["customComparisons"]:
            cmp["totals"].insert(index, "-")
        for run in newSaveData["runs"]:
            run["totals"].insert(index, "-")
        self._dataCache.updateSaveData(self._splitFile, newSaveData, "edit")
        self.parseSplits()
        self.notifyListeners({
            "type": "splitAdded",
            "data": index
        })

    def removeSplit(self, index):
        newSaveData = self.currentSaveDataSafe()
        newSaveData["splitNames"].pop(index)
        for key, cmp in newSaveData["defaultComparisons"].items():
            timeKey = "segments" if key.endswith("Segments") else "totals"
            cmp[timeKey].pop(index)
        for cmp in newSaveData["customComparisons"]:
            cmp["totals"].pop(index)
        for run in newSaveData["runs"]:
            run["totals"].pop(index)
        self._dataCache.updateSaveData(self._splitFile, newSaveData, "edit")
        self.parseSplits()
        self.notifyListeners({
            "type": "splitRemoved",
            "data": index
        })

    def addComparison(self):
        newSaveData = self.currentSaveDataSafe()
        newSaveData["customComparisons"].append({
            "name": "New Comparison",
            "totals": [
                "-"
                for _ in range(self.count)
            ]
        })
        self._dataCache.updateSaveData(self._splitFile, newSaveData, "edit")
        self.notifyListeners({
            "type": "comparisonAdded",
            "data": newSaveData["customComparisons"][-1]
        })

    def removeComparison(self):
        newSaveData = self.currentSaveDataSafe()
        oldCmp = newSaveData["customComparisons"].pop(-1)
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "comparisonRemoved",
            "data": oldCmp
        })

    def updateSplitName(self, index, newName):
        newSaveData = self.currentSaveDataSafe()
        oldMd = self.parseMarkdown(newSaveData["splitNames"][index])
        newMd = self.parseMarkdown(newName)
        shouldUpdateSubruns = (
            (not oldMd["isMd"] and newMd["isMd"])
            or (oldMd["isMd"] and not newMd["isMd"])
            or (
                (oldMd["isMd"] and newMd["isMd"])
                and (oldMd["fileName"] != newMd["fileName"])
            )
        )
        oldInfo = self._splitIndexToRunInfo[index]
        newSaveData["splitNames"][index] = newName
        collapsedStateChanged = (
            (
                oldInfo["collapsed"]
                and (newMd["isMd"])
                and (not newMd["collapsed"])
            ) or (
                (not oldInfo["collapsed"])
                and (
                    (not newMd["isMd"])
                    or (newMd["collapsed"])
                )
            )
        )
        if shouldUpdateSubruns:
            self.parseSplits(newSaveData)
            newInfo = self._splitIndexToRunInfo[index]
            if oldInfo["count"] != newInfo["count"]:
                self.adjustAllTimes(newSaveData, oldInfo, newInfo)
                self._dataCache.updateSaveData(
                    self._splitFile,
                    newSaveData,
                    "edit"
                )
            self.notifyListeners({
                "type": "subrunChanged",
                "data": index
            })
            if oldInfo["collapsed"] != newInfo["collapsed"]:
                self.notifyListeners({
                    "type": "collapsedChanged",
                    "data": {
                        "index": index,
                        "collapsed": newInfo["collapsed"]
                    },
                })
        elif collapsedStateChanged:
            self.parseSplits(newSaveData)
            self._dataCache.updateSaveData(
                self._splitFile,
                newSaveData,
                "edit"
            )
            self.notifyListeners({
                "type": "collapsedChanged",
                "data": {
                    "index": index,
                    "collapsed": not oldInfo["collapsed"]
                },
            })
        else:
            self._dataCache.updateSaveData(
                self._splitFile,
                newSaveData,
                "edit"
            )
        self.notifyListeners({
            "type": "splitNameUpdated",
            "data": {
                "index": index,
                "name": newName
            }
        })

    def adjustTotals(self, cmp, oldInfo, newInfo):
        subrunEndTime = cmp["totals"][oldInfo["startSplit"]+oldInfo["count"]-1]
        cmp["totals"] = (
            cmp["totals"][:oldInfo["startSplit"]]
            + ["-" for _ in range(newInfo["count"]-1)]
            + [subrunEndTime]
            + [
                total
                for total in cmp["totals"][
                    oldInfo["startSplit"]+oldInfo["count"]:
                ]
            ]
        )

    def adjustAllTimes(self, saveData, oldInfo, newInfo):
        for key, cmp in saveData["defaultComparisons"].items():
            timeKey = (
                "segments" if key.endswith("Segments") else "totals"
            )
            if timeKey == "segments":
                if newInfo["count"] == 1:
                    runsAsTimes = [
                        timeh.stringListToTimes(run["totals"])
                        for run in saveData["runs"]
                    ]
                    best = timeh.listMin([
                        timeh.difference(
                            run[oldInfo["startSplit"]+oldInfo["count"]-1],
                            0 if oldInfo["startSplit"] == 0
                            else run[oldInfo["startSplit"]-1]
                        )
                        for run in runsAsTimes
                    ])
                    centralSegments = [timeh.timeToString(best)]
                else:
                    centralSegments = ["-" for _ in range(newInfo["count"])]
                cmp["segments"] = (
                    cmp["segments"][:oldInfo["startSplit"]]
                    + centralSegments
                    + cmp["segments"][oldInfo["startSplit"]+oldInfo["count"]:]
                )
            else:
                self.adjustTotals(cmp, oldInfo, newInfo)
        for cmp in saveData["customComparisons"]:
            self.adjustTotals(cmp, oldInfo, newInfo)
        for run in saveData["runs"]:
            self.adjustTotals(run, oldInfo, newInfo)

    def updateComparisonName(self, index, newName):
        newSaveData = self.currentSaveDataSafe()
        defaultComparisons = self.defaultComparisons(newSaveData)
        if index < len(defaultComparisons):
            cmpName = defaultComparisons[index].name
            newSaveData["defaultComparisons"][cmpName]["name"] = newName
        else:
            trueIndex = index-len(defaultComparisons)
            newSaveData["customComparisons"][trueIndex]["name"] = newName
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "comparisonNameUpdated",
            "data": {
                "index": index,
                "name": newName
            }
        })

    # This is only used for the practice timer.
    def updateBest(self, index, time):
        newSaveData = self.currentSaveDataSafe()
        (
            newSaveData["defaultComparisons"]["bestSegments"]
            ["segments"][index]
        ) = time
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "bestUpdated",
            "data": {
                "index": index,
                "time": time
            }
        })

    def updateComparison(self, _, col_index, comparison):
        newSaveData = self.currentSaveDataSafe()
        defaultComparisons = self.defaultComparisons(newSaveData)
        if col_index < len(defaultComparisons):
            cmpName = defaultComparisons[col_index].name
            timeKey = "segments" if cmpName.endswith("Segments") else "totals"
            if timeKey == "segments":
                newSaveData["defaultComparisons"][cmpName][timeKey] = (
                    timeh.timesToStringList(comparison.times.segments)
                )
            else:
                newSaveData["defaultComparisons"][cmpName][timeKey] = (
                    timeh.timesToStringList(comparison.times.totals)
                )
        else:
            trueIndex = col_index-len(defaultComparisons)
            newSaveData["customComparisons"][trueIndex]["totals"] = (
                timeh.timesToStringList(comparison.times.totals)
            )
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "comparisonUpdated",
            "data": {
                "index": col_index,
                "times": comparison.times.totals
            }
        })

    def updateGame(self, game):
        newSaveData = self.currentSaveDataSafe()
        newSaveData["game"] = game
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "gameUpdated",
            "data": game
        })

    def updateCategory(self, category):
        newSaveData = self.currentSaveDataSafe()
        newSaveData["category"] = category
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "categoryUpdated",
            "data": category
        })

    def updateOffset(self, time):
        newSaveData = self.currentSaveDataSafe()
        newSaveData["offset"] = time
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "offsetUpdated",
            "data": time
        })

    def setSplitFile(self, splitFile):
        oldData = self.data
        oldSplitFile = self.splitFile
        if splitFile != self._splitFile:
            self._dataCache.updateSaveData(
                splitFile,
                oldData,
                "rename"
            )
            self._dataCache.removeSplitFile(self._splitFile)
        self._splitFile = splitFile
        if not oldSplitFile:
            self._dataCache.clearEmptySplits()

    def updateSubrun(self, index, splitFile):
        newSaveData = self.currentSaveDataSafe()
        if splitFile.startswith(self._config["baseDirAbsolute"]):
            trimmedFile = splitFile.replace(
                self._config["baseDirAbsolute"] + "/",
                ""
            )
        else:
            trimmedFile = splitFile
        oldMd = self.parseMarkdown(newSaveData["splitNames"][index])
        if oldMd["isMd"]:
            newSaveData["splitNames"][index] = (
                f"[{oldMd['groupName']}]({trimmedFile})"
            )
        else:
            newSaveData["splitNames"][index] = f"[placeholder]({trimmedFile})"
        oldInfo = self._splitIndexToRunInfo[index]
        self.parseSplits(newSaveData)
        if not oldMd["isMd"]:
            newSaveData["splitNames"][index] = (
                f"[{self._dataCache.getSaveData(splitFile)['game']} "
                f"{self._dataCache.getSaveData(splitFile)['category']}]"
                f"({trimmedFile})"
            )
        newInfo = self._splitIndexToRunInfo[index]
        if oldInfo["count"] != newInfo["count"]:
            self.adjustAllTimes(newSaveData, oldInfo, newInfo)
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.notifyListeners({
            "type": "subrunChanged",
            "data": index
        })
        self.notifyListeners({
            "type": "splitNameUpdated",
            "data": {
                "index": index,
                "name": newSaveData["splitNames"][index]
            }
        })

    def updateCollapseState(self, index, collapsed):
        newSaveData = self.currentSaveDataSafe()
        oldMd = self.parseMarkdown(newSaveData["splitNames"][index])
        if not oldMd["isMd"]:
            return
        if collapsed == oldMd["collapsed"]:
            return
        trimmedName = (
            oldMd['groupName'][:-1]
            if collapsed
            else oldMd['groupName'] + '*'
        )
        newSaveData["splitNames"][index] = (
            f"({trimmedName})[{oldMd['fileName']}]"
        )
        self._dataCache.updateSaveData(
            self._splitFile,
            newSaveData,
            "edit"
        )
        self.parseSplits()
        self.notifyListeners({
            "type": "collapsedChanged",
            "data": {
                "index": index,
                "collapsed": collapsed
            },
        })
