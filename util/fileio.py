import os
import csv
import json
from util import validation
from pydantic import ValidationError
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def resolveFilename(arr):
    return "/".join(arr)


def getDir(string):
    return resolveFilename(string.split("/")[:-1])


def readSplitFile(splitFileName):
    saveData = readJson(splitFileName)
    if saveData:
        return validation.updateSave(saveData)
    return newComparisons()


def writeCSVs(baseDir, name, category, splitWrite, comparesWrite):
    if splitWrite:
        writeCSV(
            resolveFilename([baseDir, name, category + ".csv"]),
            splitWrite
        )
    if comparesWrite:
        writeCSV(
            resolveFilename([baseDir, name, category + "_comparisons.csv"]),
            comparesWrite
        )


def writeCSV(filename, rows):
    if not os.path.exists(getDir(filename)):
        os.mkdir(getDir(filename))
    with open(filename, 'w') as writer:
        csvWriter = csv.writer(writer, delimiter=',')
        for thing in rows:
            csvWriter.writerow(thing)


def stripEmptyStrings(stringList):
    while not stringList[-1]:
        stringList.pop(-1)


def stripEmptyStringsReturn(stringList):
    if not len(stringList):
        return []
    new = [stringList[i] for i in range(len(stringList))]
    while not new[-1]:
        new.pop(-1)
    return new


def readJson(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as reader:
        data = json.load(reader)
    return data


def writeJson(filepath, data):
    jsonData = json.dumps(data, indent=4)
    Path(os.path.dirname(filepath)).mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as writer:
        writer.write(jsonData)


def writeSplitFile(filepath, data):
    try:
        validation.validateSave(data)
        writeJson(filepath, data)
        logger.info("Saved data to " + filepath)
    except ValidationError as err:
        filepath = filepath + ".error"
        logger.error(err)
        writeJson(filepath, data)
        logger.info("Saved data to " + filepath)


def readCsv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar="|")
        csvlines = []
        for row in reader:
            csvlines.append(stripEmptyStringsReturn(row))
    return csvlines


def getLayouts():
    if os.path.exists("layouts"):
        layoutFiles = [f[:-5] for f in os.listdir("layouts")]

        layoutFiles.insert(0, "System Default")
    else:
        layoutFiles = ["System Default"]
    return layoutFiles


def removeCategory(baseDir, game, category):
    csvName = resolveFilename([baseDir, game, category + ".csv"])
    compareCsvName = resolveFilename(
        [baseDir, game, category + "_comparisons.csv"]
    )
    os.remove(csvName)
    os.remove(compareCsvName)


def hasSplitFile(baseDir):
    for root, dirs, files in os.walk(baseDir):
        for file in files:
            if file.endswith(".pysplit"):
                return True
    return False


def newComparisons(names=[]):
    """
    Creates a dictionary with a new collection of comparisons
    based on a spcified list of split names.

    Parameters: names - a list of the desired split names

    Returns: A dictionary containing splitNames,
             defaultComparisons, and customComparisons.
             defaultComparisons will be poplated automatically
             with the default comparison list, and each
             comparison will have the default name and segment
             and total lists with the number of blank splits
             matching the number of specified splits. Should
             be used with saveData.update(newComparisons()) or
             something similar.
    """
    data = {
        "version": "1.3",
        "offset": "0:00.00000",
        "game": "",
        "category": "",
        "splitNames": names,
        "defaultComparisons": {
            "bestSegments": {
                "name": "Best Segments",
                "segments": ['-' for _ in range(len(names))],
            },
            "bestRun": {
                "name": "Personal Best",
                "totals": ['-' for _ in range(len(names))]
            }
        },
        "customComparisons": [],
        "runs": []
    }
    return data
