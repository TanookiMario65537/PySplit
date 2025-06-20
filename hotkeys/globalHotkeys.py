from util import readConfig as rc
import logging
import socket
import evdev
from evdev import InputDevice, categorize, ecodes
from pathlib import Path


def createSocket() -> socket.socket:
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        socketPath = Path(Path.cwd().anchor, "tmp", "pysplit.sock")
        sock.connect(str(socketPath))
    except ConnectionRefusedError as e:
        logging.error("Could not connect to comms socket. Aborting.")
        logging.error(e)
        exit(1)
    except FileNotFoundError:
        # This should never happen with the desktop program.
        logging.error("Socket does not exist. Aborting.")
        exit(1)
    return sock


def findKeyboardDevice(socket: socket.socket) -> InputDevice:
    devices = [InputDevice(path) for path in evdev.list_devices()]
    keyboard = None
    for i, dev in enumerate(devices):
        if dev.name.lower().find("keyboard") > -1:
            keyboard = dev
            break

    if keyboard is None:
        logging.error(
            "Could not find a keyboard. Cannot create global hotkeys. "
            "Usually this means the global hotkey process does not have "
            "admin privileges."
        )
        socket.sendall("ERROR: Keyboard not found\n".encode())
        exit(1)
    return keyboard


def readKeyboardEvents(keyboard: InputDevice, socket: socket.socket) -> None:
    for event in keyboard.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            msg = (
                f"{key_event.keystate}/"
                f"{key_event.keycode}/"
                f"{",".join(
                    [key[0] for key in keyboard.active_keys(verbose=True)]
                )}"
            )
            try:
                socket.sendall((msg + "\n").encode())
            except BrokenPipeError:
                logging.info("Socket has been destroyed")
                return


def configure() -> None:
    # No need to log the error here if there's an issue with the config file.
    # The main program will log an error to the default log file.
    userConfig = rc.getUserConfig()
    if not userConfig.get("globalHotkeys", False):
        exit(0)
    setupLogging(userConfig)


def setupLogging(userConfig: dict) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s (hotkeys) [%(levelname)s] %(message)s",
        datefmt="%c",
        handlers=[
            logging.FileHandler(userConfig["logFile"])
        ]
    )
    logging.info("Starting global hotkey handler.")


def main():
    configure()
    socket = createSocket()
    keyboard = findKeyboardDevice(socket)
    readKeyboardEvents(keyboard, socket)


if __name__ == "__main__":
    main()
