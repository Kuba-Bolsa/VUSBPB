import os
import subprocess

from .config import CONFIG_PATH, saveConfig, loadConfig


def install() -> int:
    if os.path.exists("/etc/systemd/system/vusbpb.service"):
        print("vUSBPB is already installed. Use --uninstall first")
        return 1

    if not os.path.exists(CONFIG_PATH):
        config = {"VMS": [], "USB": []}
        try:
            saveConfig(config)
        except Exception as error:
            print(f"ERROR: cannot create config file: {error}")
            return 1

    systemdContent = f"""[Unit]
Description=Virtual USB Power Button daemon (vUSBPB)
After=network.target

[Service]
ExecStart=/usr/bin/vusbpb --daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    try:
        with open("/etc/systemd/system/vusbpb.service", "w", encoding = "utf-8") as file:
            file.write(systemdContent)
    except Exception as error:
        print(f"ERROR: cannot write systemd service file: {error}")
        return 1

    if not helperRun(["systemctl", "daemon-reload"]):
        print("WARNING: systemctl daemon-reload failed")

    if not helperRun(["systemctl", "enable", "--now", "vusbpb.service"]):
        print("ERROR: cannot enable/start service")
        return 1

    print("vUSBPB installed and started as a systemd service!")
    return 0


def uninstall() -> int:
    helperRun(["systemctl", "stop", "vusbpb.service"], ignore_errors = True)
    helperRun(["systemctl", "disable", "vusbpb.service"], ignore_errors = True)

    if os.path.exists("/etc/systemd/system/vusbpb.service"):
        try:
            os.remove("/etc/systemd/system/vusbpb.service")
        except Exception as error:
            print(f"ERROR: cannot remove service file: {error}")
            return 1

    helperRun(["systemctl", "daemon-reload"], ignore_errors = True)

    if os.path.exists(CONFIG_PATH):
        try:
            os.remove(CONFIG_PATH)
        except Exception as error:
            print(f"ERROR: cannot remove config file: {error}")
            return 1

    print("vUSBPB uninstalled. Service and config removed")
    return 0


# Helpers
def helperRun(cmd: list[str], ignore_errors: bool = False) -> bool:
    try:
        result = subprocess.run(cmd, check = False)
        if result.returncode != 0 and not ignore_errors:
            return False
        return True
    except Exception:
        return False if not ignore_errors else True