import os, csv, json
from util import dataManip
from util import validation
from pydantic import ValidationError
from pathlib import Path

def resolveFilename(arr):
    return "/".join(arr)

def getDir(string):
    return resolveFilename(string.split("/")[:-1])

def readSplitFile(splitFileName):
    saveData = readJson(splitFileName)
    if saveData:
        return validation.updateSave(saveData)
    return dataManip.newComparisons()

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
    Path(os.path.dirname(filepath)).mkdir(parents=True, exist_ok=True)
    with open(filepath,'w') as writer:
        writer.write(jsonData)

def writeSplitFile(filepath, data):
    try:
        validation.validateSave(data)
        writeJson(filepath, data)
        print("Saved data to " + filepath)
    except ValidationError as err:
        filepath = filepath + ".error"
        print(err)
        print()
        writeJson(filepath, data)
        print("Saved data to " + filepath)

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

def hasSplitFile(baseDir):
    for root, dirs, files in os.walk(baseDir):
        for file in files:
            if file.endswith(".pysplit"):
                return True
    return False
