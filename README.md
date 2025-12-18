# **Automated VLAN Migration System for Cisco Access Ports**

Real-time, event-driven migration of Dell endpoints from VLAN 3 to VLAN 3010

---

![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Status](https://img.shields.io/badge/status-production-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## **Overview**

This deisgn implements a scenario based automated VLAN migration system for Cisco access switches.
Using syslog-triggered events, a FastAPI webhook, and Netmiko SSH automation, the system detects when a device connects to a switchport, verifies whether it is a **Dell endpoint**, checks whether it is currently in **VLAN 3**, and if so, automatically migrates the port to **VLAN 3010**. (Hardcoded VLANs due to strict requirements, can be further made more flexible if need arises)

The automation reacts immediately to link-up events and requires no polling, no manual intervention, and no human monitoring.

---
## **Key Features**

### **Event-Driven**

Triggered automatically by `%LINK-3-UPDOWN` syslog messages.
No polling, no SNMP overhead, and no performance impact.

### **Dell Device Detection**

Uses an OUI prefix list to identify Dell endpoints accurately.

### **Conditional VLAN Migration**

The system changes VLAN only when:

* A device is physically connected
* The MAC belongs to Dell
* The port is currently in VLAN 3
* The port has not been processed before

### **Safe Port Bounce**

After applying the new VLAN, the port is shut/no shut to force DHCP renewal.

### **Persistent Processed-Port Tracking**

Processed ports are stored in `port_changes.log` and loaded at startup.
This prevents:

* Duplicate automation
* Trigger loops from port bouncing
* Reprocessing when the user unplugs and reconnects

### **Diagnostic Logging**

Every decision and action is printed, including:

* MAC found
* Wrong VLAN
* Non-Dell device
* No MAC learned
* Successful migration
* Previously processed ports being skipped

### **Log Handling**

* No crashes on empty or malformed log entries
* UTF-8 safe

---

## **Architecture**

```
Cisco Switch (syslog)
        |
        v
     Graylog
(Syslog input + Event Definition)
        |
        v
FastAPI Webhook (/linkup)
        |
        v
Automation Engine
(Netmiko Connection)
        |
        v
Decision Logic: --------
- Is Dell?               \  No -> Wait for the next Event
- VLAN 3?                /  
- Already processed?---
        |
        v
VLAN Change to 3010
Shutdown / No Shutdown
Save configuration
        |
        v
Logging + Persistent Cache
```

---

## **Installation**

### 1. Install dependencies

```
pip install fastapi uvicorn netmiko
```

### 2. Clone this repository

```
git clone https://github.com/yourrepo/yourproject.git
cd yourproject
```

### 3. Configure switch credentials

Modify inside `handle_interface_event()`:

```python
device = {
    "device_type": "cisco_ios",
    "host": switch_ip,
    "username": "your_username",
    "password": "your_password"
}
```

### 4. Run the webhook service

```
uvicorn webhook:app --host <Your_Host_IP> --port <Your_Port_IP>
```

### 5. Configure Graylog

Create an Event Definition that matches:

```
%LINK-3-UPDOWN
"changed state to up"
```

Set notification to:

```
http://<server-ip>:33333/linkup
```

---

## **How It Works**

1. A port goes UP on a Cisco switch.
2. The switch sends a syslog message to Graylog.
3. Graylog forwards the event to `/linkup`.
4. The webhook parses the switch IP and interface name.
5. The automation connects via SSH to the switch.
6. It retrieves the MAC address and VLAN.
7. The system checks:

   * Is the MAC a Dell OUI?
   * Is VLAN equal to 3?
   * Has this port been processed before?
8. If conditions match, VLAN is changed to 3010.
9. Port is shut/no shut to force DHCP renewal.
10. A structured log entry is written.
11. The port is added to the in-memory cache.

The system is fully **idempotent** and **stable**.

---

## **Logging**

Successful VLAN migrations are stored in:

```
port_changes.log
```

Example entry:

```
[2025-12-17 16:08:45] SWITCH=xxxx.xxxx.xxxxx INTERFACE=GigabitEthernet1/0/14 MAC=cc:48:3a:46:bc:79 VLAN 3 -> 3010
```

At startup, these entries are parsed to prevent reprocessing.

---

## **Troubleshooting**

| Symptom               | Explanation              | Solution                     |
| --------------------- | ------------------------ | ---------------------------- |
| No action taken       | Device is not Dell       | Expected                     |
| VLAN not migrated     | VLAN is not 3            | Expected                     |
| Script quiet on event | MAC not yet learned      | Normal for first 1–5 seconds |
| VLAN changed twice    | Cache cleared or deleted | Keep log file persistent     |
| No webhook triggers   | Graylog filter incorrect | Confirm event definition     |

---

## **Future Enhancements**

* Slack or Teams notifications
* SQLite database for historical tracking
* Web dashboard showing processed ports
* Configuration file (`config.yaml`)
* Multi-threaded event handling
* Automatic Dell OUI updates via IEEE API

---

## **License**

MIT License
Feel free to use, modify, and improve.

---

## **Credits**

Developed by **Plann1ng**
This system provides a lightweight alternative to Cisco ISE dynamic VLAN assignment, built using modern Python automation.

---
