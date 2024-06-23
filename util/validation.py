from typing import List, Annotated
from pydantic import BaseModel, Field
from util import timeHelpers as timeh
import copy


versionList = ["1.0", "1.1", "1.2", "1.3"]
Time = Annotated[str, Field(pattern=r'^(((\d+:)?(\d?\d:))?\d)?\d.\d{5}$|^-$')]
DateTime = Annotated[
    str,
    Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2]\d|3[0-1])T([0-1]\d|2[0-3]):[0-5]\d:[0-5]\d.\d{6}([-+]\d{2}:\d{2})?$')]


class Comparison(BaseModel):
    name: str
    totals: List[Time]


class BestSegments(BaseModel):
    name: str
    segments: List[Time]


class PlaySession(BaseModel):
    startTime: DateTime
    endTime: DateTime


class Run(BaseModel):
    totals: List[Time]
    sessions: List[PlaySession]
    playTime: Time


class DefaultComparisons(BaseModel):
    bestSegments: BestSegments
    bestRun: Comparison


class SaveData(BaseModel):
    version: str
    game: str
    category: str
    splitNames: List[str]
    defaultComparisons: DefaultComparisons
    customComparisons: List[Comparison]
    runs: List[Run]


def validateSave(saveData):
    """
    Validates the save data. This mostly consists of making
    sure that everything has appropriate keys.

    Parameters: saveData - the save data to validate

    Returns: None

    Raises: ValidationError if the validation doesn't pass.
    """
    SaveData.model_validate(saveData)


def updateVersion(saveData, version):
    newSave = copy.deepcopy(saveData)
    newSave["version"] = version
    if version == "1.1":
        del newSave["defaultComparisons"]["average"]
        del newSave["defaultComparisons"]["bestExits"]
        del newSave["defaultComparisons"]["blank"]
        del newSave["defaultComparisons"]["bestSegments"]["totals"]
        del newSave["defaultComparisons"]["bestRun"]["segments"]
        for cmp in newSave["customComparisons"]:
            del cmp["segments"]
        for run in newSave["runs"]:
            del run["segments"]
    elif version == "1.2":
        newSave["offset"] = "0:00.00000"
    elif version == "1.3":
        for i, run in enumerate(newSave["runs"]):
            newSave["runs"][i]["sessions"] = [{
                "startTime": run["startTime"],
                "endTime": run["endTime"]
            }]
            del newSave["runs"][i]["startTime"]
            del newSave["runs"][i]["endTime"]
            all_times = list(filter(lambda x: x != "-", run["totals"]))
            newSave["runs"][i]["playTime"] = all_times[-1] if len(all_times) else timeh.timeToString(0)
    return newSave


def updateSave(saveData):
    for version in versionList[versionList.index(saveData["version"])+1:]:
        saveData = updateVersion(saveData, version)
    return saveData
