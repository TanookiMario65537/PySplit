import copy
import re
from util import fileio


class SaveData:
    def __init__(self, groupName, splitFile, startSplit):
        self._startSplit = startSplit
        self._groupName = groupName
        self._splitFile = splitFile
        if self._splitFile:
            self._saveData = fileio.readSplitFile(self._splitFile)
        else:
            self._saveData = fileio.newComparisons()
        self.parseSplits()

    def parseSplits(self):
        self._splits = []
        self._subruns = []
        for splitName in self._saveData["splitNames"]:
            mdMatch = re.match(r'^\(([^\)]+)\)\[([^]]+)\]$', splitName)
            if mdMatch is not None:
                self._subruns.append(SaveData(
                    mdMatch.group(1),
                    mdMatch.group(2),
                    len(self._splits)
                ))
                if len(self._splits):
                    previousSplit = self._splits[-1]
                    startIndex = previousSplit.index + 1
                    startCollectibles = previousSplit.collectibleCount
                else:
                    startIndex = 0
                    startCollectibles = 0
                for i, split in enumerate(self._subruns[-1]._splits):
                    newSplit = copy.copy(split)
                    newSplit.update_props(**{
                        "index": startIndex + i,
                        "collectibleCount": startCollectibles + newSplit.collectibleCount,
                        "inGroup": True,
                        "groupName": mdMatch.group(1),
                        "isGroupEnd": i == self._subruns[-1].count - 1
                    })
                    self._splits.append(newSplit)
            else:
                self._splits.append(Split(len(self._splits), splitName))
                if self._splits[-1].collectibleCount is None:
                    self._splits[-1].collectibleCount = (
                        self._splits[-1].collectibleCount
                        if len(self._splits) > 1
                        else 0
                    )

    @property
    def count(self) -> int:
        return len(self._saveData["splitNames"])

    @property
    def groupName(self) -> str:
        return self._groupName

    @property
    def splitNames(self) -> list[str]:
        return [str(split) for split in self._splits]

    def updateSaveData(self, newSaveData: dict) -> None:
        self._saveData = copy.deepcopy(newSaveData)


class Split:
    def __init__(self, index, name):
        self._name = name
        self.index = index
        match = re.match(r'(.*)\[P\]', name)
        self.pauseAtEnd = match is not None
        match = re.match(r'(.*)\[(d+)\]', name)
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
        self.trimmedName = (name[2:] if self.inGroup else name[:]).replace(
            "[P]", ""
        ).replace(
            f"[{self.collectibleCount}]"
            if self.collectibleCount is not None
            else "",
            ""
        ).replace(
            "{"f"{self.groupName}""}", ""
        )
        self.update_repr()

    def __copy__(self):
        newObj = type(self)(self.index, self._name)
        newObj.update_props(**{
            "_name": self._name,
            "index": self.index,
            "pauseAtEnd": self.pauseAtEnd,
            "collectibleCount": self.collectibleCount,
            "showCollectibleCount": self.showCollectibleCount,
            "inGroup": self.inGroup,
            "isGroupEnd": self.isGroupEnd,
            "groupName": self.groupName,
            "trimmedName": self.trimmedName,
        })
        return newObj

    def __str__(self):
        return self._repr

    def update_props(self, **kwargs):
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)
            else:
                raise AttributeError(f"Split has no property {key}.")
        self.update_repr()

    def update_repr(self):
        self._repr = ""
        self._repr += "- " if self.inGroup else ""
        self._repr += f"{self.trimmedName}"
        self._repr += " [P]" if self.pauseAtEnd else ""
        self._repr += (
            f" [{self.collectibleCount}]"
            if self.showCollectibleCount and not self.pauseAtEnd
            else ""
        )
        self._repr += " {" + self.groupName + "}" if self.isGroupEnd else ""
