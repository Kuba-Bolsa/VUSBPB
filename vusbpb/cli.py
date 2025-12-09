import argparse
import os
import sys

from .usb import showUSB
from .vm import showVMFromSystem, addVMPowerButton, deleteVMPowerButton, listVMPowerButton
from .systemd import (install as doInstall, uninstall as doUninstall, daemonRestartIfInstalled)
from .daemon import runDaemon


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog = "vusbpb",
        description = "Virtual USB Power Button for Proxmox Virtual Machines"
    )

    parser.add_argument(
        "--install",
        action = "store_true",
        help = "Install vUSBPB as a systemd daemon",
    )
    parser.add_argument(
        "--uninstall",
        action = "store_true",
        help = "Uninstall vUSBPB systemd daemon and remove config files",
    )
    parser.add_argument(
        "--daemon",
        action = "store_true",
        help = "Run vUSBPB daemon (used by systemd)",
    )
    parser.add_argument(
        "--list",
        choices = ["usb", "vm", "pb"],
        help = "List: 'usb' (USB ports), 'vm' (VMs), 'pb' (VM power buttons)",
    )
    parser.add_argument(
        "--add",
        type = int,
        help = "Add USB power button for VM, requires --usbport and/or --usbdevice",
    )
    parser.add_argument(
        "--delete",
        type = int,
        help = "Delete VM mapping by VM ID",
    )
    parser.add_argument(
        "--usbport",
        type = str,
        help = "USB port devpath (e.g. 1-1.2, 3-0:1.0) used with --add "
            "(use '--list usb' as a helper)",
    )
    parser.add_argument(
        "--usbdevice",
        type = str,
        help = "USB device ID (idVendor:idProduct, e.g. 1234:abcd) used with --add",
    )
    parser.add_argument(
        "--version",
        action = "store_true",
        help = "Show version and exit",
    )

    return parser


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
        requireProxmox()
        requireRoot()
        return doInstall()
    if args.uninstall:
        requireProxmox()
        requireRoot()
        return doUninstall()

    # DAEMON
    if args.daemon:
        requireProxmox()
        requireRoot()
        return runDaemon()

    # LIST: usb / vm / pb
    if args.list == "usb":
        requireRoot()
        return showUSB()
    if args.list == "vm":
        requireProxmox()
        requireRoot()
        return showVMFromSystem()
    if args.list == "pb":
        requireProxmox()
        return listVMPowerButton()

    # ADD / DELETE VM MAPPING
    if args.add is not None:
        if not args.usbport and not args.usbdevice:
            print("--add requires at least one of: "
                "--usbport PORT_ID or --usbdevice VENDOR:PRODUCT")
            return 1
        requireProxmox()
        requireRoot()
        result = addVMPowerButton(args.add, args.usbport, args.usbdevice)
        if result == 0:
            daemonRestartIfInstalled()
        return result

    if args.delete is not None:
        requireProxmox()
        requireRoot()
        result = deleteVMPowerButton(args.delete)
        if result == 0:
            daemonRestartIfInstalled()
        return result

    # Default: HELP
    parser.print_help()
    return 0


# Helpers
def requireRoot() -> None:
    if os.geteuid() != 0:
        print("This command must be executed as root!")
        raise SystemExit(1)


def requireProxmox() -> bool:
    if os.path.isdir("/etc/pve"):
        return True

    print("This tool is intended to run on Proxmox VE host only")
    raise SystemExit(1)