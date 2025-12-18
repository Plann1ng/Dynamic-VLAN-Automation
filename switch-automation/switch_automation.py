from netmiko import ConnectHandler
import re
import os
from datetime import datetime

LOG_FILE = r"C:\Users\ryusha\Desktop\switch-automation\port_changes.log"

DELL_OUI_PREFIXES = [
    "00:06:5B",
    "00:08:74",
    "00:0B:DB",
    "00:0D:56",
    "00:0F:1F",
    "00:11:43",
    "00:12:3F",
    "00:13:72",
    "00:14:22",
    "00:15:C5",
    "00:18:8B",
    "00:19:B9",
    "00:1A:A0",
    "00:1C:23",
    "00:1D:09",
    "00:1E:4F",
    "00:1E:C9",
    "00:21:70",
    "00:21:9B",
    "00:22:19",
    "00:23:AE",
    "00:24:E8",
    "00:25:64",
    "00:26:B9",
    "00:4E:01",
    "00:B0:D0",
    "00:BE:43",
    "00:C0:4F",
    "04:BF:1B",
    "08:92:04",
    "0C:29:EF",
    "10:65:30",
    "10:7D:1A",
    "10:98:19",
    "10:98:36",
    "14:18:77",
    "14:9E:CF",
    "14:B3:1F",
    "14:FE:B5",
    "18:03:73",
    "18:5A:58",
    "18:66:DA",
    "18:A9:9B",
    "18:DB:F2",
    "18:FB:7B",
    "1C:40:24",
    "1C:72:1D",
    "20:04:0F",
    "20:47:47",
    "20:88:10",
    "24:53:ED",
    "24:6E:96",
    "24:71:52",
    "24:B6:FD",
    "28:00:AF",
    "28:F1:0E",
    "2C:EA:7F",
    "30:D0:42",
    "34:17:EB",
    "34:48:ED",
    "34:73:5A",
    "34:E6:D7",
    "38:14:28",
    "3C:25:F8",
    "3C:2C:30",
    "40:5C:FD",
    "44:A8:42",
    "48:4D:7E",
    "4C:76:25",
    "4C:C5:D9",
    "4C:D7:17",
    "4C:D9:8F",
    "50:9A:4C",
    "54:48:10",
    "54:9F:35",
    "54:BF:64",
    "58:8A:5A",
    "5C:26:0A",
    "5C:F9:DD",
    "60:18:95",
    "60:5B:30",
    "64:00:6A",
    "68:4F:64",
    "6C:2B:59",
    "6C:3C:8C",
    "70:B5:E8",
    "74:78:27",
    "74:86:7A",
    "74:86:E2",
    "74:E6:E2",
    "78:2B:CB",
    "78:45:C4",
    "78:AC:44",
    "80:18:44",
    "84:2B:2B",
    "84:5C:31",
    "84:7B:EB",
    "84:8F:69",
    "88:6F:D4",
    "8C:04:BA",
    "8C:47:BE",
    "8C:E9:FF",
    "8C:EC:4B",
    "90:8D:6E",
    "90:B1:1C",
    "98:40:BB",
    "98:90:96",
    "98:E7:43",
    "A0:29:19",
    "A4:1F:72",
    "A4:4C:C8",
    "A4:BA:DB",
    "A4:BB:6D",
    "A8:3C:A5",
    "A8:99:69",
    "AC:1A:3D",
    "AC:91:A1",
    "AC:B4:80",
    "B0:4F:13",
    "B0:7B:25",
    "B0:83:FE",
    "B4:45:06",
    "B4:E1:0F",
    "B4:E9:B8",
    "B8:2A:72",
    "B8:85:84",
    "B8:AC:6F",
    "B8:CA:3A",
    "B8:CB:29",
    "BC:30:5B",
    "C0:25:A5",
    "C0:3E:BA",
    "C0:47:0E",
    "C4:5A:B1",
    "C4:CB:E1",
    "C4:D6:D3",
    "C8:1F:66",
    "C8:4B:D6",
    "C8:F7:50",
    "CC:48:3A",
    "CC:96:E5",
    "CC:C5:E5",
    "D0:43:1E",
    "D0:46:0C",
    "D0:67:E5",
    "D0:8E:79",
    "D0:94:66",
    "D0:C1:B5",
    "D4:81:D7",
    "D4:A2:CD",
    "D4:AE:52",
    "D4:BE:D7",
    "D4:BE:D9",
    "D8:9E:F3",
    "D8:D0:90",
    "DC:F4:01",
    "E0:D8:48",
    "E0:DB:55",
    "E4:43:4B",
    "E4:54:E8",
    "E4:B9:7A",
    "E4:F0:04",
    "E8:65:5F",
    "E8:B2:65",
    "E8:B5:D0",
    "E8:CF:83",
    "EC:2A:72",
    "EC:F4:BB",
    "F0:1F:AF",
    "F0:4D:A2",
    "F0:D4:E2",
    "F4:02:70",
    "F4:8E:38",
    "F4:EE:08",
    "F8:B1:56",
    "F8:BC:12",
    "F8:CA:B8",
    "F8:DB:88",
    "FC:4C:EA"
]

