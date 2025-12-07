from typing import Dict, Any, List

from .config import (loadConfig, saveConfig, getVmMappings, setVmMappings, ConfigError)
from .proxmox import get_vm_status, VmStatus, getAllVMs
from .drawtree import TreeNode, renderTree


def showVMFromSystem() -> int:
    try:
        config = loadConfig(allow_missing = True)
    except ConfigError as error:
        print(f"ERROR: Cannot load config: {error}")
        return 1

    vmIdToUSB: Dict[int, str] = {}
    for mapping in getVmMappings(config):
        vmId = helperSafeInt(mapping.get("vmId"))
        if vmId is None:
            continue
        vmIdToUSB[vmId] = mapping.get("usbPortId", "")

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
        vmUSBPort = vmIdToUSB.get(vmId, "<none>")

        nodes.append(
            TreeNode(
                label = f"\033[38;5;82mVM ID: \033[38;5;15m{vmId}\033[0m",
                children = [
                    TreeNode(label = f"\033[38;5;82mName: \033[38;5;15m{vmName}\033[0m"),
                    TreeNode(label = f"\033[38;5;82mStatus: \033[38;5;15m{vmStatus}\033[0m"),
                    TreeNode(label = f"\033[38;5;82mUSB devpath: \033[38;5;15m{vmUSBPort}\033[0m"),
                ],
            )
        )

    print(renderTree("\033[38;5;28mVM list\033[0m", nodes))
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

        vmUSBPort = m.get("usbPortId", "")
        vmStatus = statusMap.get(get_vm_status(vmId), "unknown")

        nodes.append(
            TreeNode(
                label = f"\033[38;5;28mVM ID: \033[38;5;15m{vmId}\033[0m",
                children = [
                    TreeNode(label = f"\033[38;5;28mStatus: \033[38;5;15m{vmStatus}\033[0m"),
                    TreeNode(label = f"\033[38;5;28mUSB number: \033[38;5;15m{vmUSBPort}\033[0m"),
                ],
            )
        )

    print(renderTree("\033[38;5;28mVM with USB Power Buttons\033[0m", nodes))
    return 0


def addVMPowerButton(vmId: int, vmUSBPort: str) -> int:
    try:
        config = loadConfig(allow_missing = True)
    except ConfigError as error:
        print(f"ERROR: Cannot load config: {error}")
        return 1

    mappings: List[Dict[str, Any]] = getVmMappings(config)
    for m in mappings:
        if int(m.get("vmId", -1)) == vmId:
            print(f"ERROR: VMID {vmId} is already configured. Use --delete {vmId} first")
            return 1

    mappings.append({
        "vmId": vmId,
        "usbPortId": vmUSBPort
    })

    config = setVmMappings(config, mappings)
    try:
        saveConfig(config)
    except ConfigError as error:
        print(f"ERROR: Cannot save config: {error}")
        return 1

    print(f"Added VM ID: {vmId} with USB devpath {vmUSBPort}")
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