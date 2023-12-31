"""
This must be run from the base directory, as the config paths are relative.
"""
import json
import os
import csv
import datetime
import re


def stripEmptyStringsReturn(stringList: list[str]) -> list[str]:
    if not len(stringList):
        return []
    new = [stringList[i] for i in range(len(stringList))]
    while not new[-1]:
        new.pop(-1)
    return new


def readJson(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as reader:
        data = json.load(reader)
    return data


def writeJson(filepath: str, data) -> None:
    jsonData = json.dumps(data, indent=4)
    with open(filepath, 'w') as writer:
        writer.write(jsonData)


def readCsv(filepath: str) -> list[list[str]]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar="|")
        csvlines = []
        for row in reader:
            csvlines.append(stripEmptyStringsReturn(row))
    return csvlines


def getUserConfig() -> dict:
    defaultConfig = readJson("defaults/global.json")
    if os.path.exists("config/global.json"):
        userConfig = readJson("config/global.json")
    else:
        userConfig = {}
    defaultConfig.update(userConfig)
    return defaultConfig


def stringToTime(timestring):
    parts1 = re.split("\.", timestring)
    parts2 = re.split(":", parts1[0])
    hours = 0
    mins = 0
    secs = 0
    fracsecs = 0
    if len(parts1) > 1:
        fracsecs = float("0."+parts1[1])
    if len(parts2) == 3:
        hours = int(parts2[0])
        mins = int(parts2[1])
        secs = int(parts2[2])
    elif len(parts2) == 2:
        mins = int(parts2[0])
        secs = int(parts2[1])
    else:
        secs = int(parts2[0])
    return 3600*hours + 60*mins + secs + fracsecs


def findFinalTime(runTotals: list[str]):
    finalIndex = len(runTotals) - 1
    while finalIndex >= 0 and runTotals[finalIndex] == "-":
        finalIndex -= 1
    if finalIndex == -1:
        return datetime.timedelta(seconds=1)
    else:
        return datetime.timedelta(seconds=stringToTime(runTotals[finalIndex]))


def convertSave(baseDir: str, game: str, category: str) -> None:
    runFilename = os.path.join(baseDir, game, category + ".csv")
    runFile = readCsv(runFilename)
    compFilename = os.path.join(baseDir, game, category + "_comparisons.csv")
    compFile = readCsv(compFilename)
    modifyDate = datetime.datetime.fromtimestamp(
        os.path.getmtime(runFilename)
    ).date()
    newSave = {
        "version": "1.0",
        "game": game,
        "category": category,
        "splitNames": [row[0] for row in runFile[1:]],
        "defaultComparisons": {
            "bestSegments": {
                "name": compFile[0][1],
                "segments": [compFile[j][1] for j in range(1, len(compFile))],
                "totals": [compFile[j][2] for j in range(1, len(compFile))],
            },
            "bestRun": {
                "name": compFile[0][5],
                "segments": [compFile[j][5] for j in range(1, len(compFile))],
                "totals": [compFile[j][6] for j in range(1, len(compFile))],
            },
            "average": {
                "name": compFile[0][3],
                "segments": [compFile[j][3] for j in range(1, len(compFile))],
                "totals": [compFile[j][4] for j in range(1, len(compFile))],
            },
            "bestExits": {
                "name": compFile[0][7],
                "segments": [compFile[j][7] for j in range(1, len(compFile))],
                "totals": [compFile[j][8] for j in range(1, len(compFile))],
            },
            "blank": {
                "name": compFile[0][9],
                "segments": [compFile[j][9] for j in range(1, len(compFile))],
                "totals": [compFile[j][10] for j in range(1, len(compFile))],
            },
        },
        "customComparisons": [
            {
                "name": compFile[0][i],
                "segments": [compFile[j][i] for j in range(1, len(compFile))],
                "totals": [compFile[j][i+1] for j in range(1, len(compFile))],
            } for i in range(11, len(compFile[0]), 2)
        ],
        "runs": [
            {
                "startTime": (
                    datetime.datetime.combine(
                        modifyDate,
                        datetime.datetime.min.time()
                    ) - datetime.timedelta(days=int((i-1)/2))
                ).isoformat() + ".000000",
                "endTime": (
                    datetime.datetime.combine(
                        modifyDate,
                        datetime.datetime.min.time()
                    ) - datetime.timedelta(days=int((i-1)/2))
                    + findFinalTime([runFile[j][i+1] for j in range(1, len(runFile))])
                ).isoformat(),
                "segments": [runFile[j][i] for j in range(1, len(runFile))],
                "totals": [runFile[j][i+1] for j in range(1, len(runFile))],
            } for i in range(1, len(runFile[0]), 2)
        ]
    }
    pysplitFilename = os.path.join(baseDir, game, category + ".pysplit")
    writeJson(pysplitFilename, newSave)


def main():
    baseDir = getUserConfig()["baseDir"]
    for root, dirs, files in os.walk(baseDir):
        for file in files:
            if file.endswith("_comparisons.csv"):
                category = file.split("_comparisons.csv")[0]
                game = root.split("/")[-1]
                convertSave(baseDir, game, category)


if __name__ == "__main__":
    main()
