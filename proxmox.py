# vusbpb/proxmox.py
import subprocess
from enum import Enum, auto


class VmStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    UNKNOWN = auto()


def get_vm_status(vm_id: int) -> VmStatus:
    """
    Zwraca status VM z Proxmoxa na podstawie `qm status <vmid>`.

    RUNNING / STOPPED / UNKNOWN przy błędzie lub nieznanym statusie.
    """
    try:
        result = subprocess.run(
            ["qm", "status", str(vm_id)],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        # qm nie istnieje / nie ma uprawnień
        return VmStatus.UNKNOWN

    if result.returncode != 0:
        # Np. VM nie istnieje
        return VmStatus.UNKNOWN

    for line in result.stdout.splitlines():
        line = line.strip().lower()
        if line.startswith("status:"):
            status_value = line.split(":", 1)[1].strip()
            if status_value == "running":
                return VmStatus.RUNNING
            if status_value == "stopped":
                return VmStatus.STOPPED
            return VmStatus.UNKNOWN

    return VmStatus.UNKNOWN


def start_vm(vm_id: int) -> bool:
    """
    Uruchamia VM przez `qm start <vmid>`.
    Zwraca True, jeśli exit code == 0.
    """
    try:
        result = subprocess.run(
            ["qm", "start", str(vm_id)],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False

    return result.returncode == 0
