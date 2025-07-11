import datetime
from DataClasses import SyncedTimeList as STL
from util import timeHelpers as timeh


def isoToLss(isostring):
    return (
        datetime.datetime
        .fromisoformat(isostring)
        .astimezone(datetime.timezone.utc).strftime("%m/%d/%Y %H:%M:%S")
    )


def addPlaytime(isostring, playTimeString):
    return (
        datetime.datetime.fromisoformat(isostring)
        + datetime.timedelta(seconds=timeh.stringToTime(playTimeString))
    ).isoformat(timespec="microseconds")


def splitTimeToLss(timestring):
    zerostring = "00:00:00"
    cleaned = "0.00000" if timestring == "-" else timestring
    return zerostring[:14-len(cleaned)] + cleaned + "0000"


def convertName(name):
    if "{" in name and "}" in name and name.startswith("- "):
        parts = name.split("{")
        return "{" + parts[1].split("}")[0] + "}" + parts[0][2:].strip()
    return name


def attemptTag(run, id):
    """
    Creates the appropriate LSS tag for a run.

    *Note*: Currently there is no LiveSplit support for multiple sessions, and
            therun.gg doesn't count runs over 4 days long towards play time.
            For now, just use `startTime + playTime` as the end time for the
            run to make stats work.
    """
    if run["totals"][-1] != "-":
        return (
            '        '
            '<Attempt '
            f'id="{id}" '
            f'started="{isoToLss(run["sessions"][0]["startTime"])}" '
            'isStartedSynced="False" '
            f'ended="{isoToLss(
                addPlaytime(
                    run["sessions"][0]["startTime"], run["playTime"]
                )
            )}" '
            'isEndedSynced="False"'
            '>'
            '<RealTime>'
            f'{splitTimeToLss(run["totals"][-1])}'
            '</RealTime>'
            '</Attempt>'
        )
    else:
        return (
            '        '
            '<Attempt '
            f'id="{id}" '
            f'started="{isoToLss(run["sessions"][0]["startTime"])}" '
            'isStartedSynced="False" '
            f'ended="{isoToLss(
                addPlaytime(
                    run["sessions"][0]["startTime"],
                    run["playTime"]
                )
            )}" '
            'isEndedSynced="False"'
            '/>'
        )


def segmentHistoryTag(run, index, splitIndex):
    if timeh.isBlank(run.segments[splitIndex]):
        return None
    return (
        '                '
        f'<Time id="{index+1}">'
        '<RealTime>'
        f'{splitTimeToLss(timeh.timeToString(run.segments[splitIndex]))}'
        '</RealTime>'
        '</Time>'
    )


def comparisonTag(comparison, splitIndex):
    if comparison["totals"][splitIndex] == "-":
        return f'                <SplitTime name="{comparison["name"]}"/>'
    return (
        '                '
        f'<SplitTime name="{comparison["name"]}">'
        '<RealTime>'
        f'{splitTimeToLss(comparison["totals"][splitIndex])}'
        '</RealTime>'
        '</SplitTime>'
    )


def combineTagList(tagList):
    return "\n".join(list(filter(lambda x: x is not None, tagList)))


def segmentTag(saveData, index):
    comparisonList = [saveData["defaultComparisons"]["bestRun"]]
    for comparison in saveData["customComparisons"]:
        if len(comparison["totals"]) == len(saveData["splitNames"]):
            comparisonList.append(comparison)
    comparisons = combineTagList(
        [
            comparisonTag(comparison, index)
            for i, comparison in enumerate(comparisonList)
        ]
    )
    segmentTimes = combineTagList(
        [
            segmentHistoryTag(run, i, index)
            for i, run in enumerate(
                [
                    STL.SyncedTimeList(totals=r["totals"])
                    for r in saveData["runs"]
                ]
            )
        ]
    )
    header = (
        '        '
        '<Segment>'
        '<Name>'
        f'{convertName(saveData["splitNames"][index])}'
        '</Name>'
        '<Icon/>'
    )
    return f"""{header}
            <SplitTimes>
{comparisons}
            </SplitTimes>
            <BestSegmentTime><RealTime>{splitTimeToLss(saveData["defaultComparisons"]["bestSegments"]["segments"][index])}</RealTime></BestSegmentTime>
            <SegmentHistory>
{segmentTimes}
            </SegmentHistory>
        </Segment>"""


def pysplitToLss(saveData):
    attemptHistory = "\n".join(
        [
            attemptTag(run, i+1)
            for i, run in enumerate(saveData["runs"])
        ]
    )
    segments = "\n".join(
        [
            segmentTag(saveData, i)
            for i in range(len(saveData["splitNames"]))
        ]
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Run version="1.8.0">
    <GameIcon/>
    <GameName>{saveData["game"]}</GameName>
    <CategoryName>{saveData["category"]}</CategoryName>
    <Metadata>
        <Run id=""/>
        <Platform usesEmulator="False"/>
        <Region/>
        <SpeedrunComVariables/>
        <CustomVariables/>
    </Metadata>
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
        description="Convert .pysplit files to .lss"
    )
    parser.add_argument(
        'infile',
        type=str,
        help='The input .pysplit file to convert'
    )
    parser.add_argument(
        '-o',
        "--output",
        type=str,
        required=False,
        metavar="outfile",
        help='The output file for the resulting .lss'
    )
    args = parser.parse_args()

    saveData = readJson(args.infile)
    if not saveData:
        print(f"File {args.infile} does not exist.")
    else:
        if args.output:
            writeXml(args.output, pysplitToLss(saveData))
        else:
            print(pysplitToLss(saveData))
