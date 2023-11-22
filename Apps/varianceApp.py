# Run tkinter code in another thread

import tkinter as tk
import threading
from Components import VarianceColumn
from Dialogs import fileDialogs
from util import readConfig as rc
from util import varianceCalculator as varcalc

class App(threading.Thread):
    def __init__(self):
        super().__init__()

    ##########################################################
    ## Creates the window with the destruction callback, and
    ## sets control callbacks.
    ##########################################################
    def setupGui(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.title("Variance Calculator")
        self.config = rc.getUserConfig()

        self.button = tk.Button(
            self.root,
            text="Choose Run",
            bg="steelblue",
            command=self.chooseRun)
        self.button.pack(side="bottom", fill="both")

        self.base = VarianceColumn.VarianceColumn(self.root,"In Order")
        self.sort = VarianceColumn.VarianceColumn(self.root,"Sorted")
        self.base.pack(side="left")
        self.sort.pack(side="right")
        self.root.configure(bg="black")

    def chooseRun(self,_=None):
        splitFile = fileDialogs.chooseRun(self.config)
        if splitFile:
            variances = varcalc.computeVariances(splitFile)
            self.showVariances(variances["order"],variances["sorted"])

    ##########################################################
    ## Show the window, and call the first update after one
    ## frame.
    ##########################################################
    def startGui(self):
        self.root.mainloop()

    def showVariances(self,variance,sort):
        self.base.update(variance)
        self.sort.update(sort)
