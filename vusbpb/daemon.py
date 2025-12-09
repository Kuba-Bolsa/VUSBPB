import time
from typing import Dict, List

from .logging_util import logInfo, logError, logWarning
from .config import loadConfig, ConfigError
from .vm import getVMStatus, startVM, VmStatus
from .usb import scanUSBPorts


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

    mappings = config.get("VMS", [])
    if not mappings:
        logWarning("No VM mappings found in config. Daemon will run but do nothing")
    else:
        countPortOnly = countDevOnly = countBoth = 0
        for entry in mappings:
            hasPort = bool(entry.get("usbPortId"))
            hasDev  = bool(entry.get("usbDeviceId"))
            if hasPort and hasDev:
                countBoth += 1
            elif hasPort:
                countPortOnly += 1
            elif hasDev:
                countDevOnly += 1
        total = len(mappings)
        logInfo(
            f"Loaded {total} VM mapping(s) "
            f"(port only: {countPortOnly}, device only: {countDevOnly}, port+device: {countBoth})"
        )

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
            usbDeviceId = helperGetUsbDeviceId(usbPortId)

            vmIds = helperFindMatchingVMs(config, usbPortId, usbDeviceId)
            if not vmIds:
                logInfo(
                    f"USB 'add' event on {usbPortId}, "
                    f"device={usbDeviceId or 'unknown'}, no matching VMs"
                )
                continue

            logInfo(
                f"USB 'add' event on {usbPortId}, "
                f"device={usbDeviceId or 'unknown'}, mapped VMs: {vmIds}"
            )

            for vmId in vmIds:
                vmStatus = getVMStatus(vmId)
                if vmStatus == VmStatus.STOPPED:
                    logInfo(f"VM {vmId} is stopped, attempting to start...")
                    ok = startVM(vmId)
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
def helperGetUsbDeviceId(usbPortId: str) -> str | None:
    for port in scanUSBPorts():
        if port.usbPortId == usbPortId and port.usbIsConnected:
            return port.usbDeviceId
    return None


def helperFindMatchingVMs(config: dict, usbPortId: str, usbDeviceId: str | None) -> List[int]:
    result: List[int] = []
    vms = config.get("VMS", [])
    for entry in vms:
        vmId_raw = entry.get("vmId")
        if vmId_raw is None:
            continue
        try:
            vmId = int(vmId_raw)
        except (TypeError, ValueError):
            continue

        portCond = entry.get("usbPortId")
        devCond = entry.get("usbDeviceId")

        if not portCond and not devCond:
            continue

        if portCond and portCond != usbPortId:
            continue

        if devCond:
            if not usbDeviceId or devCond != usbDeviceId:
                continue

        result.append(vmId)

    return result
