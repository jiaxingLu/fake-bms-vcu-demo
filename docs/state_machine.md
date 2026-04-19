# Fake BMS Demo – State Machine v1.0

## 1. Purpose

This document defines the minimal VCU-side state machine for the Fake BMS–VCU integration demo.

The purpose of the state machine is to convert received BMS status signals and local VCU input signals into deterministic vehicle-side operational states. The state machine is intentionally minimal and designed for software prototype validation rather than production deployment.

---

## 2. State Overview

The Fake_VCU shall operate with the following top-level states:

- `S0_STARTUP`
- `S1_READY`
- `S2_DRIVE_ENABLED`
- `S3_CHARGING`
- `S4_FAULT`
- `S5_ESTOP`
- `S6_COMM_LOST`

---

## 3. State Definitions

### 3.1 S0_STARTUP
Initial system startup state.

**Actions:**
- initialize internal variables
- initialize communication supervision
- initialize local inputs
- set display state to Startup
- disable drive output

**Exit condition:**
- initialization completed

**Next state:**
- `S1_READY`

---

### 3.2 S1_READY
System is healthy and ready, but drive is not enabled.

**Actions:**
- `VCU_DriveEnable = 0`
- `VCU_DisplayState = Ready`

**Entry conditions:**
- no emergency stop
- no fault
- no communication timeout
- no charging lockout
- no start request

**Transitions:**
- if `VCU_EStop = 1` -> `S5_ESTOP`
- if `BMS_Fault = 1` -> `S4_FAULT`
- if communication timeout occurs -> `S6_COMM_LOST`
- if `BMS_ChargerPlugged = 1` or `BMS_ChargeActive = 1` -> `S3_CHARGING`
- if `VCU_StartCmd = 1` -> `S2_DRIVE_ENABLED`

---

### 3.3 S2_DRIVE_ENABLED
Drive is permitted.

**Actions:**
- `VCU_DriveEnable = 1`
- `VCU_DisplayState = Drive_Enabled`

**Entry conditions:**
- `VCU_StartCmd = 1`
- no emergency stop
- no fault
- no communication timeout
- no charging lockout

**Transitions:**
- if `VCU_EStop = 1` -> `S5_ESTOP`
- if `BMS_Fault = 1` -> `S4_FAULT`
- if communication timeout occurs -> `S6_COMM_LOST`
- if `BMS_ChargerPlugged = 1` or `BMS_ChargeActive = 1` -> `S3_CHARGING`
- if `VCU_StartCmd = 0` -> `S1_READY`

---

### 3.4 S3_CHARGING
Charging-related lockout state.

**Actions:**
- `VCU_DriveEnable = 0`
- `VCU_ChargingMode = 1`
- `VCU_DisplayState = Charging`

**Entry conditions:**
- `BMS_ChargerPlugged = 1`
  or
- `BMS_ChargeActive = 1`

**Transitions:**
- if `VCU_EStop = 1` -> `S5_ESTOP`
- if `BMS_Fault = 1` -> `S4_FAULT`
- if communication timeout occurs -> `S6_COMM_LOST`
- if charging condition disappears -> `S1_READY`

---

### 3.5 S4_FAULT
BMS fault state.

**Actions:**
- `VCU_DriveEnable = 0`
- `VCU_DisplayState = Fault`
- optional future extension: set `VCU_FaultLatched = 1`

**Entry conditions:**
- `BMS_Fault = 1`

**Transitions:**
- In the current demo version, fault latching and manual reset are not yet implemented.
- Therefore, if `BMS_Fault = 0` and no higher-priority blocking condition exists, the state returns to `S1_READY`.

---

### 3.6 S5_ESTOP
Emergency stop state.

**Actions:**
- `VCU_DriveEnable = 0`
- `VCU_DisplayState = EStop`

**Entry conditions:**
- `VCU_EStop = 1`

**Transitions:**
- if `VCU_EStop = 0` and no higher-priority blocking condition exists -> `S1_READY`

---

### 3.7 S6_COMM_LOST
Communication supervision timeout state.

**Actions:**
- `VCU_DriveEnable = 0`
- `VCU_CommTimeout = 1`
- `VCU_DisplayState = Communication_Lost`

**Entry conditions:**
- no valid `BMS_Status_1` message received within timeout threshold

**Transitions:**
- if valid communication resumes and no higher-priority blocking condition exists -> `S1_READY`

---

## 4. Priority Rules

If multiple blocking conditions are present simultaneously, the following priority shall be applied:

1. `ESTOP`
2. `FAULT`
3. `COMM_LOST`
4. `CHARGING`
5. `DRIVE_ENABLED`
6. `READY`

This means that the VCU state shall always be resolved according to the highest-priority active condition.

---

## 5. Communication Timeout Definition

The Fake_BMS transmits `BMS_Status_1` every 100 ms.

For the first prototype version, communication timeout shall be declared when no valid BMS message is received for more than 300 ms.

---

## 6. State Output Mapping

| State | VCU_DriveEnable | VCU_DisplayState |
|---|---:|---|
| S0_STARTUP | 0 | Startup |
| S1_READY | 0 | Ready |
| S2_DRIVE_ENABLED | 1 | Drive_Enabled |
| S3_CHARGING | 0 | Charging |
| S4_FAULT | 0 | Fault |
| S5_ESTOP | 0 | EStop |
| S6_COMM_LOST | 0 | Communication_Lost |

---

## 7. Pseudocode

```text
if VCU_EStop:
    state = S5_ESTOP
elif BMS_Fault:
    state = S4_FAULT
elif communication_timeout:
    state = S6_COMM_LOST
elif BMS_ChargerPlugged or BMS_ChargeActive:
    state = S3_CHARGING
elif VCU_StartCmd:
    state = S2_DRIVE_ENABLED
else:
    state = S1_READY
```

---

## 8. Scope Boundary

This state machine is limited to the first software prototype.

The following features are intentionally excluded at this stage:

- fault acknowledgement logic
- fault latching implementation
- manual reset sequencing
- debounce handling
- direction plausibility checks
- contactor control
- multi-frame diagnostic communication
- watchdog recovery behavior

These may be added later when the prototype is extended.

---

## 9. Revision
Version: v1.0
Status: Initial definition

---
