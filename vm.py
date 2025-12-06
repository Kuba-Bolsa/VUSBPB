# vusbpb/vm.py
from typing import Dict, Any, List

from .config import (
    load_config,
    save_config,
    get_vm_mappings,
    set_vm_mappings,
    ConfigError,
)
from .proxmox import get_vm_status, VmStatus


def show_vm(no_status: bool = False) -> int:
    """
    Implementacja `vusbpb --show vm` (+ opcjonalnie --no-status).
    """
    try:
        config = load_config(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = get_vm_mappings(config)

    print("VMID   USB devpath   Status")
    print("-----------------------------------")

    if not mappings:
        # Brak skonfigurowanych maszyn
        return 0

    for m in mappings:
        # Bezpieczne pobieranie pól z fallbackiem
        vm_id = m.get("vmId")
        usb_port_id = m.get("usbPortId", "")

        # Jeśli brak vmId (np. stary/uszkodzony wpis), pomijamy
        if vm_id is None:
            continue

        if no_status:
            status_str = "unknown"
        else:
            status = get_vm_status(int(vm_id))
            if status == VmStatus.RUNNING:
                status_str = "running"
            elif status == VmStatus.STOPPED:
                status_str = "stopped"
            else:
                status_str = "unknown"

        print(f"{str(vm_id):<6} {usb_port_id:<12} {status_str}")

    return 0


def add_vm_mapping(vm_id: int, usb_port_id: str) -> int:
    """
    Implementacja `vusbpb --add {vmId} --usb {usbPortId}`.

    - Nie pozwala dodać drugiego wpisu z tym samym vmId.
    - Pozwala, by wiele VM korzystało z tego samego usbPortId.
    """
    try:
        config = load_config(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = get_vm_mappings(config)

    # Sprawdź, czy vmId już istnieje
    for m in mappings:
        if int(m.get("vmId", -1)) == vm_id:
            print(f"ERROR: VMID {vm_id} is already configured. Use --delete {vm_id} first.")
            return 1

    # Dodaj nowy wpis
    mappings.append(
        {
            "vmId": vm_id,
            "usbPortId": usb_port_id,
        }
    )

    config = set_vm_mappings(config, mappings)

    try:
        save_config(config)
    except ConfigError as e:
        print(f"ERROR: cannot save config: {e}")
        return 1

    print(f"Added VMID {vm_id} with USB devpath {usb_port_id}.")
    return 0


def delete_vm_mapping(vm_id: int) -> int:
    """
    Implementacja `vusbpb --delete {vmId}`.

    - Usuwa wszystkie wpisy dla danego vmId (teoretycznie powinna być max 1).
    """
    try:
        config = load_config(allow_missing=True)
    except ConfigError as e:
        print(f"ERROR: cannot load config: {e}")
        return 1

    mappings: List[Dict[str, Any]] = get_vm_mappings(config)

    new_mappings = [m for m in mappings if int(m.get("vmId", -1)) != vm_id]

    removed_count = len(mappings) - len(new_mappings)

    if removed_count == 0:
        print(f"No mapping found for VMID {vm_id}. Nothing to delete.")
        return 0

    config = set_vm_mappings(config, new_mappings)

    try:
        save_config(config)
    except ConfigError as e:
        print(f"ERROR: cannot save config: {e}")
        return 1

    print(f"Removed {removed_count} mapping(s) for VMID {vm_id}.")
    return 0
