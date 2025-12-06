# vusbpb/proxmox.py
import subprocess
from enum import Enum, auto
from typing import List, Dict


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
        # qm nie istnieje / brak uprawnień
        return VmStatus.UNKNOWN

    if result.returncode != 0:
        # np. VM nie istnieje
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


def getAllVMs() -> List[Dict[str, str]]:
    try:
        result = subprocess.run(
            ["qm", "list"],
            text=True,
            capture_output=True,
            check=False,
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

        # Ignorujemy warningi i linie nie będące listingiem VM:
        # szukamy tylko linii zaczynających się od cyfry
        # np: "101   Windows10   running ..."
        if not line or not line[0].isdigit():
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        vm_id = parts[0]
        name = parts[1]
        status = parts[2]

        vms.append({
            "vmId": vm_id,
            "name": name,
            "status": status
        })

    return vms
