from util import timeHelpers as timeh
import copy

##########################################################
## Reads a column of times in from a specified data table
##
## Parameters: col - the column to read
##             data_ref - the array to read from
##########################################################
def getTimesByCol(col,data_ref):
    times = []
    for i in range(1,len(data_ref)):
        times.append(timeh.stringToTime(data_ref[i][col]))
    return times

##########################################################
## Replaces the elements of a data table, starting with a 
## specified column.
## 
## Parameters: lines - the new data to put in
##             startIndex - the column to start replacing at
##             data_ref - the CSV to replace data in
##########################################################
def replaceCols(lines,startIndex,data_ref):
    for i in range(1,len(data_ref)):
        for j in range(len(lines)):
            data_ref[i][startIndex+j]=lines[j][i-1]

##########################################################
## Inserts new lines into a data table, starting with a
## specified column.
##
## Parameters: lines - the new data to put in
##             startIndex - the column to start inserting at
##########################################################
def insertCols(lines,startIndex,data_ref):
    for i in range(1,len(data_ref)):
        for j in range(len(lines)):
            data_ref[i].insert(startIndex+j,lines[j][i-1])

##########################################################
## Inserts a run into a data table as the second and third
## columns.
##
## Parameters:
##   run - the run to insert
##   data_ref - the data table to insert the run into
##########################################################
def insertRun(run,data_ref):
    lastRun = [timeh.timesToStringList(run.segments,{"precision":5}),timeh.timesToStringList(run.totals,{"precision":5})]
    data_ref[0].insert(1,"Run #"+str(int((len(data_ref[1])+1)/2)))
    data_ref[0].insert(2,"Totals")
    insertCols(lastRun,1,data_ref)

##############################################################
## Inserts a SumList object into the data_ref table as two
## columns, starting with startIndex.
##
## Parameters: sumList: the SumList object to insert into the
##                      table
##             key - the default comparison to replace
##             data_ref - the overall splits
##             options - the options for converting the times
##                       into strings
##
## Returns: None
##############################################################
def replaceSumList(sumList,key,data_ref,options={}):
    data_ref["defaultComparisons"][key]["segments"] = [timeh.timeToString(time,options) for time in sumList.bests]
    data_ref["defaultComparisons"][key]["totals"] = [timeh.timeToString(time,options) for time in sumList.totalBests]

##############################################################
## Inserts a SumList object into the data_ref table as two
## columns, starting with startIndex.
##
## Parameters: comparison: the Comparison object to insert into the
##                         table
##             key - the default comparison to replace
##             data_ref - the overall splits
##             options - the options for converting the times
##                       into strings
##
## Returns: None
##############################################################
def replaceComparison(comparison,key,data_ref,options={}):
    data_ref["defaultComparisons"][key]["segments"] = [timeh.timeToString(time,options) for time in comparison.segments]
    data_ref["defaultComparisons"][key]["totals"] = [timeh.timeToString(time,options) for time in comparison.totals]

##############################################################
## Changes the names in the first column of the table in
## data_ref, adding and removing rows from the table if the
## lists of names do not have the same length.
##
## Parameters: names - a list of the new names
##             data_ref - the data table to update
##
## Returns: A deep copy of the original data, with the names
##          updated.
##############################################################
def adjustNames(names,data_ref):
    new_data = copy.deepcopy(data_ref)
    for i in range(1,len(names)+1):
        if i >= len(new_data):
            row = [names[i-1]]
            row.extend(['-' for _ in range(len(new_data[0])-1)])
            new_data.append(row)
        else:
            new_data[i][0] = names[i-1]
    return new_data[:len(names)+1]

##############################################################
## Changes the names in the first column of the table in
## data_ref, adding and removing rows from the table if the
## lists of names do not have the same length.
##
## Parameters: names - a list of the new names
##             data - the JSON data to update
##
## Returns: None, updates are done in place.
##############################################################
def adjustNamesJson(names, data):
    for key in ["defaultComparisons"]:
        for ckey in data[key]:
            for t in ["segments", "totals"]:
                if len(data[key][ckey][t]) < len(names):
                    data[key][ckey][t].extend(['-' for _ in range(len(data[key][ckey][t])-1)])
                else:
                    data[key][ckey][t] = data[key][ckey][t][:len(names)]

    for key in ["customComparisons", "runs"]:
        for i in range(len(data[key])):
            for t in ["segments", "totals"]:
                if len(data[key][i][t]) < len(names):
                    data[key][i][t].extend(['-' for _ in range(len(data[key][i][t])-1)])
                else:
                    data[key][i][t] = data[key][i][t][:len(names)]

##############################################################
## Changes the names in the first column of the table in
## data_ref, adding and removing rows from the table if the
## lists of names do not have the same length.
##
## Parameters: names - a list of the new names
##             data_ref - the data table to update
##
## Returns: A deep copy of the original data, with the names
##          updated.
##############################################################
def adjustNamesMismatch(names,data_ref,originals):
    new_data = [copy.deepcopy(data_ref[0])]
    for i in range(len(names)):
        if i in originals:
            new_data.append(copy.deepcopy(data_ref[originals.index(i)+1]))
        else:
            new_data.append([names[i]]+['-' for _ in range(len(new_data[0])-1)])
    return new_data

def newCompleteCsv(names=[]):
    data = [['Split Names']]
    for name in names:
        data.append([name])
    return data

def newComparisons(names=[]):
    data = {
        "splitNames": names,
        "defaultComparisons": {
            "bestSegments": {
                "name": "Best Segments",
                "segments": ['-' for _ in range(len(names))],
                "totals": ['-' for _ in range(len(names))]
            },
            "bestRun": {
                "name": "Personal Best",
                "segments": ['-' for _ in range(len(names))],
                "totals": ['-' for _ in range(len(names))]
            },
            "average": {
                "name": "Average",
                "segments": ['-' for _ in range(len(names))],
                "totals": ['-' for _ in range(len(names))]
            },
            "bestExits": {
                "name": "Best Exits",
                "segments": ['-' for _ in range(len(names))],
                "totals": ['-' for _ in range(len(names))]
            },
            "blank": {
                "name": "Blank",
                "segments": ['-' for _ in range(len(names))],
                "totals": ['-' for _ in range(len(names))]
            }
        },
        "customComparisons": []
    }
    return data
