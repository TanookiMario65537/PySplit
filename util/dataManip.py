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
    lastRun = [timeh.timesToStringList(run.segments),timeh.timesToStringList(run.totals)]
    data_ref[0].insert(1,"Run #"+str(int((len(data_ref[1])+1)/2)))
    data_ref[0].insert(2,"Totals")
    insertCols(lastRun,1,data_ref)

##############################################################
## Inserts a SumList object into the defaultComparisons
## portion of the save data matching the specified key.
##
## Parameters: sumList: the SumList object to insert into the
##                      table
##             key - the default comparison to replace
##             saveData - the complete save data
##
## Returns: None
##############################################################
def replaceSumList(sumList,key,saveData):
    saveData["defaultComparisons"][key]["segments"] = [timeh.timeToString(time) for time in sumList.bests]
    saveData["defaultComparisons"][key]["totals"] = [timeh.timeToString(time) for time in sumList.totalBests]

##############################################################
## Inserts a Comparison object into the defaultComparisons
## portion of the save data matching the specified key
##
## Parameters: comparison: the Comparison object to insert into the
##                         table
##             key - the default comparison to replace
##             saveData - the overall splits
##
## Returns: None
##############################################################
def replaceComparison(comparison,key,saveData):
    saveData["defaultComparisons"][key]["segments"] = [timeh.timeToString(time) for time in comparison.segments]
    saveData["defaultComparisons"][key]["totals"] = [timeh.timeToString(time) for time in comparison.totals]

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
## Creates a dictionary with a new collection of comparisons
## based on a spcified list of split names.
##
## Parameters: names - a list of the desired split names
##
## Returns: A dictionary containing splitNames,
##          defaultComparisons, and customComparisons.
##          defaultComparisons will be poplated automatically
##          with the default comparison list, and each
##          comparison will have the default name and segment
##          and total lists with the number of blank splits
##          matching the number of specified splits. Should
##          be used with saveData.update(newComparisons()) or
##          something similar.
##############################################################
def newComparisons(names=[]):
    data = {
        "version": "1.1",
        "game": "",
        "category": "",
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
            }
        },
        "customComparisons": [],
        "runs": []
    }
    return data
