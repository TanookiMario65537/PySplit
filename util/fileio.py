import os, csv, json
from util import dataManip
from util import validation
from pydantic import ValidationError

def resolveFilename(arr):
    return "/".join(arr)

def getDir(string):
    return resolveFilename(string.split("/")[:-1])

def readSplitFile(baseDir,name,category,splitList):
    splitFileName = resolveFilename([baseDir,name,category + ".pysplit"])
    if not os.path.exists(splitFileName):
        if not os.path.isdir(resolveFilename([baseDir,name])):
            os.mkdir(resolveFilename([baseDir,name]))
        splits = {
            "game": name,
            "category": category,
            "runs": []
        }.update(dataManip.newComparisons(splitList))
        if name and category:
            writeJson(splitFileName, splits)

    else:
        splits = readJson(splitFileName)
        dataManip.adjustNamesJson(splitList, splits)

    return splits

def writeCSVs(baseDir,name,category,splitWrite,comparesWrite):
    if splitWrite:
        writeCSV(resolveFilename([baseDir,name,category + ".csv"]),splitWrite)
    if comparesWrite:
        writeCSV(resolveFilename([baseDir,name,category + "_comparisons.csv"]),comparesWrite)

def writeCSV(filename,rows):
    if not os.path.exists(getDir(filename)):
        os.mkdir(getDir(filename))
    with open(filename,'w') as writer:
        csvWriter = csv.writer(writer, delimiter = ',')
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
    with open(filepath,'r') as reader:
        data = json.load(reader)
    return data

def writeJson(filepath,data):
    jsonData = json.dumps(data, indent=4)
    with open(filepath,'w') as writer:
        writer.write(jsonData)

def writeSplitFile(baseDir, name, category ,data):
    filepath = resolveFilename([baseDir,name,category + ".pysplit"])
    try:
        validation.validateSave(data)
        writeJson(filepath, data)
    except ValidationError as err:
        filepath = filepath + ".error"
        print(err)
        print()
        print("Saving data under " + filepath)
        writeJson(filepath, data)

def readCsv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath,'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=",",quotechar="|")
        csvlines = []
        for row in reader:
            csvlines.append(stripEmptyStringsReturn(row))
    return csvlines

def getLayouts():
    if os.path.exists("layouts"):
        layoutFiles = [f[:-5] for f in os.listdir("layouts")]
        layoutFiles.insert(0,"System Default")
    else:
        layoutFiles = ["System Default"]
    return layoutFiles

def removeCategory(baseDir,game,category):
    csvName = resolveFilename([baseDir,game,category + ".csv"])
    compareCsvName = resolveFilename([baseDir,game,category + "_comparisons.csv"])
    os.remove(csvName)
    os.remove(compareCsvName)
