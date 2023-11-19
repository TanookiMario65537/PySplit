from typing import List, Annotated
from pydantic import BaseModel, Field


Time = Annotated[str, Field(pattern=r'^(((\d+:)?(\d?\d:))?\d)?\d.\d{5}$|^-$')]
DateTime = Annotated[
    str,
    Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2]\d|3[0-1])T([0-1]\d|2[0-3]):[0-5]\d:[0-5]\d.\d{6}([-+]\d{2}:\d{2})?$')]


class Comparison(BaseModel):
    name: str
    segments: List[Time]
    totals: List[Time]


class Run(BaseModel):
    startTime: DateTime
    endTime: DateTime
    segments: List[Time]
    totals: List[Time]


class DefaultComparisons(BaseModel):
    bestSegments: Comparison
    bestRun: Comparison
    average: Comparison
    bestExits: Comparison
    blank: Comparison


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
