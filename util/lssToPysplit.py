import xml.etree.ElementTree as ET
from util import timeHelpers as timeh
import json
import datetime
from DataClasses import SyncedTimeList as STL


def realTimeToTime(realTime):
    if realTime is None:
        return "-"
    return lssToSplitTime(realTime.text)


def lssToSplitTime(lssTime):
    time = lssTime[:14]
    if time[0] != "0":
        return time
    if time[1] != "0":
        return time[1:]
    if time[3] != "0":
        return time[3:]
    if time[4] != "0":
        return time[4:]
    if time[6] != "0":
        return time[6:]
    return time[7:]


def convertName(name):
    if "{" in name and "}" in name and name.startswith("{"):
        parts = name.split("}")
        return "- " + "}".join(parts[1:]) + parts[0] + "}"
    return name


def lssToDatetime(lssString):
    return datetime.datetime.strptime(lssString, "%m/%d/%Y %H:%M:%S")


def getTimeInfo(root):
    segments = []
    names = []
    runTimeMaps = []
    compTimeMaps = []
    for segment in root.findall('./Segments/Segment'):
        segments.append(segment)
        names.append(convertName(segment.find('./Name').text))
        history = segment.find('./SegmentHistory')
        idToTime = {}
        for time in history.findall('./Time'):
            idToTime[time.attrib["id"]] = time.find('./RealTime')
        runTimeMaps.append(idToTime)
        compToTime = {}
        segmentTimes = segment.find('./SplitTimes')
        for segmentTime in segmentTimes.findall('./SplitTime'):
            compToTime[segmentTime.attrib["name"]] =\
                segmentTime.find('./RealTime')
        compTimeMaps.append(compToTime)

    runKeys, runTimeMaps = fillTimes(runTimeMaps)
    compKeys, compTimeMaps = fillTimes(compTimeMaps)
    return {
        "names": names,
        "runs": {
            "keys": runKeys,
            "timeMap": runTimeMaps
        },
        "comps": {
            "keys": compKeys,
            "timeMap": compTimeMaps
        }
    }


def fillTimes(timeMaps):
    keys = []
    for compMap in timeMaps:
        for key in compMap.keys():
            if key not in keys:
                keys.append(key)
    for i, compMap in enumerate(timeMaps):
        for key in keys:
            if key not in compMap:
                compMap[key] = None
            timeMaps[i][key] = realTimeToTime(compMap[key])
    return keys, timeMaps


def getAttemptInfo(root):
    attemptInfo = {}
    for attempt in root.findall('./AttemptHistory/Attempt'):
        start = lssToDatetime(
            attempt.attrib["started"]).astimezone(datetime.timezone.utc)
        end = lssToDatetime(
            attempt.attrib["ended"]).astimezone(datetime.timezone.utc)
        attemptInfo[attempt.attrib["id"]] = {
            "start": start.isoformat(timespec="microseconds"),
            "end": end.isoformat(timespec="microseconds"),
            "totalTime": timeh.timeToString((end-start).total_seconds()),
        }
    return attemptInfo


def getGoldTimes(names, runs):
    run_stls = []
    for run in runs:
        run_stls.append(STL.SyncedTimeList(totals=run["totals"]))

    gold_list = []
    for i in range(len(names)):
        gold_list.append(
            timeh.timeToString(
                timeh.listMin([stl.segments[i] for stl in run_stls])))
    return gold_list


def mergeRuns(r1, r2):
    a = []
    for b1, b2 in zip(r1["totals"], r2["totals"]):
        a.append(b2 if b1 == "-" else b1)
    return {
        "sessions": r1["sessions"] + r2["sessions"],
        "playTime": timeh.timeToString(
            timeh.stringToTime(r1["playTime"])
            + timeh.stringToTime(r2["playTime"])),
        "totals": a
    }


