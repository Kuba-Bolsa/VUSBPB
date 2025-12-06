# vusbpb/vm.py
from typing import Dict, Any, List

from .config import (
    loadConfig,
    saveConfig,
    getVmMappings,
    setVmMappings,
    ConfigError,
)
from .proxmox import get_vm_status, VmStatus, getAllVMs


def showSystemVM() -> int:
    """
    `vusbpb --show vm`

    Pokazuje listę WSZYSTKICH maszyn z Proxmoxa (qm list),
    a w ostatniej kolumnie zaznacza, które VM mają skonfigurowany
    USB Power Button w vUSBPB.
    """
    # Wczytaj konfigurację, żeby znać mapowanie vmId -> usbPortId
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

    # Pobierz listę VM z Proxmoxa
    vms = getAllVMs()

    print("VMID   Name             Status     USB devpath")
    print("----------------------------------------------------")

    if not vms:
        # brak maszyn albo qm list zwrócił błąd
        return 0

    for vm in vms:
        try:
            vm_id_int = int(vm.get("vmId", -1))
        except (TypeError, ValueError):
            continue

        name = vm.get("name", "")
        status = vm.get("status", "unknown")
        usb_port_id = vmid_to_usb.get(vm_id_int, "-")

        print(f"{vm_id_int:<6} {name:<16} {status:<10} {usb_port_id}")

    return 0


def listVMPowerButton() -> int:
    """
    `vusbpb --list`

    Pokazuje TYLKO to, co jest skonfigurowane w vUSBPB,
    czyli mapowanie VMID -> USB devpath, wraz ze statusem VM.
    """
    try:
        config = loadConfig(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = getVmMappings(config)

    print("VMID   USB devpath   Status")
    print("-----------------------------------")

    if not mappings:
        return 0

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

        print(f"{vm_id_int:<6} {usb_port_id:<12} {status_str}")

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
