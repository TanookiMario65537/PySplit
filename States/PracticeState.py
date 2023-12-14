from timeit import default_timer as timer
from util import fileio
from util import timeHelpers as timeh
from States import BaseState


class State(BaseState.State):
    # bestTime = 0
    currentTime = 0
    # splitName = ""
    # splitnum = 0

    def __init__(self, session):
        super().__init__(session.splitFile)
        super().loadSplits(self.saveData)
        self.splitName = session.split
        self.splitnum = self.splitnames.index(session.split)
        self.bestTime = timeh.stringToTime(
            self.saveData["defaultComparisons"]["bestSegments"]["segments"][self.splitnum])
        self.unSaved = False

    def frameUpdate(self):
        if not (self.started and not self.runEnded):
            return 1
        self.segmentTime = timer() - self.starttime

    ##########################################################
    # Do the state update when the run starts
    ##########################################################
    def onStarted(self):
        self.starttime = timer()
        self.started = True
        self.runEnded = False

    ##########################################################
    # Do the state update when the split is ended
    #
    # Parameters: time - the time the split was ended
    ##########################################################
    def onSplit(self):
        self.runEnded = True
        splitTime = timer() - self.starttime
        self.currentTime = splitTime
        self.unSaved = True
        if timeh.greater(self.bestTime, splitTime):
            self.bestTime = splitTime
        self.unSaved = True
        return 4

    ##########################################################
    # Restart the run
    ##########################################################
    def onRestart(self):
        self.started = False

    ##########################################################
    # Save the times when we close the window.
    ##########################################################
    def saveTimes(self):
        self.saveData["defaultComparisons"]["bestSegments"]["segments"][self.splitnum] =\
            timeh.timeToString(self.bestTime)

        fileio.writeSplitFile(
            self.splitFile,
            self.saveData)
        self.unSaved = False

    def hasPartialSave(self):
        return False

    def saveType(self):
        return 2 if self.unSaved else 0
