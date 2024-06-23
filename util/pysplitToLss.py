import datetime
import sys
import os
sys.path.insert(0, os.getcwd())
from DataClasses import SyncedTimeList as STL
from util import timeHelpers as timeh


def isoToLss(isostring):
    return datetime.datetime.fromisoformat(isostring).astimezone(datetime.timezone.utc).strftime("%m/%d/%Y %H:%M:%S")


def splitTimeToLss(timestring):
    zerostring = "00:00:00"
    cleaned = "0.00000" if timestring == "-" else timestring
    return zerostring[:14-len(cleaned)] + cleaned + "0000"


def attemptTag(run, id):
    if run["totals"][-1] != "-":
        return f"""        <Attempt id="{id}" started="{isoToLss(run["sessions"][0]["startTime"])}" isStartedSynced="False" ended="{isoToLss(run["sessions"][0]["endTime"])}" isEndedSynced="False"><RealTime>{splitTimeToLss(run["totals"][-1])}</RealTime></Attempt>"""
    else:
        return f"""        <Attempt id="{id}" started="{isoToLss(run["sessions"][0]["startTime"])}" isStartedSynced="False" ended="{isoToLss(run["sessions"][0]["endTime"])}" isEndedSynced="False"/>"""


def segmentHistoryTag(run, index, splitIndex):
    if timeh.isBlank(run.segments[splitIndex]):
        return None
    return f"""                <Time id="{index+1}"><RealTime>{splitTimeToLss(timeh.timeToString(run.segments[splitIndex]))}</RealTime></Time>"""


def comparisonTag(comparison, splitIndex):
    if comparison["totals"][splitIndex] == "-":
        return None
    return f"""                <SplitTime name="{comparison["name"]}"><RealTime>{splitTimeToLss(comparison["totals"][splitIndex])}</RealTime></SplitTime>"""


def combineTagList(tagList):
    return "\n".join(list(filter(lambda x: x is not None, tagList)))


def segmentTag(saveData, index):
    comparisons = combineTagList([comparisonTag(comparison, index) for i, comparison in enumerate([saveData["defaultComparisons"]["bestRun"]] + saveData["customComparisons"])])
    segmentTimes = combineTagList([segmentHistoryTag(run, i, index) for i, run in enumerate([STL.SyncedTimeList(totals=r["totals"])for r in saveData["runs"]])])
    return f"""        <Segment><Name>{saveData["splitNames"][index]}</Name><Icon/>
            <SplitTimes>
{comparisons}
            </SplitTimes>
            <BestSegmentTime><RealTime>{splitTimeToLss(saveData["defaultComparisons"]["bestSegments"]["segments"][index])}</RealTime></BestSegmentTime>
            <SegmentHistory>
{segmentTimes}
            </SegmentHistory>
        </Segment>"""


def pysplitToLss(saveData):
    attemptHistory = "\n".join([attemptTag(run, i+1) for i, run in enumerate(saveData["runs"])])
    segments = "\n".join([segmentTag(saveData, i) for i in range(len(saveData["splitNames"]))])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Run version="1.8.0">
    <GameIcon/>
    <GameName>{saveData["game"]}</GameName>
    <CategoryName>{saveData["category"]}</CategoryName>
    <Metadata><Run id=""/><Platform usesEmulator="False"/><Region/><SpeedrunComVariables/><CustomVariables/></Metadata>
    <LayoutPath/>
    <Offset>{splitTimeToLss(saveData["offset"])}</Offset>
    <AttemptCount>{len(saveData["runs"])}</AttemptCount>
    <AttemptHistory>
{attemptHistory}
    </AttemptHistory>
    <Segments>
{segments}
    </Segments>
    <AutoSplitterSettings/>
</Run>"""


if __name__ == "__main__":
    import argparse
    import os
    import json

    def readJson(filepath):
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as reader:
            data = json.load(reader)
        return data

    def writeXml(filepath, string):
        with open(filepath, 'w') as writer:
            writer.write(string)

    parser = argparse.ArgumentParser(
        description="Convert .pysplit files to .lss")
    parser.add_argument(
        'infile',
        type=str,
        help='The input .pysplit file to convert')
    parser.add_argument(
        '-o',
        "--output",
        type=str,
        required=False,
        metavar="outfile",
        help='The output file for the resulting .lss')
    args = parser.parse_args()

    saveData = readJson(args.infile)
    if not saveData:
        print(f"File {args.infile} does not exist.")
    else:
        if args.output:
            writeXml(args.output, pysplitToLss(saveData))
        else:
            print(pysplitToLss(saveData))
