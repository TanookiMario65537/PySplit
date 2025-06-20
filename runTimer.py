import sys
from Apps import app as App
import WidgetLoader
import errors as Errors
from DataClasses import Session
from States import State
from util import readConfig as rc
import logging
from hotkeys import HotkeyHandler as HH
from pathlib import Path
import threading


def threadExceptionHandler(args):
    logging.error(
        "Uncaught exception",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )


def logUncaughtExceptions(excType, excValue, excTraceback):
    if issubclass(excType, KeyboardInterrupt):
        # Don't log keyboard interrupt
        sys.__excepthook__(excType, excValue, excTraceback)
        return
    logging.error(
        "Uncaught exception",
        exc_info=(excType, excValue, excTraceback)
    )


def setupLogging():
    # Make sure the error is logged if we can't read the global config.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%c",
        handlers=[
            logging.FileHandler("pysplit.log")
        ]
    )
    sys.excepthook = logUncaughtExceptions
    threading.excepthook = threadExceptionHandler
    userConfig = rc.getUserConfig()

    # At this point, there's a user configured log file. Switching the logger
    # to use it requires removing the old one.
    rootLogger = logging.getLogger()
    for handler in rootLogger.handlers[:]:
        rootLogger.removeHandler(handler)

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

    hotkeyHandler = HH.HotkeyHandler(app, state)
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
