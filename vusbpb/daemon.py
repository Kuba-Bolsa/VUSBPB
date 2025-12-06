import time
from typing import Dict, List

from .logging_util import log_info, log_error, log_warning
from .config import loadConfig, ConfigError
from .proxmox import get_vm_status, start_vm, VmStatus


def _build_port_to_vm_map(config: dict) -> Dict[str, List[int]]:
    """
    Z "VMS" w configu buduje mapę:
    { "1-1.2": [101, 102], "3-0:1.0": [100], ... }
    """
    mapping: Dict[str, List[int]] = {}
    vms = config.get("VMS", [])
    for entry in vms:
        vm_id = entry.get("vmId")
        usb_port_id = entry.get("usbPortId")
        if vm_id is None or not usb_port_id:
            continue
        try:
            vm_id_int = int(vm_id)
        except (TypeError, ValueError):
            continue

        mapping.setdefault(usb_port_id, []).append(vm_id_int)

    return mapping


def runDaemon() -> int:
    """
    Główna logika demona vUSBPB.

    - wczytuje config
    - buduje mapowanie port -> [vmId...]
    - nasłuchuje zdarzeń USB przez pyudev
    - przy action == "add" na skonfigurowanym porcie:
        - jeśli VM jest 'stopped' -> `qm start`
        - jeśli 'running' -> nic
        - jeśli 'unknown' -> log_warning
    """
    try:
        import pyudev
    except ImportError:
        log_error("pyudev is not installed. Please install python3-pyudev.")
        return 1

    log_info("vUSBPB daemon starting")

    try:
        config = loadConfig(allow_missing=False)
    except ConfigError as e:
        log_error(f"Cannot load config: {e}")
        return 1

    port_to_vms = _build_port_to_vm_map(config)
    total_vms = sum(len(v) for v in port_to_vms.values())

    if not port_to_vms:
        log_warning("No VM mappings found in config. Daemon will run but do nothing.")
    else:
        port_list = ", ".join(port_to_vms.keys())
        log_info(f"Loaded {total_vms} VM mappings on ports: {port_list}")

    # Inicjalizacja pyudev
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="usb")

    log_info("Listening for USB 'add' events...")

    # iter(monitor.poll, None) -> blokujące czekanie na kolejne eventy
    try:
        for device in iter(monitor.poll, None):
            # device.attributes / device.sys_name / device.action
            action = getattr(device, "action", None)
            sys_name = getattr(device, "sys_name", None)

            if action is None or sys_name is None:
                continue

            # Interesują nas tylko zdarzenia "add"
            if action != "add":
                continue

            port_id = sys_name  # np. "1-1.2", "3-0:1.0"

            if port_id not in port_to_vms:
                # Ten port nie jest skonfigurowany jako power button
                continue

            vm_ids = port_to_vms[port_id]
            log_info(f"USB 'add' event on {port_id}, mapped VMs: {vm_ids}")

            for vm_id in vm_ids:
                status = get_vm_status(vm_id)
                if status == VmStatus.STOPPED:
                    log_info(f"VM {vm_id} is stopped, attempting to start...")
                    ok = start_vm(vm_id)
                    if ok:
                        log_info(f"Successfully started VM {vm_id}")
                    else:
                        log_error(f"Failed to start VM {vm_id}")
                elif status == VmStatus.RUNNING:
                    log_info(f"VM {vm_id} is already running; nothing to do")
                else:
                    log_warning(f"Unknown status for VM {vm_id}; skipping start")

    except KeyboardInterrupt:
        log_info("vUSBPB daemon interrupted by user (KeyboardInterrupt)")
        return 0
    except Exception as e:
        log_error(f"Unexpected error in daemon loop: {e}")
        # krótka pauza, żeby nie mielić CPU w kółko w razie błędu
        time.sleep(2)
        return 1
