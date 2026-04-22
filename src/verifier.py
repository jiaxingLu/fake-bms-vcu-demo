"""
Verifier node.
Listens to BMS_Status_1 on the virtual CAN bus, decodes each frame,
and prints signal values in human-readable form.

Used to validate that fake_bms is emitting correct BMS_Status_1 frames.
"""

import threading
import can
from bms_signals import decode_bms_status_1


BMS_STATUS_1_ID = 0x180


def monitor(bus, stop_event):
    print(f"[Verifier] Listening for ID 0x{BMS_STATUS_1_ID:03X}")

    try:
        while not stop_event.is_set():
            msg = bus.recv(timeout=0.5)
            if msg is None:
               continue

            if msg.arbitration_id != BMS_STATUS_1_ID:
                continue

            signals = decode_bms_status_1(msg.data)

            valid_mark = "OK" if signals["checksum_valid"] else "BAD"
            print(
                f"[Verifier] "
                f"SOC={signals['soc']:3d}% "
                f"Temp={signals['temp_max_raw']/10.0:+5.1f}C "
                f"Plug={signals['charger_plugged']} "
                f"Chg={signals['charge_active']} "
                f"Flt={signals['fault']} "
                f"Wrn={signals['warning']} "
                f"Alive={signals['alive_counter']:3d} "
                f"Chk=0x{signals['checksum']:02X}[{valid_mark}]"
            )

    except KeyboardInterrupt:
        print("\n[Verifier] Stopping...")
    finally:
        print("[Verifier] Stopped cleanly.")


if __name__ == "__main__":
    # Standalone mode: create bus, monitor, then clean up
    bus = can.Bus(interface="virtual", channel="demo_bus")
    stop_event = threading.Event()
    try:
        monitor(bus, stop_event)
    finally:
        bus.shutdown()
        print("[Verifier] Bus closed.")
