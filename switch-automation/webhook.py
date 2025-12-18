from fastapi import FastAPI, Request
from switch_automation import handle_interface_event
import subprocess
import re
import json

app = FastAPI()

@app.post("/linkup")
async def linkup(request: Request):
    data = await request.json()

    print("========== RAW DATA FROM GRAYLOG ==========")
    print(json.dumps(data, indent=4))
    print("============================================")

    # Defaults
    switch = None
    message = None

    #
    # Try backlog first (this contains the REAL syslog message)
    #
    backlog = data.get("backlog", [])
    if backlog:
        first = backlog[0]
        message = first.get("message")
        switch = first.get("source")

    #
    # Fallback to event-level fields (summary, not useful for interface detection)
    #
    if not message:
        evt = data.get("event", {})
        message = evt.get("message")

    if not switch:
        evt = data.get("event", {})
        switch = evt.get("source")

    print("Detected Switch:", switch)
    print("Detected Message:", message)

    # Extract interface name from the syslog message
    iface = None
    if message:
        match = re.search(r'(?:Interface|interface)\s+([A-Za-z0-9/]+)', message)
        if match:
            iface = match.group(1)

    print("Extracted Interface:", iface)
    # Call the automation function
    handle_interface_event(
        switch_ip=switch,
        interface_name=iface,
        username="admin",
        password="TYAaAS32hd"
    )
    #
    # Only call Ansible for valid events
    #
    if switch and iface:
        print(f"Triggering automation for switch={switch}, interface={iface}")

        # subprocess.call([
        #     "ansible-playbook",
        #     "C:/ansible/handle_portup.yml",
        #     "-e", f"switch={switch}",
        #     "-e", f"interface={iface}"
        # ])
    else:
        print("Missing switch or interface, ignoring event.")

    return {"status": "ok", "switch": switch, "interface": iface}
