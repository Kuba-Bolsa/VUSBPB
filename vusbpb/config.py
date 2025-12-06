import json
import os
import tempfile
from typing import Any, Dict, List

CONFIG_PATH = "/etc/vusbpb.conf"


class ConfigError(Exception):
    """Błąd ładowania / zapisu konfiguracji."""


def defaultConfig() -> Dict[str, Any]:
    return {
        "VMS": [],
        "USB": [],
    }


def loadConfig(allow_missing: bool = True) -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        if allow_missing:
            return defaultConfig()
        raise ConfigError(f"Config file {CONFIG_PATH} does not exist")

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ConfigError(f"Invalid JSON in {CONFIG_PATH}: {error}") from error
    except OSError as error:
        raise ConfigError(f"Cannot read {CONFIG_PATH}: {error}") from error

    return data


def saveConfig(config: Dict[str, Any]) -> None:
    dirName = os.path.dirname(CONFIG_PATH) or "/"
    os.makedirs(dirName, exist_ok = True)

    fd, tmpPath = tempfile.mkstemp(prefix = ".vusbpb_conf_", dir = dirName)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmpFile:
            json.dump(config, tmpFile, indent=4, sort_keys=True)
            tmpFile.flush()
            os.fsync(tmpFile.fileno())
        os.replace(tmpPath, CONFIG_PATH)
    except OSError as error:
        try:
            os.unlink(tmpPath)
        except OSError:
            pass
        raise ConfigError(f"Cannot write config to {CONFIG_PATH}: {error}") from error


def getVmMappings(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(config.get("VMS", []))


def setVmMappings(config: Dict[str, Any], mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
    config["VMS"] = mappings
    return config


def getUSBHistory(config: Dict[str, Any]) -> List[str]:
    return list(config.get("USB", []))


def setUSBHistory(config: Dict[str, Any], ports: List[str]) -> Dict[str, Any]:
    config["USB"] = list(ports)
    return config
