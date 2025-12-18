from netmiko import ConnectHandler
import re
import os
from datetime import datetime

from switch_automation import DELL_OUI_PREFIXES, normalize_mac, is_dell_mac

LOG_FILE = r"C:\Users\ryusha\Desktop\switch-automation\single_switch_port_changes.log"


###############################################################
# LOGGING
###############################################################
def log_change(switch, iface, mac, old_vlan, new_vlan):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = (
        f"[{timestamp}] SWITCH={switch} "
        f"INTERFACE={iface} MAC={mac} "
        f"VLAN {old_vlan} -> {new_vlan}"
    )

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

    print(line)


###############################################################
# STATIC ACCESS CHECK (bulletproof, exact match)
###############################################################
def is_static_access_port(net, iface):
    """
    Returns True ONLY if the port is exactly:
        Administrative Mode: static access
    Any deviation (dynamic, trunk, monitor, tunnel, etc.) → unsafe → skip.
    """
    output = net.send_command(
        f"show interface {iface} switchport | include Administrative Mode"
    ).strip()

    return output == "Administrative Mode: static access"


###############################################################
# MAIN SWITCH SCAN AND MIGRATION
###############################################################
def scan_and_migrate(switch_ip, username, password):
    print(f"Connecting to {switch_ip}...")

    device = {
        "device_type": "cisco_ios",
        "host": switch_ip,
        "username": username,
        "password": password,
    }

    # Connect to device
    try:
        net = ConnectHandler(**device)
    except Exception as e:
        print(f"ERROR: Could not connect to {switch_ip}: {e}")
        return

    print("Connected successfully.\n")
    print("Fetching MAC address-table for VLAN 3 only...")

    # Pull ONLY VLAN 3 MAC table entries
    mac_table = net.send_command("show mac address-table vlan 3")

    # Extract: MAC address + Interface (VLAN is always 3, so no need to capture)
    matches = re.findall(
        r"3\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\w+\s+([A-Za-z0-9/]+)",
        mac_table
    )

    if not matches:
        print("No VLAN 3 MAC entries found.")
        net.disconnect()
        return

    print(f"Found {len(matches)} VLAN 3 entries. Processing...\n")

    # Process each entry
    for raw_mac, iface in matches:
        mac = normalize_mac(raw_mac)

        print(f"Checking {iface} — MAC {mac} (VLAN 3)")

        # Check if port is static access
        if not is_static_access_port(net, iface):
            print(f"Skipping {iface}: Port is NOT 'static access' — unsafe to modify.")
            continue

        # Check Dell OUI
        if not is_dell_mac(mac):
            print(f"Skipping {iface}: MAC {mac} is NOT Dell.")
            continue

        # Now it is safe to migrate
        print(f"Migrating {iface}: VLAN 3 → 3010")


        config = [
            f"interface {iface}",
            "switchport access vlan 3010",
            "shutdown",
            "no shutdown"
        ]

        try:
            net.send_config_set(config)
            net.save_config()
        except Exception as e:
            print(f"ERROR updating VLAN on {iface}: {e}")
            continue

        # Log success
        log_change(switch_ip, iface, mac, "3", "3010")

    net.disconnect()
    print("\nMigration completed successfully.")


###############################################################
# ENTRY POINT
###############################################################
if __name__ == "__main__":
    switch = input("Enter switch IP/hostname: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    scan_and_migrate(switch, username, password)

