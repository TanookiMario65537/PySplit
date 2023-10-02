from util import fileio
from util import timeHelpers as timeh
from util import readConfig as rc
global varianceList


def getRows(saveData):
    rows = []
    for i in range(len(saveData["splitNames"])):
        timeList = []
        for j in range(len(saveData["runs"])):
            time = timeh.stringToTime(saveData["runs"][j]["segments"][i])
            if not timeh.isBlank(time):
                timeList.append(time)
        rows.append(timeList)
    return rows


def sort(i):
    return varianceList[i]


def createTable(names, variances, sort):
    table = []
    for i in sort:
        table.append([names[i], variances[i]])
    return table


def computeVariances(game, category, splits):
    global varianceList
    config = rc.getUserConfig()
    splitNames = splits.getSplitNames(game, category)
    saveData = fileio.readSplitFile(
        config["baseDir"],
        game,
        category,
        splitNames)
    timeRows = getRows(saveData)
    varianceList = []
    for row in timeRows:
        if not len(row):
            continue
        avg = sum(row)/len(row)
        varList = [(x-avg)**2 for x in row]
        variance = sum(varList)/len(varList)
        varianceList.append(variance/avg)
    sortedRange = sorted(
        list(range(len(varianceList))),
        key=sort,
        reverse=True)

    return {
        "order": createTable(
            splitNames,
            varianceList,
            range(len(varianceList))),
        "sorted": createTable(
            splitNames,
            varianceList,
            sortedRange)
    }
