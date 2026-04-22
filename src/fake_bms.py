"""
Fake BMS node.
Periodically transmits BMS_Status_1 on a virtual CAN bus.

Behavior:
  - Sends every 100 ms
  - AliveCounter rolls 0..255 and wraps
  - All other signals are hardcoded (nominal battery, no fault)
  - Press Ctrl+C to stop
"""

import time
import threading
import can
from bms_signals import encode_bms_status_1


BMS_STATUS_1_ID = 0x180
CYCLE_TIME_S = 0.1


def run(bus, stop_event):
    print(f"[BMS] Started, sending ID 0x{BMS_STATUS_1_ID:03X} every {CYCLE_TIME_S*1000:.0f} ms")

    alive_counter = 0
    next_send_time = time.time()

    try:
        while not stop_event.is_set():
            data = encode_bms_status_1(
                soc=50,
                temp_max_raw=250,
                charger_plugged=0,
                charge_active=0,
                fault=0,
                warning=0,
                alive_counter=alive_counter
            )

            msg = can.Message(
                arbitration_id=BMS_STATUS_1_ID,
                data=data,
                is_extended_id=False
            )
            bus.send(msg)

            # Advance AliveCounter (wrap 0..255)
            alive_counter = (alive_counter + 1) % 256

            # Schedule next cycle precisely
            next_send_time += CYCLE_TIME_S
            sleep_duration = next_send_time - time.time()
            if sleep_duration > 0:
                time.sleep(sleep_duration)

    except KeyboardInterrupt:
        print("\n[BMS] Stopping...")
    finally:
        print("[BMS] Stopped cleanly.")

if __name__ == "__main__":
    # Standalone mode: create bus, run, then clean up
    bus = can.Bus(interface="virtual", channel="demo_bus")
    stop_event = threading.Event()
    try:
        run(bus, stop_event)
    finally:
        bus.shutdown()
        print("[BMS] Bus closed.")
