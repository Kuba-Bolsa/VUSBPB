
# vUSBPB - Virtual USB Power Button for Proxmox VMs

vUSBPB to lekka, lecz niezwykle funkcjonalna aplikacja zaprojektowana z myślą o automatyzacji uruchamiania maszyn wirtualnych w środowiskach Proxmox, QEMU oraz KVM - i to bez konieczności korzystania z terminala lub interfejsu graficznego.
Jej główną ideą jest stworzenie swoistych „wirtualnych włączników komputerów”, czyli mechanizmu, który potrafi wystartować wybraną maszynę wirtualną w momencie, gdy użytkownik wpina dowolne urządzenie do określonego portu USB.

Dzięki temu obsługa VM może stać się tak intuicyjna, jak włączenie fizycznego komputera: wkładasz pendrive, adapter lub inne urządzenie USB - a przypisana mu maszyna wirtualna uruchamia się automatycznie.

Aplikacja działa jako demon systemowy, stale monitorujący zdarzenia USB w tle. Jej zachowanie jest w pełni konfigurowalne: administrator może zdefiniować dowolną liczbę portów USB oraz przypisać je do konkretnych VM. Pozwala to tworzyć elastyczne scenariusze działania, takie jak:
- start różnych maszyn wirtualnych w zależności od użytego portu USB,
- obsługa wielu urządzeń wyzwalających różne funkcje,
- wygodne sterowanie środowiskiem Proxmox/QEMU/KVM bez interakcji z poziomu konsoli.

Dzięki swojej prostocie i elastyczności vUSBPB sprawdza się w zastosowaniach domowych, biurowych i hobbystycznych - wszędzie tam, gdzie szybki i bezobsługowy start maszyn wirtualnych znacząco ułatwia pracę.
