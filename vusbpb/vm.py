import subprocess
from enum import Enum, auto
from typing import Dict, Any, List
from .config import (loadConfig, saveConfig, getVmMappings, setVmMappings, ConfigError)
from .drawtree import TreeNode, renderTree


class VmStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    UNKNOWN = auto()


def getAllVMs() -> List[Dict[str, str]]:
    try:
        result = subprocess.run(
            ["qm", "list"],
            text = True,
            capture_output = True,
            check = False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []

    lines = result.stdout.splitlines()
    if not lines:
        return []

    vms: List[Dict[str, str]] = []
    for line in lines:
        line = line.strip()
        if not line or not line[0].isdigit():
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        vmId = parts[0]
        vmName = parts[1]
        vmStatus = parts[2]

        vms.append({
            "vmId": vmId,
            "name": vmName,
            "status": vmStatus
        })

    return vms


def getVMStatus(vmId: int) -> VmStatus:
    try:
        result = subprocess.run(
            ["qm", "status", str(vmId)],
            text = True,
            capture_output = True,
            check = False,
        )
    except OSError:
        return VmStatus.UNKNOWN
    if result.returncode != 0:
        return VmStatus.UNKNOWN

    for line in result.stdout.splitlines():
        line = line.strip().lower()
        if line.startswith("status:"):
            mvStatus = line.split(":", 1)[1].strip()
            if mvStatus == "running":
                return VmStatus.RUNNING
            if mvStatus == "stopped":
                return VmStatus.STOPPED
            return VmStatus.UNKNOWN

    return VmStatus.UNKNOWN


def startVM(vmId: int) -> bool:
    try:
        result = subprocess.run(
            ["qm", "start", str(vmId)],
            text = True,
            capture_output = True,
            check = False,
        )
    except OSError:
        return False

    return result.returncode == 0


def showVMFromSystem() -> int:
    try:
        config = loadConfig(allow_missing = True)
    except ConfigError as error:
        print(f"ERROR: Cannot load config: {error}")
        return 1

    vmIdToMapping: Dict[int, Dict[str, Any]] = {}
    for mapping in getVmMappings(config):
        vmId = helperSafeInt(mapping.get("vmId"))
        if vmId is None:
            continue
        vmIdToMapping[vmId] = mapping

    vms = getAllVMs()
    if not vms:
        print("No virtual machines found")
        return 0

    nodes: List[TreeNode] = []
    for vm in vms:
        vmId = helperSafeInt(vm.get("vmId"))
        if vmId is None:
            continue

        vmName = vm.get("name", "")
        vmStatus = vm.get("status", "unknown")

        mapping = vmIdToMapping.get(vmId)
        if not mapping:
            usbInfo = "<none>"
        else:
            mPort = mapping.get("usbPortId")
            mDev  = mapping.get("usbDeviceId")

            if not mPort and not mDev:
                usbInfo = "<none>"
            else:
                portDisplay = mPort or "<any port>"
                devDisplay  = mDev or "<any device>"
                usbInfo = f"{portDisplay} (device {devDisplay})"

        nodes.append(
            TreeNode(
                label = f"\033[38;5;82mVM ID: \033[38;5;15m{vmId}\033[0m",
                children = [
                    TreeNode(label = f"\033[38;5;82mName: \033[38;5;15m{vmName}\033[0m"),
                    TreeNode(label = f"\033[38;5;82mStatus: \033[38;5;15m{vmStatus}\033[0m"),
                    TreeNode(label = f"\033[38;5;82mUSB trigger: \033[38;5;15m{usbInfo}\033[0m"),
                ],
            )
        )

    print(renderTree("\033[38;5;28mVirtual Machine(s)\033[0m", nodes))
    return 0


def listVMPowerButton() -> int:
    try:
        config = loadConfig(allow_missing = True)
    except ConfigError as error:
        print(f"ERROR: Cannot load config: {error}")
        return 1

    mappings = getVmMappings(config)
    if not mappings:
        print("No VM USB Power Button configured")
        return 0

    statusMap = {
        VmStatus.RUNNING: "running",
        VmStatus.STOPPED: "stopped",
        VmStatus.UNKNOWN: "unknown",
    }

    nodes: List[TreeNode] = []
    for m in mappings:
        vmId = helperSafeInt(m.get("vmId"))
        if vmId is None:
            continue

        vmUSBPort = m.get("usbPortId")
        vmUSBDevice = m.get("usbDeviceId")

        if not (vmUSBPort or vmUSBDevice):
            portDisplay = "<none>"
            devDisplay = "<none>"
        else:
            portDisplay = vmUSBPort or "<any>"
            devDisplay = vmUSBDevice or "<any>"

        vmStatus = statusMap.get(getVMStatus(vmId), "unknown")

        nodes.append(
            TreeNode(
                label = f"\033[38;5;28mVM ID: \033[38;5;15m{vmId}\033[0m",
                children = [
                    TreeNode(label = f"\033[38;5;28mStatus: \033[38;5;15m{vmStatus}\033[0m"),
                    TreeNode(label = f"\033[38;5;28mUSB port: \033[38;5;15m{portDisplay}\033[0m"),
                    TreeNode(label = f"\033[38;5;28mUSB device: \033[38;5;15m{devDisplay}\033[0m"),
                ],
            )
        )

    print(renderTree("\033[38;5;28mVM with USB Power Buttons\033[0m", nodes))
    return 0


def addVMPowerButton(vmId: int, vmUSBPort: str | None, vmUSBDevice: str | None) -> int:
    try:
        config = loadConfig(allow_missing = True)
    except ConfigError as error:
        print(f"ERROR: Cannot load config: {error}")
        return 1

    if not vmUSBPort and not vmUSBDevice:
        print("ERROR: You must provide --usbport and/or --usbdevice")
        return 1

    mappings: List[Dict[str, Any]] = getVmMappings(config)
    for m in mappings:
        if int(m.get("vmId", -1)) == vmId:
            print(f"ERROR: VM ID {vmId} is already configured. Use --delete {vmId} first")
            return 1

    newMapping: Dict[str, Any] = {"vmId": vmId}
    if vmUSBPort:
        newMapping["usbPortId"] = vmUSBPort
    if vmUSBDevice:
        newMapping["usbDeviceId"] = vmUSBDevice

    mappings.append(newMapping)
    config = setVmMappings(config, mappings)

    try:
        saveConfig(config)
    except ConfigError as error:
        print(f"ERROR: Cannot save config: {error}")
        return 1

    vmUSBConfigJoin: List[str] = []
    if vmUSBPort:
        vmUSBConfigJoin.append(f"USB devpath {vmUSBPort}")
    if vmUSBDevice:
        vmUSBConfigJoin.append(f"USB device {vmUSBDevice}")
    vmUSBConfigJoin = " and ".join(vmUSBConfigJoin)

    print(f"Added VM ID: {vmId} with {vmUSBConfigJoin}")
    return 0


def deleteVMPowerButton(vmId: int) -> int:
    try:
        config = loadConfig(allow_missing = True)
    except ConfigError as error:
        print(f"ERROR: Cannot load config: {error}")
        return 1

    mappings = getVmMappings(config)
    newMappings = [m for m in mappings if helperSafeInt(m.get("vmId")) != vmId]
    removedCounter = len(mappings) - len(newMappings)

    if removedCounter == 0:
        print(f"No mapping found for VM ID: {vmId}. Nothing to delete")
        return 0

    config = setVmMappings(config, newMappings)
    try:
        saveConfig(config)
    except ConfigError as error:
        print(f"ERROR: Cannot save config: {error}")
        return 1

    print(f"Removed {removedCounter} mapping(s) for VM ID: {vmId}")
    return 0


# Helpers
def helperSafeInt(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None