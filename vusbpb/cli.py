import argparse
import os
import sys

from .usb import showUSB
from .vm import show_vm, addVMPowerButton, deleteVMPowerButton, listVMappings
from .systemd_install import install as doInstall, uninstall as doUninstall
from .daemon import runDaemon


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vusbpb",
        description="Virtual USB Power Button for Proxmox"
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help="Install vUSBPB as a systemd daemon",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall vUSBPB systemd daemon and remove config files",
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
        "--add",
        type=int,
        help="Add USB power button for VM, requires --usb",
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
        "--list",
        action="store_true",
        help="List VM power buttons",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    return parser


def requireRoot() -> None:
    if os.geteuid() != 0:
        print("This command must be executed as root!")
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = buildParser()
    args = parser.parse_args(argv)

    # VERSION
    if args.version:
        print("vUSBPB v0.5")
        return 0

    # INSTALL / UNINSTALL
    if args.install:
        requireRoot()
        return doInstall()
    if args.uninstall:
        requireRoot()
        return doUninstall()

    # DAEMON
    if args.daemon:
        requireRoot()
        return runDaemon()

    # SHOW: USB
    if args.show == "usb":
        requireRoot()
        return showUSB()

    # SHOW: VM
    if args.show == "vm":
        requireRoot()
        return showSystemVMs()

    # LIST
    if args.list:
        return listVMappings()

    # ADD / DELETE VM MAPPING
    if args.add is not None:
        if not args.usb:
            print("--add requires --usb PORT_ID (use '--show usb' like a helper)")
            return 1
        requireRoot()
        return addVMPowerButton(args.add, args.usb)

    if args.delete is not None:
        requireRoot()
        return deleteVMPowerButton(args.delete)

    # Default: HELP
    parser.print_help()
    return 0
