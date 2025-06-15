import sys
from Apps import app as App
import WidgetLoader
import errors as Errors
from DataClasses import Session
from States import State
from util import readConfig as rc
import logging


def setHotkeys(app, state):
    app.root.bind(
        state.config["hotkeys"]["decreaseComparison"],
        app.guiSwitchCompareCCW
    )
    app.root.bind(
        state.config["hotkeys"]["increaseComparison"],
        app.guiSwitchCompareCW
    )
    app.root.bind(state.config["hotkeys"]["split"], app.onSplitEnd)
    app.root.bind(state.config["hotkeys"]["reset"], app.reset)
    app.root.bind(state.config["hotkeys"]["skip"], app.skip)
    app.root.bind(state.config["hotkeys"]["start"], app.start)
    app.root.bind(state.config["hotkeys"]["pause"], app.togglePause)
    app.root.bind(state.config["hotkeys"]["restart"], app.restart)
    app.root.bind(state.config["hotkeys"]["finish"], app.finish)
    app.root.bind(state.config["hotkeys"]["save"], app.save),
    app.root.bind(state.config["hotkeys"]["partialSave"], app.partialSave),
    app.root.bind("<Control-L>", app.partialLoad),
    app.root.bind(state.config["hotkeys"]["chooseLayout"], app.chooseLayout)
    app.root.bind(state.config["hotkeys"]["chooseRun"], app.chooseRun)


def setupLogging():
    userConfig = rc.getUserConfig()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%c",
        handlers=[
            logging.FileHandler(userConfig["logFile"])
        ]
    )
    logging.info("Starting PySplit")


setupLogging()
session = Session.Session()
if session.exit:
    sys.exit()

app = None
exitCode = None

while not app or exitCode:
    rootWindow = None

    state = State.State(session.splitFile)
    rc.validateHotkeys(state.config)

    app = App.App(state, session)
    app.setupGui(showMenu=session.layout["menu"])

    setHotkeys(app, state)
    rootWindow = app.root

    loader = WidgetLoader.WidgetLoader(app, state, rootWindow)

    for component in session.layout["components"]:
        try:
            if not component.get("enabled", True):
                logging.info(f"Component \"{component['type']}\" is disabled.")
                continue
            if "config" in component.keys():
                app.addWidget(
                    loader.loadWidget(component["type"], component["config"])
                )
            else:
                app.addWidget(loader.loadWidget(component["type"]))
        except Errors.WidgetTypeError as e:
            logging.error(e)

    exitCode = app.startGui()

session.save()
