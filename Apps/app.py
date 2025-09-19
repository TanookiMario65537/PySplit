# Run tkinter code in another thread

import tkinter as tk
import threading
from Components import MainMenu
from Dialogs import AddRun
from Dialogs import ConfirmPopup
from Dialogs import fileDialogs
from Dialogs import LayoutPopup
from Dialogs import PracticeRunSelector
from Dialogs import SplitEditor
from States import PracticeState
from States import State


class App(threading.Thread):
    # state = None
    # components = []
    # numWidgets = 0
    # session = None
    retVal = None
    updated = None
    initialLoad = True

    """
    GUI Setup
    """

    def __init__(self, state, session):
        """
        Initialize the app in a different thread than the state

        Parameters: state - the state of the program
                    session - the session info for the program
        """
        super().__init__()
        self.state = state
        self.session = session
        self.components = []
        self.numWidgets = 0

    def addWidget(self, component):
        """
        Add a component to the bottom of the app, and track the
        new component.

        Parameters: component - the component to add to the app.
                                Must extend the
                                WidgetBase.WidgetBase class so it
                                has the appropriate signals.
        """
        component.grid(
            row=self.numWidgets,
            column=0,
            columnspan=12,
            sticky='NSWE'
        )
        component.bind('<Configure>', self.updateWeights)
        self.root.rowconfigure(self.numWidgets, weight=1)
        self.numWidgets = self.numWidgets + 1
        self.components.append(component)

    def switchSignal(self, component, signalType, **kwargs):
        """
        Calls the signal on the given component of the
        specified type.

        Parameters: component - the component to update
                    signalType - the signal to dispatch
        """
        signals = {
            "frame": component.frameUpdate,
            "start": component.onStarted,
            "split": component.onSplit,
            "comp": component.onComparisonChanged,
            "pause": component.onPaused,
            "skip": component.onSplitSkipped,
            "reset": component.onReset,
            "restart": component.onRestart,
            "runChanged": component.runChanged,
            "resize": component.onResize,
            "shutdown": component.onShutdown,
            "view": component.moveView
        }
        signals.get(signalType, component.frameUpdate)(**kwargs)

    def updateWidgets(self, signalType, **kwargs):
        """
        Updates all the components with a given signal type.

        Parameters: signalType - the type of signal to dispatch
        """
        for component in self.components:
            self.switchSignal(component, signalType, **kwargs)

    def setupGui(self, isPractice=False, showMenu=True):
        """
        Creates the window with the destruction callback, and
        sets control callbacks.
        """
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.finish)
        self.root.title("Base Timer")
        for i in range(12):
            self.root.columnconfigure(i, weight=1)
        if isPractice:
            self.menu = MainMenu.PracticeMenu(self)
            self.root.configure(menu=self.menu)
        elif (showMenu):
            self.menu = MainMenu.Menu(self)
            self.root.configure(menu=self.menu)
        else:
            self.menu = None

    def startGui(self):
        """
        Show the window, and call the first update after one
        frame.
        """
        self.root.after(17, self.update)
        self.root.mainloop()
        return self.retVal

    def updateWeights(self, *_):
        for i in range(self.numWidgets):
            self.root.rowconfigure(i, weight=self.components[i].winfo_height())
        condition = not len(
            list(
                filter(
                    lambda x: x == 1,
                    [
                        self.components[i].winfo_height()
                        for i in range(self.numWidgets)
                    ]
                )
            )
        )
        if condition:
            for component in self.components:
                component.unbind('<Configure>')
        else:
            self.updateWidgets("resize")

    """
    Signal/Event Handling
    """

    def update(self):
        """
        Set the timer to update every time this is called
        """
        exitCode = self.state.frameUpdate()
        if self.initialLoad:
            self.confirmPartialLoad()
            self.initialLoad = False
        if not exitCode:
            self.updateWidgets("frame")
        self.updater = self.root.after(17, self.update)

    def start(self, _=None):
        """
        Initialize the start and first split times when the run
        starts
        """
        if not self.state.onStarted():
            self.updateWidgets("start")
            if self.menu:
                self.menu.updateMenuState("during")

    def onSplitEnd(self, event=None):
        """
        At the end of each split, record and store the times,
        calculate all the diffs, and call the helper functions
        to update the GUI
        """
        exitCode = self.state.onSplit()
        if exitCode == 1:
            return
        elif exitCode and exitCode > 6:
            self.togglePause()
        if exitCode and self.menu:
            if exitCode % 3 == 1:
                self.menu.updateMenuState("after")
            elif exitCode % 3 == 2:
                self.menu.updateMenuState("last")
        self.updateWidgets("split")

    def guiSwitchCompareCCW(self, _=None):
        """
        Move the comparison counter-clockwise (backwards)
        """
        self.rotateCompare(-1)

    def guiSwitchCompareCW(self, _=None):
        """
        Move the comparison clockwise (forwards)
        """
        self.rotateCompare(1)

    def guiMoveViewUp(self, _=None):
        self.moveSplitWindow(-1)

    def guiMoveViewDown(self, _=None):
        self.moveSplitWindow(1)

    def reset(self, _=None):
        """
        Stop the run here
        """
        if not self.state.onReset():
            self.updateWidgets("reset")
            if self.menu:
                self.menu.updateMenuState("after")

    def skip(self, event=None):
        """
        Skip a split
        """
        if not self.state.onSplitSkipped():
            self.updateWidgets("skip")

    def togglePause(self, event=None):
        """
        If paused, unpause. If not paused, pause.
        """
        if not self.state.onPaused():
            self.updateWidgets("pause")
            if self.menu:
                if self.menu.state == "paused":
                    self.menu.updateMenuState(self.beforePauseState)
                else:
                    self.beforePauseState = self.menu.state
                    self.menu.updateMenuState("paused")

    def restart(self, _=None):
        """
        Restart the run by resetting the timer state.
        """
        if not self.state.onRestart():
            self.updateWidgets("restart")
            if self.menu:
                self.menu.updateMenuState("before")

    def save(self, _=None):
        """
        Saves the data stored in the state.
        """
        self.state.saveTimes()

    def partialSave(self, _=None):
        """
        Saves the data stored in the state partway through a
        run.
        """
        self.state.partialSave()

    def chooseLayout(self, _=None):
        """
        Opens a window to change the current layout
        """
        if self.state.started:
            return
        LayoutPopup.LayoutPopup(self.root, self.setLayout, self.session).show()

    def choosePracticeRun(self, _=None):
        """
        Opens a window to change the current run (practice
        timer)
        """
        if self.state.started:
            return
        splitFile = fileDialogs.chooseRun(self.state.config)
        if not splitFile:
            return
        self.session.setRun(splitFile)
        self.session.setSplit("")
        self.chooseSplit()

    def chooseRun(self, _=None):
        """
        Opens a window to change the current run
        """
        if self.state.started:
            return
        self.setRun(fileDialogs.chooseRun(self.state.config))

    def chooseSplit(self, _=None):
        """
        Opens a window to change the current split (practice
        only)
        """
        if self.state.started:
            return
        (
            PracticeRunSelector.SelectorP(
                self.root,
                self.setSplit,
                self.session
            )
            .show()
        )

    def finish(self, _=None):
        """
        Finish the run by saving the splits and closing the
        window.
        """
        if not self.state.shouldFinish():
            return
        if self.state.saveType():
            self.confirmSave(self.saveAndClose, self.close)
        else:
            self.close()

    def editSplits(self):
        """
        Open the split editor. Used by the main menu.
        """
        SplitEditor.SplitEditor(self.root, self.newEditedState, self.state)

    def addRun(self):
        """
        Open the new run creator (a variation of the split
        editor).
        """
        AddRun.SplitEditorP(self.root, self.addRunState)

    """
    Helper functions
    """

    def rotateCompare(self, rotation):
        """
        The function called when the 'Switch Compare' button is
        clicked
        """
        if not self.state.onComparisonChanged(rotation):
            self.updateWidgets("comp")

    def moveSplitWindow(self, movement):
        self.updateWidgets("view", **{"movement": movement})

    """
    Dialogs
    """

    def confirmPartialLoad(self):
        """
        Loads previously saved partial run data.
        """
        if self.state.hasPartialSave():
            ConfirmPopup.ConfirmPopup(
                self.root,
                {
                    "accepted": self.partialLoad,
                    "rejected": self.confirmDeletePartialSave
                },
                "Load",
                "This category has an incomplete run saved. Load it?"
            )

    def confirmDeletePartialSave(self):
        """
        Show a popup for the user to delete their partial save.
        """
        ConfirmPopup.ConfirmPopup(
            self.root,
            {"accepted": self.state.deletePartialSave},
            "Delete",
            "Delete partial save?"
        )

    def confirmSave(self, accepted, rejected=None):
        """
        Save the splits before closing the window or changing the
        run.
        """
        saveType = self.state.saveType()
        prompt = ""
        if saveType == 1:
            prompt = "Save partial run (closing will save automatically)?"
        elif saveType == 2:
            prompt = "Save local changes (closing will save automatically)?"

        callbacks = {"accepted": accepted}
        if rejected:
            callbacks["rejected"] = rejected
        if prompt:
            ConfirmPopup.ConfirmPopup(
                self.root,
                callbacks,
                "Save",
                prompt
            )

    """
    Dialog Callbacks
    """

    def partialLoad(self):
        """
        Loads previously saved partial run data.
        """
        self.start()
        self.togglePause({})
        self.state.partialLoad()
        self.updateWidgets("split")
        self.confirmDeletePartialSave()

    def setLayout(self, retVal):
        """
        Set the layout if necessary, and restart to apply.
        """
        layoutName = retVal["layoutName"]
        if not layoutName == self.session.layoutName:
            self.session.setLayout(layoutName)
            self.retVal = 1
            self.finish()

    def setRun(self, splitFile):
        """
        Set the run if necessary.
        """
        if splitFile == self.state.splitFile:
            return
        self.confirmSave(self.saveFullOrPartial)
        compareNum = self.state.compareNum
        self.session.setRun(splitFile)
        self.state = State.State(self.session.splitFile)
        self.state.setComparison(compareNum)
        self.updateWidgets("runChanged", state=self.state)
        self.updateWeights()
        self.confirmPartialLoad()

    def setSplit(self, newSession):
        """
        Set the split if necessary (practice only).
        """
        self.confirmSave(self.saveFullOrPartial)
        self.session.setSplit(newSession["split"])
        self.state = PracticeState.State(self.session)
        self.updateWidgets("runChanged", state=self.state)

    def saveFullOrPartial(self):
        """
        Save the run.
        """
        if self.state.saveType() == 1:
            self.partialSave()
        else:
            self.save()

    def saveAndClose(self):
        """
        Save and close the window.
        """
        self.saveFullOrPartial()
        if self.updater:
            self.root.after_cancel(self.updater)
        self.root.destroy()

    def close(self):
        """
        Close the window.
        """
        if self.updater:
            self.root.after_cancel(self.updater)

        self.updateWidgets("shutdown")
        self.root.destroy()

    def newEditedState(self, newSaveData):
        """
        Reload the current splits after editing.
        """
        self.state.loadSplits(newSaveData)
        self.updateWidgets("runChanged", state=self.state)

    def addRunState(self, retVal):
        """
        Load the splits for a newly added run.
        """
        compareNum = self.state.compareNum
        if retVal["splitFile"]:
            self.session.setRun(retVal["splitFile"])
        else:
            self.session.setRun(self.state.splitFile)
        self.state = State.State(self.session.splitFile)
        self.state.setComparison(compareNum)
        self.updateWidgets("runChanged", state=self.state)
