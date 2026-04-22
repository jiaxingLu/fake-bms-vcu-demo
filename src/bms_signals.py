"""
BMS signal encoder.
Packs BMS_Status_1 message according to docs/message_matrix.csv.

Byte layout (DLC=8):
  Byte 0: BMS_SOC            (uint8, 0..100, %)
  Byte 1-2: BMS_Temp_Max     (int16, raw value, Intel little-endian, physical = raw * 0.1 degC)
  Byte 3: packed booleans
    Bit 0: BMS_ChargerPlugged
    Bit 1: BMS_ChargeActive
    Bit 2: BMS_Fault
    Bit 3: BMS_Warning
    Bit 4-7: reserved (0)
  Byte 4: BMS_AliveCounter   (uint8, 0..255, rolling)
  Byte 5: BMS_Checksum       (uint8, sum of bytes 0-4 + 6-7, low 8 bits)
  Byte 6-7: reserved (0x00), included in checksum
"""

import struct


def encode_bms_status_1(soc, temp_max_raw, charger_plugged, charge_active,
                        fault, warning, alive_counter):
    """
    Encode BMS_Status_1 into 8 bytes.

    Args:
        soc: int, 0..100, percent
        temp_max_raw: int, raw value (physical degC * 10)
        charger_plugged: int, 0 or 1
        charge_active: int, 0 or 1
        fault: int, 0 or 1
        warning: int, 0 or 1
        alive_counter: int, 0..255

    Returns:
        bytearray of length 8
    """
    data = bytearray(8)

    # Byte 0: SOC
    data[0] = soc

    # Byte 1-2: Temp_Max, Intel little-endian, signed 16-bit
    # TODO: use struct.pack_into with format "<h" at offset 1
    struct.pack_into("<h", data, 1, temp_max_raw)
    # Byte 3: pack booleans
    # TODO: shift each bool into its bit position and OR them together
    data[3] = (charger_plugged << 0) | (charge_active << 1) | (fault << 2) | (warning << 3)
    # Byte 4: AliveCounter
    data[4] = alive_counter

    # Byte 6-7 stay 0x00 (bytearray initialized to 0)

    # Byte 5: Checksum = sum of byte 0,1,2,3,4,6,7 low 8 bits
    # TODO: compute checksum, skip byte 5 itself, place in byte 5
    data[5] = (data[0] + data[1] + data[2] + data[3] + data[4] + data[6] + data[7]) & 0xFF
    return data

def decode_bms_status_1(data):
    """
    Decode BMS_Status_1 from 8 bytes back into a signals dict.

    Args:
        data: bytes or bytearray of length 8

    Returns:
        dict with keys: soc, temp_max_raw, charger_plugged, charge_active,
                        fault, warning, alive_counter, checksum, checksum_valid
    """
    # Byte 0: SOC
    soc = data[0]

    # Byte 1-2: Temp_Max, Intel little-endian, signed 16-bit
    temp_max_raw = struct.unpack_from("<h", data, 1)[0]

    # Byte 3: unpack booleans
    charger_plugged = (data[3] >> 0) & 1
    charge_active   = (data[3] >> 1) & 1
    fault           = (data[3] >> 2) & 1
    warning         = (data[3] >> 3) & 1

    # Byte 4: AliveCounter
    alive_counter = data[4]

    # Byte 5: Checksum (as transmitted)
    checksum = data[5]

    # Recompute expected checksum from bytes 0,1,2,3,4,6,7
    expected = (data[0] + data[1] + data[2] + data[3] + data[4] + data[6] + data[7]) & 0xFF
    checksum_valid = (checksum == expected)

    return {
        "soc": soc,
        "temp_max_raw": temp_max_raw,
        "charger_plugged": charger_plugged,
        "charge_active": charge_active,
        "fault": fault,
        "warning": warning,
        "alive_counter": alive_counter,
        "checksum": checksum,
        "checksum_valid": checksum_valid,
    }

if __name__ == "__main__":
    # Test case: SOC=50%, Temp=25.0 degC, Charger unplugged, Fault off, Alive=42
    data = encode_bms_status_1(
        soc=50,
        temp_max_raw=250,
        charger_plugged=0,
        charge_active=0,
        fault=0,
        warning=0,
        alive_counter=42
    )
    print("Test 1 (nominal):")
    print("  bytes:", " ".join(f"{b:02X}" for b in data))
    # Test case: Fault + Warning active, others off, Alive=200
    data2 = encode_bms_status_1(
        soc=80,
        temp_max_raw=350,
        charger_plugged=0,
        charge_active=0,
        fault=1,
        warning=1,
        alive_counter=200
    )
    print("Test 2 (fault active):")
    print("  bytes:", " ".join(f"{b:02X}" for b in data2))

    # Round-trip test: encode then decode should reproduce original signals
    print()
    print("Round-trip test:")
    decoded = decode_bms_status_1(data2)
    print(f"  soc             = {decoded['soc']}")
    print(f"  temp_max_raw    = {decoded['temp_max_raw']}")
    print(f"  charger_plugged = {decoded['charger_plugged']}")
    print(f"  charge_active   = {decoded['charge_active']}")
    print(f"  fault           = {decoded['fault']}")
    print(f"  warning         = {decoded['warning']}")
    print(f"  alive_counter   = {decoded['alive_counter']}")
    print(f"  checksum        = 0x{decoded['checksum']:02X}")
    print(f"  checksum_valid  = {decoded['checksum_valid']}")
