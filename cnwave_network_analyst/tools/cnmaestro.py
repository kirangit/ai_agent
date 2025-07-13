# File: cnmaestro.py

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging
import time

load_dotenv()

CNMAESTRO_URL = os.getenv("CNMAESTRO_URL", "qa.cloud.cambiumnetworks.com")
CNMAESTRO_CLIENT_ID = os.getenv("CNMAESTRO_CLIENT_ID")
CNMAESTRO_CLIENT_SECRET = os.getenv("CNMAESTRO_CLIENT_SECRET")
CNMAESTRO_REDIRECT_URL = None

logger = logging.getLogger("cnmaestro")

_cached_token = None
_token_timestamp = 0
TOKEN_EXPIRY_BUFFER = 300  # seconds before actual expiry

def apply_fields_param(endpoint: str, fields: str | None) -> str:
    if not fields:
        return endpoint

    # Known bad or unsupported fields in link statistics
    invalid_fields = {"tx_rssi", "rx_rssi", "tx_snr"}

    # Map of aliases → canonical names
    alias_map = { "mcs": "rx_mcs", "snr": "rx_snr" }

    # Split, strip, map aliases, and de-duplicate
    field_set = {
        alias_map.get(f.strip(), f.strip())
        for f in fields.split(",")
        if f.strip()
    }
    
    # Split fields into a set for easy check, remove duplicates
    field_set = set(f.strip() for f in fields.split(',') if f.strip())

    # Remove invalid fields
    field_set -= invalid_fields

    # Force inclusion of required fields
    field_set.update(["a_node_name", "z_node_name"])

    # Rebuild the string
    final_fields = ",".join(sorted(field_set))

    # Append to endpoint
    if "?" in endpoint:
        return f"{endpoint}&fields={final_fields}"
    else:
        return f"{endpoint}?fields={final_fields}"

def get_bearer_token():
    global _cached_token, _token_timestamp
    global CNMAESTRO_REDIRECT_URL

    now = time.time()
    if _cached_token and (now - _token_timestamp) < (3600 - TOKEN_EXPIRY_BUFFER):
        return _cached_token

    url = f"https://{CNMAESTRO_URL}/api/v2/access/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CNMAESTRO_CLIENT_ID,
        "client_secret": CNMAESTRO_CLIENT_SECRET
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    token = response.json()["access_token"]
    CNMAESTRO_REDIRECT_URL = response.json()['redirect_uri']

    _cached_token = token
    _token_timestamp = now
    return token

