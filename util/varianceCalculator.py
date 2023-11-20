from util import fileio
from util import timeHelpers as timeh
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


def computeVariances(filename):
    global varianceList
    saveData = fileio.readSplitFile(filename)
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
            saveData["splitNames"],
            varianceList,
            range(len(varianceList))),
        "sorted": createTable(
            saveData["splitNames"],
            varianceList,
            sortedRange)
    }
