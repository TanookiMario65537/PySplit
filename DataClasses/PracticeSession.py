import os
from Dialogs import PracticeRunSelector
from Dialogs import AddRun
from Dialogs import fileDialogs
from util import fileio
from util import readConfig as rc


class Session:
    split: str
    config: dict
    saveFile: str
    splitFile: str

    def __init__(self):
        self.config = rc.getUserConfig()
        if not fileio.hasSplitFile(self.config["baseDir"]):
            AddRun.SplitEditorD().show()
        self.saveFile = self.config["baseDir"] + "/.practiceSave"
        self.splitFile = ""
        self.split = ""
        self.exit = False
        if os.path.exists(self.saveFile):
            if not self.loadSave():
                self.getSession()
        else:
            self.getSession()

    def loadSave(self):
        saved = fileio.readJson(self.saveFile)
        if ("splitFile" not in saved.keys()) or ("split" not in saved.keys()):
            return False
        self.setRun(saved["splitFile"])
        self.setSplit(saved["split"])
        return True

    def save(self):
        fileio.writeJson(self.saveFile, {
            "splitFile": self.splitFile,
            "split": self.split
        })

    def getSession(self):
        splitFile = fileDialogs.chooseRun(self.config)
        if not splitFile:
            self.exit = True
            return
        self.setRun(splitFile)
        PracticeRunSelector.RunSelector(self.splitFile, self._setSplit).show()

    def setRun(self, splitFile):
        if not os.path.exists(splitFile):
            return
        self.splitFile = splitFile

    def _setSplit(self, retVal):
        self.setSplit(retVal["split"])

    def setSplit(self, splitName):
        self.split = splitName
