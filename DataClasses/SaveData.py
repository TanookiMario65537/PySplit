import copy
import re
from util import fileio


class SaveData:
    def __init__(self, groupName, splitFile, startSplit):
        self._startSplit = startSplit
        self._groupName = groupName
        self._root = self._groupName == ""
        self._splitFile = splitFile
        if self._splitFile:
            self._saveData = fileio.readSplitFile(self._splitFile)
        else:
            self._saveData = fileio.newComparisons()
        if self._root:
            self._adjustedSplitNames = []
        else:
            self._adjustedSplitNames = [
                self.adjustSplitName(splitName)
                for splitName in self._saveData["splitNames"]
            ]
            self._adjustedSplitNames[-1] = (
                self._adjustedSplitNames[-1] + " {" + self._groupName + "}"
            )

    def adjustSplitName(self, splitName: str) -> str:
        if not splitName.startswith("-"):
            splitName = "- " + splitName
        match = re.match(r'(.*)\{.*\}', splitName)
        if match is not None:
            splitName = match.group(1).strip()
        return splitName

    @property
    def count(self) -> int:
        return len(self._saveData["splitNames"])

    @property
    def groupName(self) -> str:
        return self._groupName

    @property
    def root(self) -> bool:
        return self._root

    @property
    def splitNames(self) -> list[str]:
        return (
            self._saveData["splitNames"]
            if self._root
            else self._adjustedSplitNames
        )

    def updateSaveData(self, newSaveData: dict) -> None:
        self._saveData = copy.deepcopy(newSaveData)
