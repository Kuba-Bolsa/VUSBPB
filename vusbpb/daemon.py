import time
from typing import Dict, List

from .logging_util import logInfo, logError, logWarning
from .config import loadConfig, ConfigError
from .proxmox import get_vm_status, start_vm, VmStatus


def runDaemon() -> int:
    try:
        import pyudev
    except ImportError:
        logError("pyudev is not installed. Please install python3-pyudev")
        return 1
    logInfo("vUSBPB daemon starting")

    try:
        config = loadConfig(allow_missing = False)
    except ConfigError as error:
        logError(f"Can't load config: {error}")
        return 1

    usbPortToVMs = helperBuildPortToVMMap(config)
    totalVMs = sum(len(v) for v in usbPortToVMs.values())

    if not usbPortToVMs:
        logWarning("No VM mappings found in config. Daemon will run but do nothing")
    else:
        portList = ", ".join(usbPortToVMs.keys())
        logInfo(f"Loaded {totalVMs} VM mappings on ports: {portList}")

    portMonitor = pyudev.Monitor.from_netlink(pyudev.Context())
    portMonitor.filter_by(subsystem = "usb")
    logInfo("Listening for USB 'add' events...")

    try:
        for device in iter(portMonitor.poll, None):
            usbAction = getattr(device, "action", None)
            usbSysName = getattr(device, "sys_name", None)

            if usbAction is None or usbSysName is None:
                continue
            if usbAction != "add":
                continue

            usbPortId = usbSysName
            if usbPortId not in usbPortToVMs:
                continue

            vmIds = usbPortToVMs[usbPortId]
            logInfo(f"USB 'add' event on {usbPortId}, mapped VMs: {vmIds}")

            for vmId in vmIds:
                vmStatus = get_vm_status(vmId)
                if vmStatus == VmStatus.STOPPED:
                    logInfo(f"VM {vmId} is stopped, attempting to start...")
                    ok = start_vm(vmId)
                    if ok:
                        logInfo(f"Successfully started VM {vmId}")
                    else:
                        logError(f"Failed to start VM {vmId}")
                elif vmStatus == VmStatus.RUNNING:
                    logInfo(f"VM {vmId} is already running; nothing to do")
                else:
                    logWarning(f"Unknown status for VM {vmId}; skipping start")

    except KeyboardInterrupt:
        logInfo("vUSBPB daemon interrupted by user (KeyboardInterrupt)")
        return 0
    except Exception as error:
        logError(f"Unexpected error in daemon loop: {error}")
        time.sleep(2)
        return 1


# Helpers
def helperBuildPortToVMMap(config: dict) -> Dict[str, List[int]]:
    mapping: Dict[str, List[int]] = {}
    vms = config.get("VMS", [])
    for entry in vms:
        vmId = entry.get("vmId")
        usbPortId = entry.get("usbPortId")
        if vmId is None or not usbPortId:
            continue
        try:
            vmId_int = int(vmId)
        except (TypeError, ValueError):
            continue

        mapping.setdefault(usbPortId, []).append(vmId_int)
    return mapping