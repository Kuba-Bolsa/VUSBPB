# vusbpb/cli.py
import argparse
import sys

from .usb import show_usb


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


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    # Na razie obsługujemy tylko minimum: --show usb i --version.
    if args.version:
        print("vusbpb version 0.1.0-dev")
        return 0

    if args.show == "usb":
        return show_usb()

    # TODO: dalsze komendy: --show vm, --add, --delete, --install, --uninstall, --daemon
    if any([args.install, args.uninstall, args.daemon, args.show == "vm", args.add, args.delete]):
        print("Not implemented yet in this version.")
        return 1

    parser.print_help()
    return 0
