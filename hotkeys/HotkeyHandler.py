import threading
import socket
from contextlib import contextmanager
import logging
from pathlib import Path
import subprocess
import time
import platform

logger = logging.getLogger(__name__)


@contextmanager
def unixSocket(path):
    if path.exists():
        path.unlink()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        yield sock
    finally:
        sock.close()
        if path.exists():
            path.unlink()


class HotkeyRunner:
    def __init__(self, app, state, handler):
        self.app = app
        self.state = state
        self.handler = handler
        self.error = ""

    def run(self):
        pass


class LocalRunner(HotkeyRunner):
    def run(self):
        self.app.root.bind(
            self.state.config["hotkeys"]["decreaseComparison"],
            self.app.guiSwitchCompareCCW
        )
        self.app.root.bind(
            self.state.config["hotkeys"]["increaseComparison"],
            self.app.guiSwitchCompareCW
        )
        self.app.root.bind(self.state.config["hotkeys"]["split"], self.app.onSplitEnd)
        self.app.root.bind(self.state.config["hotkeys"]["reset"], self.app.reset)
        self.app.root.bind(self.state.config["hotkeys"]["skip"], self.app.skip)
        self.app.root.bind(self.state.config["hotkeys"]["start"], self.app.start)
        self.app.root.bind(self.state.config["hotkeys"]["pause"], self.app.togglePause)
        self.app.root.bind(self.state.config["hotkeys"]["restart"], self.app.restart)
        self.app.root.bind(self.state.config["hotkeys"]["finish"], self.app.finish)
        self.app.root.bind(self.state.config["hotkeys"]["save"], self.app.save),
        self.app.root.bind(self.state.config["hotkeys"]["partialSave"], self.app.partialSave),
        self.app.root.bind("<Control-L>", self.app.partialLoad),
        self.app.root.bind(
            self.state.config["hotkeys"]["chooseLayout"],
            self.app.chooseLayout
        )
        self.app.root.bind(self.state.config["hotkeys"]["chooseRun"], self.app.chooseRun)


class LinuxGlobalRunner(HotkeyRunner):
    def run(self):
        logging.info("Starting global hotkey handler")
        (
            threading.Thread(
                target=self.handle_global_hotkeys,
                daemon=True
            )
            .start()
        )

    def monitorBgProcess(self):
        while True:
            code = self.bgProcess.poll()
            if code is not None:
                logging.info(f"Subprocess exited with code {code}")
                if code != 0:
                    logging.error("Subprocess error — closing socket")
                    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    sock.connect(str(self.socketPath))
                    sock.sendall("ERROR: Background process failed\n".encode())
                    sock.close()
                break
            time.sleep(0.5)

    def handle_global_hotkeys(self):
        logging.info("Creating socket")
        self.socketPath = Path(Path.cwd().anchor, "tmp", "pysplit.sock")
        try:
            with unixSocket(self.socketPath) as s:
                self.socket = s
                s.bind(str(self.socketPath))
                logging.debug("Bound to local socket")
                s.listen()
                self.bgProcess = subprocess.Popen(
                    ["pkexec", (Path.home()/".local"/"bin"/"pysplitHotkeys")],
                    start_new_session=True,
                )
                (
                    threading.Thread(
                        target=self.monitorBgProcess,
                        daemon=True
                    )
                    .start()
                )
                conn, _ = s.accept()
                with conn:
                    for i, line in enumerate(conn.makefile()):
                        ls = line.strip()
                        if ls.startswith("ERROR"):
                            raise Exception(ls)
                        self.fireHotkey(ls)
        except Exception as e:
            logging.info(
                "Socket error: " + str(e) + ". Falling back to local hotkeys."
            )
            self.handler.update_runner("local")

    def isModifier(self, keyName: str) -> str:
        modifierToTkinter = {
            "CTRL": "Control",
            "META": "Super",
            "ALT": "Alt",
            "SHIFT": "Shift"
        }
        for ending in modifierToTkinter.keys():
            if key_name.endswith(ending):
                return modifierToTkinter[ending]
        return ""

    def isSpecial(self, keyName: str) -> str:
        specialCodes = {
            "KEY_BREAK":     "Cancel",
            "KEY_ENTER":     "Return",
            "KEY_ESC":       "Escape",
            "KEY_SPACE":     "space",
            "KEY_TAB":       "Tab",
            "KEY_BACKSPACE": "BackSpace",
            "KEY_UP":        "Up",
            "KEY_DOWN":      "Down",
            "KEY_LEFT":      "Left",
            "KEY_RIGHT":     "Right",
        }
        for i in range(1, 13):
            specialCodes[f"KEY_F{i}"] = f"F{i}"
        return specialCodes.get(keyName, "")

    def evdevToTkinter(self, hotkeyList) -> str:
        info = hotkeyList.split("/")
        if info[0] != "1":
            return
        modifierList = ["Control", "Shift", "Alt", "Super"]
        modifiers = {key: False for key in modifierList}
        for key in info[2].split(","):
            modifier = self.isModifier(key)
            if modifier:
                modifiers[modifier] = True
        specialKey = self.isSpecial(info[1])
        keyText = "<"
        for modifier in modifierList:
            if modifier == "Shift":
                continue
            if not modifiers[modifier]:
                continue
            keyText += modifier + "-"
        pressedKey = specialKey if specialKey else info[1].split("_")[1].lower()
        keyText += pressedKey if specialKey or not modifiers["Shift"] else pressedKey.upper()
        keyText += ">"
        return keyText

    def fireHotkey(self, hotkeyList):
        logging.info(hotkeyList)
        keyString = self.evdevToTkinter(hotkeyList)
        funcMap = {
            self.state.config["hotkeys"]["decreaseComparison"]: self.app.guiSwitchCompareCCW,
            self.state.config["hotkeys"]["increaseComparison"]: self.app.guiSwitchCompareCW,
            self.state.config["hotkeys"]["split"]: self.app.onSplitEnd,
            self.state.config["hotkeys"]["reset"]: self.app.reset,
            self.state.config["hotkeys"]["skip"]: self.app.skip,
            self.state.config["hotkeys"]["start"]: self.app.start,
            self.state.config["hotkeys"]["pause"]: self.app.togglePause,
            self.state.config["hotkeys"]["restart"]: self.app.restart,
            self.state.config["hotkeys"]["finish"]: self.app.finish,
            self.state.config["hotkeys"]["save"]: self.app.save,
            self.state.config["hotkeys"]["partialSave"]: self.app.partialSave,
            self.state.config["hotkeys"]["chooseLayout"]: self.app.chooseLayout,
            "<Control-L>": self.app.partialLoad,
            self.state.config["hotkeys"]["chooseRun"]: self.app.chooseRun,
        }
        func = funcMap.get(keyString, None)
        logging.info(keyString)
        if func is None:
            return
        func()


class HotkeyHandler:
    def __init__(self, app, state):
        self.app = app
        self.state = state
        if self.state.config.get("globalHotkeys", False):
            if platform.system() != "Linux":
                logging.warn(f"Global hotkeys not supported for {platform.system()}")
                self.runner = LocalRunner(self.app, self.state, self)
            else:
                self.runner = LinuxGlobalRunner(self.app, self.state, self)
        else:
            self.runner = LocalRunner(self.app, self.state, self)
        self.runner.run()

    def update_runner(self, new_runner):
        self.runner = LocalRunner(self.app, self.state, self)
        self.runner.run()
