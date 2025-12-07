from typing import Dict, Any, List

from .config import (
    loadConfig,
    saveConfig,
    getVmMappings,
    setVmMappings,
    ConfigError,
)
from .proxmox import get_vm_status, VmStatus, getAllVMs
from .drawtree import TreeNode, renderTree


def showSystemVM() -> int:
    try:
        config = loadConfig(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = getVmMappings(config)
    vmid_to_usb: Dict[int, str] = {}
    for m in mappings:
        vm_id = m.get("vmId")
        usb_port_id = m.get("usbPortId", "")
        if vm_id is None:
            continue
        try:
            vm_id_int = int(vm_id)
        except (TypeError, ValueError):
            continue
        vmid_to_usb[vm_id_int] = usb_port_id

    vms = getAllVMs()
    if not vms:
        print("Brak maszyn wirtualnych (qm list).")
        return 0

    nodes: List[TreeNode] = []
    for vm in vms:
        try:
            vm_id_int = int(vm.get("vmId", -1))
        except (TypeError, ValueError):
            continue

        name = vm.get("name", "")
        status = vm.get("status", "unknown")
        usb_port_id = vmid_to_usb.get(vm_id_int, "")

        label = f"VM ID: {vm_id_int}"

        children = [
            TreeNode(label = f"Name: {name}"),
            TreeNode(label=f"Status: {status}"),
            TreeNode(label=f"USB devpath: {usb_port_id}"),
        ]

        nodes.append(TreeNode(label=label, children=children))

    tree = renderTree("(vm list)", nodes)
    print(tree)
    return 0


def listVMPowerButton() -> int:
    try:
        config = loadConfig(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = getVmMappings(config)
    if not mappings:
        print("Brak skonfigurowanych VM Power Button.")
        return 0

    nodes: List[TreeNode] = []
    for m in mappings:
        vm_id = m.get("vmId")
        usb_port_id = m.get("usbPortId", "")
        if vm_id is None:
            continue

        try:
            vm_id_int = int(vm_id)
        except (TypeError, ValueError):
            continue

        status = get_vm_status(vm_id_int)
        if status == VmStatus.RUNNING:
            status_str = "running"
        elif status == VmStatus.STOPPED:
            status_str = "stopped"
        else:
            status_str = "unknown"

        vm_node = TreeNode(
            label=f"VM ID: {vm_id_int}",
            children=[
                TreeNode(label=f"Status: {status_str}"),
                TreeNode(label=f"USB number: {usb_port_id}"),
            ],
        )
        nodes.append(vm_node)

    tree = renderTree("(node)", nodes)
    print(tree)
    return 0


def addVMPowerButton(vm_id: int, usb_port_id: str) -> int:
    """
    `vusbpb --add {vmId} --usb {usbPortId}`
    """
    try:
        config = loadConfig(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = getVmMappings(config)

    # Nie pozwalamy na duplikaty vmId
    for m in mappings:
        if int(m.get("vmId", -1)) == vm_id:
            print(f"ERROR: VMID {vm_id} is already configured. Use --delete {vm_id} first.")
            return 1

    mappings.append(
        {
            "vmId": vm_id,
            "usbPortId": usb_port_id,
        }
    )

    config = setVmMappings(config, mappings)

    try:
        saveConfig(config)
    except ConfigError as e:
        print(f"ERROR: cannot save config: {e}")
        return 1

    print(f"Added VMID {vm_id} with USB devpath {usb_port_id}.")
    return 0


def deleteVMPowerButton(vm_id: int) -> int:
    """
    `vusbpb --delete {vmId}`
    """
    try:
        config = loadConfig(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = getVmMappings(config)

    new_mappings = [m for m in mappings if int(m.get("vmId", -1)) != vm_id]
    removed_count = len(mappings) - len(new_mappings)

    if removed_count == 0:
        print(f"No mapping found for VMID {vm_id}. Nothing to delete.")
        return 0

    config = setVmMappings(config, new_mappings)

    try:
        saveConfig(config)
    except ConfigError as e:
        print(f"ERROR: cannot save config: {e}")
        return 1

    print(f"Removed {removed_count} mapping(s) for VMID {vm_id}.")
    return 0
