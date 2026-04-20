import can
import time
import threading

sender_bus = can.Bus(interface="virtual", channel="demo_bus")
receiver_bus = can.Bus(interface="virtual", channel="demo_bus")

def sender_task():
    time.sleep(1)
    msg = can.Message(
        arbitration_id=0x123,
        data=[0x11, 0x22, 0x33, 0x44],
        is_extended_id=False
    )
    print("[Sender] Sending message...")
    sender_bus.send(msg)
    print("[Sender] Sent.")


def receiver_task():
    print("[Receiver] Waiting for message...")
    msg = receiver_bus.recv()
    print("[Receiver] Got:")
    print(msg)


receiver_thread = threading.Thread(target=receiver_task)
sender_thread = threading.Thread(target=sender_task)

receiver_thread.start()
sender_thread.start()

receiver_thread.join()
sender_thread.join()

sender_bus.shutdown()
receiver_bus.shutdown()

print("Done.")