def mergeAllRuns(runs, mergeLists):
    mergedRuns = []
    runCount = 0
    i = 0
    while i < len(runs):
        if runCount >= len(mergeLists) or i < int(mergeLists[runCount][0]) - 1:
            mergedRuns.append(runs[i])
        else:
            merged = runs[i]
            i += 1
            while i < int(mergeLists[runCount][1]):
                merged = mergeRuns(merged, runs[i])
                i += 1
            mergedRuns.append(merged)
        i += 1
    return mergedRuns


def parseXML(xmlfile, mergeList):
    # create element tree object
    tree = ET.parse(xmlfile)

    # get root element
    root = tree.getroot()

    # create empty list for news items
    numAttempts = int(root.find('./AttemptCount').text)
    defaults = {}

    attemptInfo = getAttemptInfo(root)
    timeInfo = getTimeInfo(root)
    names = timeInfo["names"]
    runTimeMaps = timeInfo["runs"]["timeMap"]
    compKeys = timeInfo["comps"]["keys"]
    compTimeMaps = timeInfo["comps"]["timeMap"]

    runs = []
    for i in range(1, numAttempts+1):
        run = []
        totalTime = 0
        key = str(i)
        for timeMap in runTimeMaps:
            currentTime = timeh.stringToTime(timeMap[key])
            if not timeh.isBlank(currentTime):
                totalTime += currentTime
                run.append(timeh.timeToString(totalTime))
            else:
                run.append(timeh.timeToString(timeh.blank()))
        runs.append({
            "sessions": [{
                "startTime": attemptInfo[key]["start"],
                "endTime": attemptInfo[key]["end"]
            }],
            "playTime": attemptInfo[key]["totalTime"],
            "totals": run
        })
    runs = mergeAllRuns(runs, mergeList)

    gold_list = getGoldTimes(names, runs)

    defaults["bestSegments"] = {
        "name": "Best Segment",
        "segments": gold_list
    }

    compList = []
    for key in compKeys:
        run = []
        for timeMap in compTimeMaps:
            currentTime = timeh.stringToTime(timeMap[key])
            if not timeh.isBlank(currentTime):
                run.append(timeh.timeToString(currentTime))
            else:
                run.append(timeh.timeToString(timeh.blank()))
        if key == "Personal Best":
            defaults["bestRun"] = {
                "name": key,
                "totals": run
            }
        else:
            compList.append({
                "name": key,
                "totals": run
            })

    return {
        "version": "1.3",
        "offset": lssToSplitTime(root.find('./Offset').text),
        "game": root.find('./GameName').text,
        "category": root.find('./CategoryName').text,
        "splitNames": names,
        "defaultComparisons": defaults,
        "customComparisons": compList,
        "runs": runs
    }


if __name__ == "__main__":
    import argparse
    import os
    import sys

    def writeJson(filepath, data):
        with open(filepath, 'w') as writer:
            data = writer.write(json.dumps(data, indent=4))

    parser = argparse.ArgumentParser(
        description="Convert .lss files to .pysplit")
    parser.add_argument(
        'infile',
        type=str,
        help='The input .lss file to convert')
    parser.add_argument(
        '-o',
        "--output",
        type=str,
        required=False,
        metavar="outfile",
        help='The output file for the resulting .pysplit')
    parser.add_argument(
        "-r",
        "--run",
        type=str,
        required=False,
        help="The run to pull out")
    parser.add_argument(
        "-m",
        "--merge",
        type=str,
        required=False,
        help="""The groups of runs to merge. Has the format
'<merge start 1>/<merge end 1>,<merge start 2>/<merge end 2>,etc.""")
    args = parser.parse_args()

    if not os.path.exists(args.infile):
        print(f"File {args.infile} does not exist.")
        sys.exit(1)

    if args.merge:
        mergeList = [pair.split("/") for pair in args.merge.split(",")]
    else:
        mergeList = []
    if args.output:
        writeJson(args.output, parseXML(args.infile, mergeList))
    else:
        print(parseXML(args.infile, mergeList))
