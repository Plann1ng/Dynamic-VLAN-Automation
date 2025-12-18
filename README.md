# **Automated VLAN Migration System for Cisco Access Ports**

Real-time, event-driven migration of Dell endpoints from VLAN 3 to VLAN 3010

---

![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Status](https://img.shields.io/badge/status-production-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Below is a **clean, professional, production-grade README** that documents **both scripts together** as one system.
It explains the architecture, purpose, workflow, safety rules, installation, usage, logging, and operational requirements.

You can copy/paste this into a file named:

```
README.md
```

---

# README – Automated VLAN Migration System

### (Webhook-Triggered + Manual Bulk Migration Tools)

---

## Overview

This automation system performs **safe, rule-controlled VLAN migration** for Dell endpoints across Cisco switches.
It consists of **two complementary Python applications**, each handling a different operational scenario:

---

## 1. Webhook Automation (`webhook.py` + `switch_automation.py`)

### Purpose

This system reacts **in real-time** when an access port transitions from:

```
LINK DOWN → LINK UP
```

A syslog event from Graylog triggers an HTTP POST toward the webhook listener.
The listener extracts:

* Switch IP/hostname
* Interface name
* Time of the link event

Then it calls the automation engine (`switch_automation.py`), which performs:

### Workflow

1. Connect to the switch via SSH (Netmiko)
2. Run:

   ```
   show mac address-table interface <interface>
   ```
3. If no MAC exists → **no action**
4. Extract VLAN + MAC address
5. Normalize MAC format
6. Compare MAC OUI against **Dell OUI list**
7. If non-Dell → skip
8. If VLAN ≠ 3 → skip
9. Check if port is exactly:

   ```
   Administrative Mode: static access
   ```

   If not → **skip (trunk/phone/uplink protection)**
10. Apply migration:

```
interface <port>
switchport access vlan 3010
shutdown
no shutdown
```

11. Log the successful migration
12. Add the interface to a "processed ports" set so the port is never migrated twice

### Logging

`switch_automation.py` writes entries to:

```
port_changes.log
```

Format:

```
[YYYY-MM-DD HH:MM:SS] SWITCH=<ip> INTERFACE=<iface> MAC=<mac> VLAN 3 -> 3010
```

This log is **persistent**, and previously processed ports are loaded at startup to prevent repeated migrations.

---

## 2. Manual Bulk Migration Tool

### (`single_switch_dynamic_change.py`)

### Purpose

This script handles the *opposite workflow*:

* The port is **already connected**, possibly for days.
* The VLAN still needs migration.
* You want to migrate **all eligible ports on a switch at once**.

This script does not listen to Graylog.
Instead, the administrator runs it manually.

### Workflow

1. Prompt for:

   * Switch IP/hostname
   * Username
   * Password

2. Connect via SSH

3. Pull all VLAN 3 MAC entries:

```
show mac address-table vlan 3 | in DYNAMIC
```

4. For each entry:

   * Extract MAC and interface
   * Normalize MAC
   * Validate Dell OUI
   * Verify **Administrative Mode: static access**
   * (Optional testing mode) Skip unless interface is in your ALLOWED_PORTS list
   * If eligible → apply:

     ```
     interface <port>
     switchport access vlan 3010
     shutdown
     no shutdown
     ```

5. Log each successful migration to:

```
single_switch_port_changes.log
```

### When to use this script

Use this tool when:

* You want to migrate a whole switch at once
* You are onboarding new offices
* You want to catch ports that didn’t trigger a link-up event
* You want to sweep all actively connected Dell devices

---

# Why Two Scripts?

| Script                  | Trigger                 | Best For                  | Detection Method         |
| ----------------------- | ----------------------- | ------------------------- | ------------------------ |
| **Webhook (Real-Time)** | Link UP syslog event    | Users plugging in laptops | Per-interface MAC lookup |
| **Bulk Scan (Manual)**  | Administrator runs tool | PCs already connected     | VLAN-wide MAC table scan |

Both tools **serve the same business goal**, but cover **different operational timing**.

Together, they ensure:

* No Dell device remains on VLAN 3
* Whether the port is connected *now*, or *connected later*
* Whether users plug/unplug randomly
* Whether the migration needs to happen immediately or in batch

---

# Installation Requirements

### Python

Python 3.10+ recommended.

Install dependencies:

```
pip install fastapi uvicorn netmiko
```

### Directory Structure

```
switch-automation/
├── webhook.py
├── switch_automation.py
├── single_switch_dynamic_change.py
├── port_changes.log
├── single_switch_port_changes.log
└── ...
```

---

# Running the Webhook Listener

Start the FastAPI server:

```
uvicorn webhook:app --host 0.0.0.0 --port 33333
```

Graylog must POST link-up events to:

```
http://<automation-server>:33333/linkup
```

When an interface goes UP with a new device, the migration logic triggers automatically.

---

# Running the Manual Bulk Migration Script

```
python single_switch_dynamic_change.py
```

You will be prompted:

```
Enter switch IP/hostname:
Username:
Password:
```

The script processes all Dell devices detected dynamically on VLAN 3.

---

# Safety Features (Critical)

## 1. Trunk / Uplink Protection

The automation **will NEVER** touch a port unless:

```
Administrative Mode: static access
```

This prevents:

* Breaking uplinks
* Removing trunk configuration
* Taking down buildings
* STP topology changes

## 2. Dell OUI Validation

Only Dell OUIs are migrated.

## 3. VLAN Check

Only ports currently in **VLAN 3** are eligible.

## 4. Replay Protection (Webhook mode)

Once a port is migrated, the system never touches it again, even if:

* User unplugs
* User reconnects
* Interface bounces
* Graylog retries the event

## 5. Logging

Every migration is logged with:

* Timestamp
* Switch
* Interface
* MAC
* Before/after VLAN

---

# Recommended Workflow in a Real Migration

### 1. Enable Webhook Listener

Captures real-time plug-in events.

### 2. Run Bulk Tool After Hours

Catches all Dell devices currently connected.

### 3. Validate Logs

Confirm all devices are migrating cleanly.

### 4. Roll Out Site-Wide

---

# Troubleshooting

### Dell MAC appears on trunk port

This is normal. It means the device is behind another switch.
Trunk protection will skip it safely.

### No MAC found

The port is up but nothing is connected.

### VLAN is not 3

The device is already migrated or in another network segment.

### Authentication failures

Verify SSH credentials.

---

# Conclusion

Together, these two scripts form a **complete, safe, and reliable VLAN migration engine** capable of:

* Real-time event-based automation
* Bulk scanning and correction
* Strict safety enforcement
* Full audit logging
* Enterprise-scale switch control

## **Credits**

Developed by **@Plann1ng**
This system provides a lightweight alternative to Cisco ISE dynamic VLAN assignment, built using modern Python automation.
More to come :D.

---
