# vusbpb/usb.py
import os
from dataclasses import dataclass
from typing import List

from .config import loadConfig, saveConfig, getUSBHistory, setUSBHistory, ConfigError


SYS_USB_DEVICES = "/sys/bus/usb/devices"


@dataclass
class UsbPortInfo:
    port_id: str        # np. "1-1.2"
    connected: bool     # True jeśli jest urządzenie
    device_id: str      # np. "046d:c534" albo "none"
    comment: str        # opis, np. "Logitech USB Receiver"


def _read_file(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except OSError:
        return None


def scan_usb_ports() -> List[UsbPortInfo]:
    """
    Skanuje /sys/bus/usb/devices i zwraca listę UsbPortInfo.

    Heurystyka:
    - każde wejście w /sys/bus/usb/devices traktujemy jako potencjalny port/urządzenie,
      jeśli ma pliki idVendor/idProduct -> connected = True.
    - device_id = vendor:product lub "none".
    - comment = product lub manufacturer, jeśli dostępne.
    """
    ports: List[UsbPortInfo] = []

    if not os.path.isdir(SYS_USB_DEVICES):
        return ports

    for entry in sorted(os.listdir(SYS_USB_DEVICES)):
        entry_path = os.path.join(SYS_USB_DEVICES, entry)
        if not os.path.isdir(entry_path):
            continue

        # To jest nasz port_id
        port_id = entry  # np. "1-1.2"

        id_vendor = _read_file(os.path.join(entry_path, "idVendor"))
        id_product = _read_file(os.path.join(entry_path, "idProduct"))

        connected = id_vendor is not None and id_product is not None

        if connected:
            device_id = f"{id_vendor}:{id_product}"
            product = _read_file(os.path.join(entry_path, "product")) or ""
            manufacturer = _read_file(os.path.join(entry_path, "manufacturer")) or ""
            comment_parts = [p for p in [manufacturer, product] if p]
            comment = " ".join(comment_parts) if comment_parts else "Unknown device"
        else:
            device_id = "none"
            comment = ""

        ports.append(
            UsbPortInfo(
                port_id=port_id,
                connected=connected,
                device_id=device_id,
                comment=comment,
            )
        )

    return ports


# ANSI kolory do podświetlania nowych portów
ANSI_GREEN = "\033[32m"
ANSI_RESET = "\033[0m"


def showUSB() -> int:
    """
    Implementacja komendy `vusbpb --show usb`.
    Zwraca exit code (0 = ok, !=0 przy błędzie).
    """
    try:
        config = loadConfig(allow_missing=True)
        previous_usb = set(getUSBHistory(config))
    except ConfigError as e:
        # Config uszkodzony – wypisujemy ostrzeżenie, ale nadal pokażemy porty
        previous_usb = set()
        print(f"WARNING: cannot load config: {e}")

    ports = scan_usb_ports()
    current_connected = {p.port_id for p in ports if p.connected}

    if not ports:
        print("No USB ports found under /sys/bus/usb/devices")
    else:
        for p in ports:
            connected_str = "yes" if p.connected else "no"
            comment_part = f'  Comment="{p.comment}"' if p.comment else ""
            line = f"USB port={p.port_id}  Connected={connected_str}  Device ID={p.device_id}{comment_part}"

            is_new_connected = p.connected and (p.port_id not in previous_usb)

            if is_new_connected:
                print(f"{ANSI_GREEN}{line}{ANSI_RESET}")
            else:
                print(line)

    # Spróbuj zapisać nową historię, jeśli config da się wczytać
    try:
        config = loadConfig(allow_missing=True)
        config = setUSBHistory(config, sorted(current_connected))
        saveConfig(config)
    except ConfigError as e:
        # Nie psujemy działania komendy przez błąd zapisu – tylko informujemy
        print(f"WARNING: cannot update USB history in config: {e}")
        return 1

    return 0
