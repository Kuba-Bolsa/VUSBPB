import subprocess
from enum import Enum, auto
from typing import List, Dict


class VmStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    UNKNOWN = auto()


def get_vm_status(vmId: int) -> VmStatus:
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


def start_vm(vmId: int) -> bool:
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