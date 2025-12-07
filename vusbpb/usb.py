# vusbpb/usb.py
import os
from dataclasses import dataclass
from typing import List

from .config import loadConfig, saveConfig, getUSBHistory, setUSBHistory, ConfigError
from .drawtree import TreeNode, renderTree


@dataclass
class UsbPortInfo:
    usbPortId: str
    usbIsConnected: bool
    usbDeviceId: str
    usbDescription: str


def scanUSBPorts() -> List[UsbPortInfo]:
    allPorts: List[UsbPortInfo] = []

    if not os.path.isdir("/sys/bus/usb/devices"):
        return allPorts

    for entryUSB in sorted(os.listdir("/sys/bus/usb/devices")):
        entryPath = os.path.join("/sys/bus/usb/devices", entryUSB)
        if not os.path.isdir(entryPath):
            continue

        # Remove hubs, interfaces etc.
        if entryUSB.startswith("usb"):
            continue
        if ":" in entryUSB:
            continue
        if entryUSB.endswith(".0"):
            continue

        usbPortId = entryUSB
        usbIdVendor = helperReadFile(os.path.join(entryPath, "idVendor"))
        usbIdProduct = helperReadFile(os.path.join(entryPath, "idProduct"))
        usbIsConnected = usbIdVendor is not None and usbIdProduct is not None

        if usbIsConnected:
            usbDeviceId = f"{usbIdVendor}:{usbIdProduct}"
            usbProduct = helperReadFile(os.path.join(entryPath, "product")) or ""
            usbManufacturer = helperReadFile(os.path.join(entryPath, "manufacturer")) or ""
            __tmpUsbDesc = [p for p in [usbManufacturer, usbProduct] if p]
            usbDescription = " ".join(__tmpUsbDesc) if __tmpUsbDesc else "Unknown device"
        else:
            usbDeviceId = "none"
            usbDescription = ""

        allPorts.append(
            UsbPortInfo(
                usbPortId = usbPortId,
                usbIsConnected = usbIsConnected,
                usbDeviceId = usbDeviceId,
                usbDescription = usbDescription,
            )
        )
    return allPorts


def showUSB() -> int:
    try:
        config = loadConfig(allow_missing = True)
        usbPrevious = set(getUSBHistory(config))
    except ConfigError as error:
        usbPrevious = set()
        print(f"WARNING: Cannot load config! {error}")

    usbPorts = scanUSBPorts()
    currentConnected = {usbPort.usbPortId for usbPort in usbPorts if usbPort.usbIsConnected}

    if not usbPorts:
        print("No USB ports found under /sys/bus/usb/devices")
        return 0

    nodes: List[TreeNode] = []
    for usbPort in usbPorts:
        connected_str = "Yes" if usbPort.usbIsConnected else "No"
        isNewConnected = usbPort.usbIsConnected and (usbPort.usbPortId not in usbPrevious)

        usbDescription = usbPort.usbDescription or ""
        usbDeviceId = usbPort.usbDeviceId or "none"

        usbPortLabel = f"\033[38;5;82mUSB port: \033[38;5;15m{usbPort.usbPortId}\033[0m"
        if isNewConnected:
            usbPortLabel += "  \033[5;48;5;196;38;5;15m ← NEW \033[0m"

        children = [
            TreeNode(
                label = f"\033[38;5;82mConnected: \033[38;5;15m{connected_str}\033[0m"
            ),
            TreeNode(
                label = f"\033[38;5;82mDevice ID: \033[38;5;15m{usbDeviceId}\033[0m"
            ),
        ]

        if usbDescription:
            children.append(TreeNode(
                label = f"\033[38;5;82mDescription: \033[38;5;15m{usbDescription}\033[0m"
            ))

        nodes.append(TreeNode(
            label = usbPortLabel,
            children = children
        ))

    try:
        config = loadConfig(allow_missing = True)
        config = setUSBHistory(config, sorted(currentConnected))
        saveConfig(config)
    except ConfigError as error:
        print(f"WARNING: cannot update USB history in config: {error}")

    print(renderTree("\033[38;5;28mUSB ports\033[0m", nodes))
    return 0


# Helpers
def helperReadFile(path: str) -> str | None:
    try:
        with open(path, "r", encoding = "utf-8", errors = "ignore") as file:
            return file.read().strip()
    except OSError:
        return None