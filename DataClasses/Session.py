import os
from util import fileio
from util import layoutHelper as lh
from util import readConfig as rc
from Dialogs import AddRun
from Dialogs import fileDialogs
from Dialogs import LayoutPopup


class Session:
    config: dict
    layout: list
    layoutName: str
    saveFile: str
    splitFile: str

    def __init__(self):
        self.config = rc.getUserConfig()
        if not fileio.hasSplitFile(self.config["baseDir"]):
            AddRun.SplitEditorD().show()
        self.saveFile = self.config["baseDir"] + "/.save"
        self.layoutName = "System Default"
        self.splitFile = ""
        self.exit = False
        if os.path.exists(self.saveFile):
            self.loadSave()
        else:
            self.getSession()

    def loadSave(self):
        saved = fileio.readJson(self.saveFile)
        if os.path.exists(saved["splitFile"]):
            self.setRun(saved["splitFile"])
            self.setLayout(saved["layoutName"])
        else:
            self.getSession()

    def save(self):
        fileio.writeJson(self.saveFile, {
            "splitFile": self.splitFile,
            "layoutName": self.layoutName
        })

    def getSession(self):
        splitFile = fileDialogs.chooseRun(self.config)
        if not splitFile:
            self.exit = True
        self.setRun(splitFile)
        LayoutPopup.LayoutDialog(self._setLayout, self).show()

    def setRun(self, splitFile):
        if not os.path.exists(splitFile):
            return
        self.splitFile = splitFile

    def _setLayout(self, retVal):
        self.setLayout(retVal["layoutName"])

    def setLayout(self, layoutName):
        if not layoutName:
            return
        self.layoutName = layoutName
        self.layout = lh.resolveLayout(self.layoutName)
