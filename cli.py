# vusbpb/cli.py
import argparse
import os
import sys

from .usb import show_usb
from .vm import show_vm, add_vm_mapping, delete_vm_mapping


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vusbpb",
        description="vUSBPB - Virtual USB Power Button"
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help="Install vUSBPB as a systemd daemon",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall vUSBPB systemd daemon and remove config",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run vUSBPB daemon (used by systemd)",
    )

    parser.add_argument(
        "--show",
        choices=["usb", "vm"],
        help="Show information: 'usb' or 'vm'",
    )
    parser.add_argument(
        "--no-status",
        action="store_true",
        help="With '--show vm', do not query Proxmox for VM status",
    )

    parser.add_argument(
        "--add",
        type=int,
        help="Add VM mapping: pass Proxmox VMID, requires --usb",
    )
    parser.add_argument(
        "--usb",
        type=str,
        help="USB port devpath (e.g. 1-1.2, 3-0:1.0) used with --add",
    )
    parser.add_argument(
        "--delete",
        type=int,
        help="Delete VM mapping by VMID",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    return parser


def require_root() -> None:
    """Sprawdza, czy uruchomiono jako root."""
    if os.geteuid() != 0:
        print("This operation must be run as root (use sudo).")
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    # --version
    if args.version:
        print("vusbpb version 0.1.0-dev")
        return 0

    # --show usb
    if args.show == "usb":
        return show_usb()

    # --show vm / --show vm --no-status
    if args.show == "vm":
        return show_vm(no_status=args.no_status)

    # --add {vmId} --usb {usbPortId}
    if args.add is not None:
        if not args.usb:
            print("--add requires --usb PORT_ID (e.g. 1-1.2)")
            return 1
        require_root()
        return add_vm_mapping(args.add, args.usb)

    # --delete {vmId}
    if args.delete is not None:
        require_root()
        return delete_vm_mapping(args.delete)

    # Na razie --install, --uninstall, --daemon niezaimplementowane
    if args.install or args.uninstall or args.daemon:
        print("Install/uninstall/daemon not implemented yet in this version.")
        return 1

    # Brak argumentów - pokaż help
    parser.print_help()
    return 0