def get_api(endpoint: str, token: str):
    endpoint = endpoint.lstrip("/")
    url = f"{CNMAESTRO_REDIRECT_URL}/api/v2/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "*/*"
    }
    logger.debug(f"Calling API: {url}")
    response = requests.get(url, headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error(f"Error response: {response.status_code}, {response.text}")
        return {"status": "error", "code": response.status_code, "details": response.text}

    logger.debug(f"Response received from {url}")
    return response.json()

def wireless_mac_to_node_mac(wireless_mac: str) -> str:
    """
    Converts a wireless MAC address to a node MAC address based on custom rules:
    - If the first octet is 12 or 22, replace it with 00
    - If the first octet is 42, replace it with 30
    """
    mac_parts = wireless_mac.lower().replace('-', ':').split(':')

    if len(mac_parts) != 6:
        return wireless_mac

    first_octet = mac_parts[0]

    if first_octet == '12' or first_octet == '22':
        mac_parts[0] = '00'
    elif first_octet == '42':
        mac_parts[0] = '30'

    return ':'.join(mac_parts)

def get_networks():
    token = get_bearer_token()
    return get_api("networks", token)

def get_devices(network: str = None, limit: str = None, offset: str = None, type: str = "cnwave60", online: bool = None, sort: str = None, site: str = None, fields: str = None):
    token = get_bearer_token()
    query = []
    if limit:
        query.append(f"limit={limit}")
    if offset:
        query.append(f"offset={offset}")        
    if network:
        query.append(f"network={network}")
    if online is not None:
        query.append(f"online={'true' if online else 'false'}")
    if sort:
        query.append(f"sort={sort}")
    if site:
        query.append(f"site={site}")
    if type:
        query.append(f"type={type}")
    if fields:
        query.append(f"fields={fields}")        
    
    endpoint = f"/devices"
    if query:
        endpoint += "?" + "&".join(query)
    print({endpoint})
    return get_api(endpoint, token)

def get_sites(network_id: str):
    token = get_bearer_token()
    endpoint = f"networks/{network_id}/sites"
    print(endpoint)
    return get_api(endpoint, token)

def get_site(network_id: str, site_id: str):
    token = get_bearer_token()
    endpoint = f"networks/{network_id}/sites/{site_id}"
    print(endpoint)
    return get_api(endpoint, token)

def get_links(network_id: str, fields: str = None):
    token = get_bearer_token()
    endpoint = f"cnwave60/networks/{network_id}/links"
    if fields:
        endpoint += f"?fields={fields}"
    print({endpoint})
    return get_api(endpoint, token)

def get_network_links_statistics(network_id: str, limit: str = None, offset: str = None, fields: str | None = None):
    token = get_bearer_token()
    endpoint = f"cnwave60/networks/{network_id}/links/statistics"

    query = []
    if limit:
        query.append(f"limit={limit}")
    if offset:
        query.append(f"offset={offset}")        

    if query:
        endpoint += "?" + "&".join(query)

    endpoint = apply_fields_param(endpoint, fields)

    print({endpoint})
    return get_api(endpoint, token)

def get_link_statistics_for_device(mac: str, fields: str | None = None):
    token = get_bearer_token()
    mac = wireless_mac_to_node_mac(mac)
    endpoint = f"cnwave60/devices/{mac}/links/statistics"
    endpoint = apply_fields_param(endpoint, fields)
    print({endpoint})
    return get_api(endpoint, token)

def get_single_link_statistics_for_device(mac: str, link_name: str, fields: str | None = None):
    token = get_bearer_token()
    mac = wireless_mac_to_node_mac(mac)
    endpoint = f"cnwave60/devices/{mac}/links/{link_name}/statistics"
    endpoint = apply_fields_param(endpoint, fields)
    print({endpoint})
    return get_api(endpoint, token)

def get_device_link_performance(mac: str, link_name: str, start_time: str = None, stop_time: str = None):
    token = get_bearer_token()
    mac = wireless_mac_to_node_mac(mac)
    query = []
    if start_time:
        query.append(f"start_time={start_time}")
    if stop_time:
        query.append(f"stop_time={stop_time}")
    endpoint = f"cnwave60/devices/{mac}/links/{link_name}/performance"
    if query:
        endpoint += "?" + "&".join(query)
    print(endpoint)
    return get_api(endpoint, token)

def get_device_overrides(network_id: str, name: str = None):
    token = get_bearer_token()
    endpoint = f"cnwave60/networks/{network_id}/devices/overrides"
    if name:
        endpoint += f"?name={name}"
    print(endpoint)
    return get_api(endpoint, token)

def get_controller_info(network_id: str):
    token = get_bearer_token()
    endpoint = f"cnwave60/networks/{network_id}/controller"
    print(endpoint)
    return get_api(endpoint, token)

def get_network_device_statistics(network_id: str, limit: str = None, offset: str = None, fields: str = None):
    """Returns real-time statistics for all cnWave devices in a given network."""
    token = get_bearer_token()
    endpoint = f"devices/statistics"
    query = []
    query.append(f"network={network_id}")
    if limit:
        query.append(f"limit={limit}")
    if offset:
        query.append(f"offset={offset}")    
    if fields:
        query.append(f"fields={fields}")
    if query:
        endpoint += "?" + "&".join(query)
    print(endpoint)
    return get_api(endpoint, token)

def get_device_statistics_by_mac(mac: str, fields: str = None):
    """Returns real-time statistics for a single cnWave device."""
    token = get_bearer_token()
    mac = wireless_mac_to_node_mac(mac)
    endpoint = f"devices/{mac}/statistics"
    query = []
    if fields:
        query.append(f"fields={fields}")
    if query:
        endpoint += "?" + "&".join(query)
    print(endpoint)
    return get_api(endpoint, token)

def get_network_counts(network_id: str) -> dict:
    """
    Live counts for a cnWave network (no cache):
      • nodes: total, online, offline, DN, CN
      • links: total, online, offline
    """
    print("get_network_counts")
    # ---------- NODES ----------
    dev_resp = get_devices(network=network_id)
    if not isinstance(dev_resp, dict) or "data" not in dev_resp:
        return {"status": "error", "message": "Unable to retrieve devices"}

    nodes = dev_resp["data"]
    node_counts = {
        "total": len(nodes),
        "online": 0,
        "offline": 0,
        "DN": 0,
        "CN": 0,
        # platform buckets
        "V5000": 0,
        "V3000": 0,
        "V2000": 0,
        "V1000": 0
    }

    for n in nodes:
        # online / offline
        if n.get("online", False):
            node_counts["online"] += 1
        else:
            node_counts["offline"] += 1

        # DN / CN
        t = n.get("mode", "").upper()
        if t in ("DN", "CN"):
            node_counts[t] += 1

        # --- platform ---
        hw = (n.get("hardware_version") or "").upper()
        for p in ("V5000", "V3000", "V2000", "V1000"):
            if p in hw:
                node_counts[p] += 1
                break    # stop at first match

    # ---------- LINKS ----------
    link_resp = get_links(network_id)
    if not isinstance(link_resp, dict) or "data" not in link_resp:
        return {"status": "error", "message": "Unable to retrieve links"}

    links = link_resp["data"]
    link_counts = {
        "total": len(links),
        "online": sum(1 for l in links if l.get("status", "").lower() == "online"),
        "offline": sum(1 for l in links if l.get("status", "").lower() != "online")
    }

    return {"nodes": node_counts, "links": link_counts}

def get_mac_for_node(network_id: str, node_name: str) -> dict:
    print("get_mac_for_node")
    """
    Returns the node MAC for a given device name.
    """
    resp = get_devices(network=network_id)
    if not isinstance(resp, dict) or "data" not in resp:
        return {"status": "error", "message": "Unable to fetch devices"}

    match = next((d for d in resp["data"] if d["name"] == node_name), None)
    if not match:
        return {"status": "error", "message": f"Device '{node_name}' not found"}
    return {"mac": match["mac"]}

def get_macs_for_link(network_id: str, link_name: str) -> dict:
    resp = get_links(network_id)
    if not (isinstance(resp, dict) and "data" in resp):
        return {"status": "error", "message": "Unable to fetch links"}

    link = next((l for l in resp["data"] if l["name"] == link_name), None)
    if not link:
        return {"status": "error", "message": f"Link '{link_name}' not found"}

    return {
        "a_node_mac": link.get("a_node_mac"),
        "a_node_name": link.get("a_node_name"),   # requires link object to include it
        "z_node_mac": link.get("z_node_mac"),
        "z_node_name": link.get("z_node_name")
    }