from util import fileio
from util import readConfig as rc

class State:
    started = False
    staticStartTime = None
    paused = False
    runEnded = False

    starttime = 0
    segmentTime = 0
    totalTime = 0

    splitnum = 0
    # splitnames = []
    # numSplits = 0

    # game = ""
    # category = ""

    # saveData = SplitJson

    # config = None

    unSaved = False

    def __init__(self, splitFile):
        self.config = rc.getUserConfig()
        self.splitFile = splitFile
        self.saveData = fileio.readSplitFile(splitFile)

    def loadSplits(self, saveData):
        self.saveData = saveData
        self.game = saveData["game"]
        self.category = saveData["category"]
        self.splitnames = saveData["splitNames"]
        self.numSplits = len(self.splitnames)

    def _cleanState(self):
        self.started = False
        self.paused = False
        self.runEnded = False

        self.starttime = 0
        self.segmentTime = 0
        self.totalTime = 0

        self.splitnum = 0

    def frameUpdate(self):
        pass

    def onStarted(self):
        pass

    def onSplit(self):
        pass

    def onComparisonChanged(self,_):
        pass

    def onPaused(self):
        pass

    def onSplitSkipped(self):
        pass

    def onReset(self):
        pass
        
    def onRestart(self):
        pass

    def saveTimes(self):
        pass

    def shouldFinish(self):
        return True
