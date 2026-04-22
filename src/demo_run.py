"""
Demo runner: launches fake_bms and verifier in two threads
sharing a virtual CAN bus, and coordinates graceful shutdown.
"""

import threading
import can

import fake_bms
import verifier


def main():
    # Create two independent bus objects on the same virtual channel.
    # This is required because python-can's VirtualBus does not loop
    # messages back to the sender bus object.
    bms_bus = can.Bus(interface="virtual", channel="demo_bus")
    verifier_bus = can.Bus(interface="virtual", channel="demo_bus")

    stop_event = threading.Event()

    verifier_thread = threading.Thread(
        target=verifier.monitor,
        args=(verifier_bus, stop_event),
        name="verifier"
    )
    bms_thread = threading.Thread(
        target=fake_bms.run,
        args=(bms_bus, stop_event),
        name="fake_bms"
    )

    # Start verifier first so it is ready to receive before BMS sends.
    verifier_thread.start()
    bms_thread.start()

    print("[Demo] Running. Press Ctrl+C to stop.")

    try:
        # Main thread waits. The Event.wait() call blocks until either
        # the event is set or the user hits Ctrl+C.
        stop_event.wait()
    except KeyboardInterrupt:
        print("\n[Demo] Ctrl+C received.")
    finally:
        stop_event.set()

        # Wait for both threads to finish their cleanup.
        bms_thread.join()
        verifier_thread.join()

        # Now it is safe to close the buses.
        bms_bus.shutdown()
        verifier_bus.shutdown()
        print("[Demo] All resources closed.")


if __name__ == "__main__":
    main()
