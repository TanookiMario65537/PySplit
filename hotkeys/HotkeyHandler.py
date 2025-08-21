import threading
import socket
from contextlib import contextmanager
import logging
from pathlib import Path
import subprocess
import time
import platform
from util import fileio

logger = logging.getLogger(__name__)


@contextmanager
def unixSocket(path: Path) -> None:
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

    def run(self) -> None:
        pass


class LocalRunner(HotkeyRunner):
    def run(self) -> None:
        for key, value in self.handler.funcMap.items():
            self.app.root.bind(key, value)


class LinuxGlobalRunner(HotkeyRunner):
    def __init__(self, app, state, handler):
        super().__init__(app, state, handler)
        self.evdevToTkinterMap = fileio.readJson(
            Path(__file__).parent / "evdevToTkinter.json"
        )

    def run(self) -> None:
        self.running = True
        logging.info("Starting global hotkey handler")
        (
            threading.Thread(
                target=self.handleGlobalHotkeys,
                daemon=True
            )
            .start()
        )

    def monitorBgProcess(self) -> None:
        while self.running:
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

    def handleGlobalHotkeys(self) -> None:
        logging.info("Creating socket")
        self.socketPath = Path(Path.cwd().anchor, "tmp", "pysplit.sock")
        try:
            with unixSocket(self.socketPath) as s:
                self.socket = s
                s.bind(str(self.socketPath))
                logging.debug("Bound to local socket")
                s.listen()
                bgPath = (
                    Path(self.state.config["installDirectory"])
                    / "pysplitHotkeys"
                )
                if not bgPath.exists():
                    raise Exception(
                        "Global hotkey background process is not installed. "
                        "Global hotkeys cannot be used without it. "
                        "The process can be installed by running `./install` "
                        "in the base directory."
                    )
                self.bgProcess = subprocess.Popen(
                    ["pkexec", bgPath],
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
            logging.error(
                "Socket error: " + str(e)
            )
            logging.info("Falling back to local hotkeys.")
            self.handler.updateRunner("local")
        self.running = False

    def evdevToTkinter(self, hotkeyList: str) -> str:
        info = hotkeyList.split("/")
        if info[0] != "1":
            return
        modifierList = ["Control", "Shift", "Alt", "Super"]
        modifiers = {key: False for key in modifierList}
        for key in info[2].split(","):
            modifier = self.modifierToTkinter["modifiers"].get(key, "")
            if modifier:
                modifiers[modifier] = True
        keyText = ""
        for modifier in modifierList:
            if modifier == "Shift":
                continue
            if not modifiers[modifier]:
                continue
            keyText += modifier + "-"
        if not keyText:
            keyText += "Key-"
        pressedKey = info[1]
        keyText += (
            self.evdevToTkinterMap
            ["unmodified" if not modifiers["Shift"] else "shifted"]
            [pressedKey]
        )
        return "<" + keyText + ">"

    def fireHotkey(self, hotkeyList: list[str]) -> None:
        keyString = self.evdevToTkinter(hotkeyList)
        func = self.handler.funcMap.get(keyString, None)
        if func is None:
            return
        func()


class HotkeyHandler:
    def __init__(self, app, state):
        self.app = app
        self.state = state
        self.funcMap = {
            self.state.config["hotkeys"]["decreaseComparison"]:
                self.app.guiSwitchCompareCCW,
            self.state.config["hotkeys"]["increaseComparison"]:
                self.app.guiSwitchCompareCW,
            self.state.config["hotkeys"]["split"]:
                self.app.onSplitEnd,
            self.state.config["hotkeys"]["reset"]:
                self.app.reset,
            self.state.config["hotkeys"]["skip"]:
                self.app.skip,
            self.state.config["hotkeys"]["start"]:
                self.app.start,
            self.state.config["hotkeys"]["pause"]:
                self.app.togglePause,
            self.state.config["hotkeys"]["restart"]:
                self.app.restart,
            self.state.config["hotkeys"]["finish"]:
                self.app.finish,
            self.state.config["hotkeys"]["save"]:
                self.app.save,
            self.state.config["hotkeys"]["partialSave"]:
                self.app.partialSave,
            self.state.config["hotkeys"]["chooseLayout"]:
                self.app.chooseLayout,
            self.state.config["hotkeys"]["partialLoad"]:
                self.app.partialLoad,
            self.state.config["hotkeys"]["chooseRun"]:
                self.app.chooseRun,
        }
        if self.state.config.get("globalHotkeys", False):
            if platform.system() != "Linux":
                logging.warn(
                    f"Global hotkeys not supported for {platform.system()}"
                )
                runner = LocalRunner(self.app, self.state, self)
            else:
                runner = LinuxGlobalRunner(self.app, self.state, self)
        else:
            runner = LocalRunner(self.app, self.state, self)
        runner.run()

    def updateRunner(self, _: str) -> None:
        LocalRunner(self.app, self.state, self).run()
