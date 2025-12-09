
# vUSBPB - Virtual USB Power Button for Proxmox VMs

vUSBPB is a lightweight yet highly capable application designed to automate the startup of virtual machines in Proxmox, QEMU, and KVM environments—without the need to use a terminal or graphical interface.

Its core concept is to create “virtual power buttons” for virtual machines: a mechanism that automatically starts a selected VM when the user plugs any device into a specified USB port.

This makes managing VMs as intuitive as powering on a physical computer: you insert a USB stick, adapter, or any other USB device—and the VM assigned to that port launches automatically.

The application runs as a system daemon, continuously monitoring USB events in the background. Its behavior is fully configurable: the administrator can define any number of USB ports and assign them to specific VMs. This allows for flexible usage scenarios such as:
- starting different virtual machines depending on which USB port is used,
- handling multiple devices that trigger different actions,
- conveniently controlling the Proxmox/QEMU/KVM environment without interacting with the console.

Thanks to its simplicity and flexibility, vUSBPB is well suited for both home and office environments—anywhere a fast and hands-free virtual machine startup can significantly improve workflow.


## Installation

```bash
git clone https://github.com/Kuba-Bolsa/VUSBPB.git
cd VUSBPB/
python3 -m venv .venv
source .venv/bin/activate
pip install nuitka pyudev
python -m nuitka --standalone --onefile --follow-imports --include-module=pyudev --output-filename=vusbpb.bin main.py
chmod +x ./vusbpb.bin
mv ./vusbpb.bin /usr/bin/vusbpb
```