processed_ports = set()  # key format: "switch_ip|interface"

def log_success(switch, iface, mac, old_vlan, new_vlan):
    """Log only successful VLAN changes."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = (
        f"[{timestamp}] SWITCH={switch} "
        f"INTERFACE={iface} MAC={mac} "
        f"VLAN {old_vlan} -> {new_vlan}"
    )

    # Ensure directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Append log line
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

    print(line)

def load_processed_ports():
    """Load previously processed ports from the log file."""
    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            parts = line.split()

            # Expected minimum number of parts
            if len(parts) < 4:
                print(f"[WARN] Skipping malformed log line: {line}")
                continue

            try:
                # parts[2] = SWITCH=1.2.3.4
                # parts[3] = INTERFACE=Gi1/0/14
                switch = parts[2].split("=")[1]
                iface = parts[3].split("=")[1]
            except Exception as e:
                print(f"[WARN] Skipping unparsable log line: {line}")
                continue

            key = f"{switch}|{iface}"
            processed_ports.add(key)

    print(f"Loaded {len(processed_ports)} previously processed ports.")

def normalize_mac(mac_raw):
    clean = mac_raw.replace(".", "").lower()
    return ":".join(clean[i:i+2] for i in range(0, 12, 2))

def get_oui(mac):
    return mac[0:8].upper()

def is_dell_mac(mac):
    oui = get_oui(mac)
    return oui in [p.upper() for p in DELL_OUI_PREFIXES]

def handle_interface_event(switch_ip, interface_name, username, password):
    key = f"{switch_ip}|{interface_name}"

    # PREVENT REPROCESSING
    if key in processed_ports:
        print(f"[SKIP] Already migrated earlier: {switch_ip} {interface_name}")
        return

    print(f"[INFO] Processing event: {switch_ip} {interface_name}")

    device = {
        "device_type": "cisco_ios",
        "host": switch_ip,
        "username": username,
        "password": password,
    }

    # CONNECT TO SWITCH
    try:
        net = ConnectHandler(**device)
    except Exception as e:
        print(f"[ERROR] Cannot connect to switch {switch_ip}: {e}")
        return

    # GET MAC + VLAN
    output = net.send_command(f"show mac address-table interface {interface_name}")

    match = re.search(
        r"(\d+)\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})",
        output
    )

    if not match:
        print(f"[INFO] No MAC found on {switch_ip} {interface_name} — likely nothing connected.")
        net.disconnect()
        return

    vlan = match.group(1)
    mac_raw = match.group(2)
    mac = normalize_mac(mac_raw)

    print(f"[INFO] Found MAC {mac} on VLAN {vlan} at {switch_ip} {interface_name}")

    # CHECK IF DELL
    if not is_dell_mac(mac):
        print(f"[INFO] MAC {mac} is NOT Dell OUI — skipping automation.")
        net.disconnect()
        return

    # CHECK IF VLAN IS 3
    if vlan != "3":
        print(f"[INFO] Device is Dell but VLAN is {vlan}, not 3 — skipping.")
        net.disconnect()
        return

    # VLAN CHANGE
    print(f"[ACTION] Changing VLAN from 3 to 3010 on {switch_ip} {interface_name}")

    config = [
        f"interface {interface_name}",
        "switchport access vlan 3010",
        "shutdown",
        "no shutdown"
    ]

    try:
        net.send_config_set(config)
        net.save_config()
    except Exception as e:
        print(f"[ERROR] VLAN change failed on {switch_ip} {interface_name}: {e}")
        net.disconnect()
        return

    # LOG SUCCESS
    log_success(
        switch=switch_ip,
        iface=interface_name,
        mac=mac,
        old_vlan=vlan,
        new_vlan="3010"
    )

    processed_ports.add(key)

    print(f"[DONE] Migration completed and logged for {switch_ip} {interface_name}")

    net.disconnect()

load_processed_ports()
