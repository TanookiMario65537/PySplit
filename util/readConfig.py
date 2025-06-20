import os
from util import fileio
import errors as Errors
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

validPositions = ["left", "center-left", "center", "center-right", "right"]

defaultHotkeys = {}


def getUserConfig():
    defaultConfig = fileio.readJson("defaults/global.json")
    setDefaultHotkeys(defaultConfig)
    if os.path.exists("config/global.json"):
        userConfig = fileio.readJson("config/global.json")
    else:
        userConfig = {}
    config = mergeConfigs(defaultConfig, userConfig)
    return config


def getCUserConfig(ctype, fileName):
    defaultConfig = fileio.readJson("defaults/"+ctype+".json")
    configPath = "config/" + fileName + ".json"
    if os.path.exists(configPath):
        userConfig = fileio.readJson(configPath)
    else:
        userConfig = {}
    config = mergeConfigs(defaultConfig, userConfig)
    return config


def setDefaultHotkeys(defaultConfig):
    global defaultHotkeys
    for key in defaultConfig["hotkeys"].keys():
        defaultHotkeys[key] = defaultConfig["hotkeys"][key]


def mergeConfigs(original, override):
    new = original
    for key in override.keys():
        if not type(override[key]) is dict:
            try:
                if key == "position" and not override[key] in validPositions:
                    raise Errors.ConfigValueError(
                        key,
                        override[key],
                        original[key]
                    )
                new[key] = override[key]
            except Errors.ConfigValueError as e:
                logger.error(e)
        else:
            new[key] = mergeConfigs(original[key], override[key])
    return new


def validHotkey(key: str) -> bool:
    if key[0] == "<" or key[-1] == ">":
        parts = key[1:-1].split("-")
    else:
        parts = [key]
    for i, part in enumerate(parts[:-1]):
        if not validModifier(part, i):
            return False
    return validKey(parts[-1])


def validKey(key: str) -> bool:
    return key in validKeysyms


def validModifier(mod: str, index: int) -> bool:
    if mod in ["Control", "Alt", "Super"]:
        return True
    if mod == "Key":
        return index == 0
    return False


def validateHotkeys(config):
    for key in config["hotkeys"].keys():
        try:
            if not validHotkey(config["hotkeys"][key]):
                raise Errors.HotKeyTypeError(
                    config["hotkeys"][key],
                    defaultHotkeys[key],
                    key
                )
        except Errors.HotKeyTypeError as e:
            logger.error(e)
            config["hotkeys"][key] = defaultHotkeys[key]


validKeysyms = fileio.readJson(
    Path(__file__).parent.parent / "hotkeys" / "validTkinterKeysyms.json"
)
