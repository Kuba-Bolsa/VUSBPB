
# vUSBPB - Virtual USB Power Button for Proxmox VMs

<img align="right" width="500" src="https://private-user-images.githubusercontent.com/209820700/524795673-6ba18f0f-b73d-412d-92a2-4e0fbe755358.gif?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjUzNjc4MzUsIm5iZiI6MTc2NTM2NzUzNSwicGF0aCI6Ii8yMDk4MjA3MDAvNTI0Nzk1NjczLTZiYTE4ZjBmLWI3M2QtNDEyZC05MmEyLTRlMGZiZTc1NTM1OC5naWY_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMjEwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTIxMFQxMTUyMTVaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT01NDliZGI4ZDA4NjRkNjljOGE2MTU3YzdjMDY5YjRjZDYyY2RjNTUyODQzNWRiYzM0YjY5Y2Q0NmIwNzJhM2Q0JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.HXttzxTd7k_7ux8INzztfbplwze3D0MvCbMt80Uy95o">
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


## Usage

After installing the application on the system, start it as a background service (daemon) in Proxmox systemd using the command:
```bash
vusbpb --install
```

---

From that moment on, the program runs in the background. To assign a virtual power button, you need two parameters: the virtual machine ID and the USB port number and/or the USB device ID that should wake the machine. You can display the list of available virtual machines with:
```bash
vusbpb --list vm
```

<p align="center"><img height="350" alt="Screenshot 2025-12-10 at 13 13 38" src="https://github.com/user-attachments/assets/b9d7cf52-a87c-4962-a574-9cfd79a0e3c4" /></p>

---

The next step is to determine the USB port identifiers. The easiest way is to remove the device from the selected USB port and run:
```bash
vusbpb --list usb
```
Then insert the device back into the port and run the command again. This time, the newly used port will be marked accordingly, making it easier to identify.

<p align="center"><img height="350" alt="Screenshot 2025-12-10 at 13 15 06" src="https://github.com/user-attachments/assets/0fd1b074-3cb5-4f05-b05c-8ddc0e7955b5" /></p>

---

Once you know the port number, you can configure the virtual power button:
```bash
vusbpb --add {VM_ID} --usbport {USB_ID}
```

<p align="center"><img height="350" alt="Screenshot 2025-12-10 at 13 17 34" src="https://github.com/user-attachments/assets/bc43bd63-3680-4f85-8b57-ef85785bfada" /></p>

---

If you want the virtual machine to be started only by one specific USB device, use the --usbdevice argument:
```bash
vusbpb --add {VM_ID} --usbdevice {USB_DEVICE_ID}
```

<p align="center"><img height="350" alt="Screenshot 2025-12-10 at 13 16 53" src="https://github.com/user-attachments/assets/09f59b46-eac3-4567-87c3-1b53ee02a78b" /></p>

---

You can remove the assigned virtual power button at any time with:
```bash
vusbpb --delete {VM_ID}
```
