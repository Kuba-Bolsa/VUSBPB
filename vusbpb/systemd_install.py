# vusbpb/systemd_install.py
import os
import subprocess

from .config import CONFIG_PATH, save_config, load_config


SERVICE_PATH = "/etc/systemd/system/vusbpb.service"


def _run(cmd: list[str], ignore_errors: bool = False) -> bool:
    """Uruchamia komendę shellową. Zwraca True gdy exit code == 0."""
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0 and not ignore_errors:
            return False
        return True
    except Exception:
        return False if not ignore_errors else True


def install() -> int:
    """
    Implementacja `vusbpb --install`.
    Tworzy config (jeśli nie istnieje), tworzy service, enable + start.
    """
    if os.path.exists(SERVICE_PATH):
        print("vUSBPB is already installed. Use --uninstall first.")
        return 1

    # Upewnij się, że config istnieje
    if not os.path.exists(CONFIG_PATH):
        config = {"VMS": [], "USB": []}
        try:
            save_config(config)
        except Exception as e:
            print(f"ERROR: cannot create config file: {e}")
            return 1

    # Zapis pliku serwisu
    service_content = f"""[Unit]
Description=Virtual USB Power Button daemon (vUSBPB)
After=network.target

[Service]
ExecStart=/usr/bin/vusbpb --daemon
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""

    try:
        with open(SERVICE_PATH, "w", encoding="utf-8") as f:
            f.write(service_content)
    except Exception as e:
        print(f"ERROR: cannot write systemd service file: {e}")
        return 1

    # Reload systemd
    if not _run(["systemctl", "daemon-reload"]):
        print("WARNING: systemctl daemon-reload failed")

    # Enable + start
    if not _run(["systemctl", "enable", "--now", "vusbpb.service"]):
        print("ERROR: cannot enable/start service")
        return 1

    print("vUSBPB installed and started as a systemd service.")
    return 0


def uninstall() -> int:
    """
    Implementacja `vusbpb --uninstall`.
    Zatrzymuje serwis, usuwa go i usuwa config.
    """
    _run(["systemctl", "stop", "vusbpb.service"], ignore_errors=True)
    _run(["systemctl", "disable", "vusbpb.service"], ignore_errors=True)

    if os.path.exists(SERVICE_PATH):
        try:
            os.remove(SERVICE_PATH)
        except Exception as e:
            print(f"ERROR: cannot remove service file: {e}")
            return 1

    _run(["systemctl", "daemon-reload"], ignore_errors=True)

    # Usuń też config
    if os.path.exists(CONFIG_PATH):
        try:
            os.remove(CONFIG_PATH)
        except Exception as e:
            print(f"ERROR: cannot remove config file: {e}")
            return 1

    print("vUSBPB uninstalled. Service and config removed.")
    return 0
