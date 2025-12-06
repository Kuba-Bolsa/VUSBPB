# vusbpb/config.py
import json
import os
import tempfile
from typing import Any, Dict, List


CONFIG_PATH = "/etc/vusbpb.conf"


class ConfigError(Exception):
    """Błąd ładowania / zapisu konfiguracji."""


def _default_config() -> Dict[str, Any]:
    return {
        "VMS": [],
        "USB": [],
    }


def load_config(allow_missing: bool = True) -> Dict[str, Any]:
    """
    Wczytaj konfigurację z /etc/vusbpb.conf.

    - Jeśli plik nie istnieje i allow_missing=True -> zwraca domyślną strukturę.
    - Jeśli plik nie istnieje i allow_missing=False -> rzuca ConfigError.
    - Jeśli JSON jest uszkodzony -> rzuca ConfigError.
    """
    if not os.path.exists(CONFIG_PATH):
        if allow_missing:
            return _default_config()
        raise ConfigError(f"Config file {CONFIG_PATH} does not exist")

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {CONFIG_PATH}: {e}") from e
    except OSError as e:
        raise ConfigError(f"Cannot read {CONFIG_PATH}: {e}") from e

    # Uzupełnij brakujące klucze (dla zgodności wstecznej)
    if "VMS" not in data or not isinstance(data["VMS"], list):
        data["VMS"] = []
    if "USB" not in data or not isinstance(data["USB"], list):
        data["USB"] = []

    return data


def save_config(config: Dict[str, Any]) -> None:
    """
    Zapisz konfigurację atomowo do /etc/vusbpb.conf.

    Tworzy plik tymczasowy i podmienia go rename() na docelowy.
    """
    # Upewniamy się, że klucze istnieją
    if "VMS" not in config or not isinstance(config["VMS"], list):
        config["VMS"] = []
    if "USB" not in config or not isinstance(config["USB"], list):
        config["USB"] = []

    dir_name = os.path.dirname(CONFIG_PATH) or "/"
    os.makedirs(dir_name, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".vusbpb_conf_", dir=dir_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(config, tmp_file, indent=4, sort_keys=True)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, CONFIG_PATH)
    except OSError as e:
        # Sprzątanie po błędzie
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise ConfigError(f"Cannot write config to {CONFIG_PATH}: {e}") from e


# Helpers do pracy z polami VMS / USB

def get_vm_mappings(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Zwraca listę mapowań VM.

    Element: { "vmId": int, "usbPortId": str }
    """
    return list(config.get("VMS", []))


def set_vm_mappings(config: Dict[str, Any], mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
    config["VMS"] = mappings
    return config


def get_usb_history(config: Dict[str, Any]) -> List[str]:
    """
    Zwraca listę portów (stringów), na których poprzednio było coś podłączone (pole USB).
    """
    return list(config.get("USB", []))


def set_usb_history(config: Dict[str, Any], ports: List[str]) -> Dict[str, Any]:
    config["USB"] = list(ports)
    return config
