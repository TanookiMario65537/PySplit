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


# saveData = {
#     "game": "Test",
#     "category": "Test",
#     "splitNames": ["1", "2", "3"],
#     "defaultComparisons": "asdf",
#     "customComparisons": [
#         {
#             "name": "asdf",
#             "segments": ["12:12:12.12345", "12.12345", "12:12.12345"],
#             "totals": ["12.12345", "12.12345", "12.12345"]
#         }
#     ],
#     "runs": [
#         {
#             "startTime": "2023-11-13T14:55:44.581426-05:00",
#             "endTime": "2023-11-13T15:02:44.581426-05:00",
#             "segments": ["12.12345", "12.12345", "12.12345"],
#             "totals": ["12.12345", "12.12345", "-"]
#         }
#     ]
# }
# validateSave(saveData)
