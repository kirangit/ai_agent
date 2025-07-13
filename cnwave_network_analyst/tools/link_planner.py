
import requests
import json
import pprint
from tools.cnmaestro import get_links, get_devices, wireless_mac_to_node_mac

LINK_PLANNER_URL = "https://apitest.lp.cambiumnetworks.com/cnmaestro/v1/sm_performance"
LINK_PLANNER_SECRET = "366201e83fb14e6d6827fdc2fe7276b2"

ANTENNAS = [
    {"product": "V3000", "variant": "high_gain", "id": "2a8d8829-e11d-417b-823f-1600833c3c5f", "beamwidth": 4.0, "gain": 44.5},
    {"product": "V3000", "variant": "mid_gain", "id": "723193c3-73f9-4a78-9b00-09a47c3b1cf5", "beamwidth": 4.0, "gain": 42.2},
    {"product": "V2000", "variant": "default", "id": "8bbd9c95-732d-49dc-9a27-c44827308f96", "beamwidth": 20.0, "gain": 34.5},
    {"product": "V5000", "variant": "default", "id": "d289296b-f730-41a4-b2c0-0410fb26d76d", "beamwidth": 280.0, "gain": 22.5},
    {"product": "V1000", "variant": "default", "id": "6b5f7168-8d8c-4862-91a7-ac86787451f8", "beamwidth": 90.0, "gain": 22.5}
]

def get_antenna(product: str, variant: str = "default") -> dict:
    return next((a for a in ANTENNAS if a["product"].upper() == product.upper() and a["variant"] == variant), None)

def extract_mcs_index(mcs_string: str) -> str:
    """
    Extracts the MCS index (e.g., '12') from a string like 'MCS12 (16QAM 0.75 Sngl)'.
    Falls back to full string if parsing fails.
    """
    try:
        return int(mcs_string.split()[0].replace("MCS", ""))
    except Exception:
        return mcs_string

def run_link_planner_prediction(request_body: dict) -> dict:
    try:
        url = f"{LINK_PLANNER_URL}?secret={LINK_PLANNER_SECRET}"
        payload = json.dumps(request_body)
        headers = {"Content-Type": "application/json"}
        #pprint.pprint(request_body)
        response = requests.post(url, headers=headers, data=payload)
        #print(f"Status: {response.status_code}")
        #print(json.dumps(response.json(), indent=2))
        #response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": str(e),
            "http_status": getattr(e.response, 'status_code', None),
            "details": getattr(e.response, 'text', None)
        }


def get_link_planner_prediction(network_id: str, link_name: str) -> dict:
    links_resp = get_links(network_id=network_id)
    devices_resp = get_devices(network=network_id)

    if not isinstance(links_resp, dict) or "data" not in links_resp:
        return {
            "status": "error",
            "message": "Unable to fetch link list from tools.cnmaestro. The API may be temporarily busy or unreachable."
        }
    if not isinstance(devices_resp, dict) or "data" not in devices_resp:
        return {
            "status": "error",
            "message": "Unable to fetch device list from tools.cnmaestro. The API may be temporarily busy or unreachable."
        }

    links = links_resp["data"]
    devices = devices_resp["data"]
    link = next((l for l in links if l["name"] == link_name), None)
    if not link:
        return {"status": "error", "message": f"Link '{link_name}' not found in network '{network_id}'."}

    a_mac, z_mac = link["a_node_mac"].lower(), link["z_node_mac"].lower()
    a_mac = wireless_mac_to_node_mac(a_mac)
    z_mac = wireless_mac_to_node_mac(z_mac)
    a_name, z_name = link["a_node_name"], link["z_node_name"]

    a_dev = next((d for d in devices if d["mac"].lower() == a_mac), None)
    z_dev = next((d for d in devices if d["mac"].lower() == z_mac), None)
    if not a_dev or not z_dev:
        return {"status": "error", "message": "One or both devices not found."}

    ap_lat, ap_lon = z_dev["location"]["coordinates"][1], z_dev["location"]["coordinates"][0]
    sm_lat, sm_lon = a_dev["location"]["coordinates"][1], a_dev["location"]["coordinates"][0]

    ap_hw = z_dev["hardware_version"]
    sm_hw = a_dev["hardware_version"]

    ap_antenna = get_antenna(ap_hw, variant="high_gain" if ap_hw == "V3000" else "default")
    sm_antenna = get_antenna(sm_hw, variant="high_gain" if sm_hw == "V3000" else "default")

    request_body = {
        "sm": {
            "name": a_name,
            "latitude": sm_lat,
            "longitude": sm_lon,
            "is_network_site": False,
            "maximum_height": 100,
            "sm": {
                "name": "",
                "description": "",
                "mac": a_dev["mac"],
                "ap_mac": z_dev["mac"],
                "equipment": {
                    "band": "60 GHz",
                    "product": sm_hw
                },
                "antenna": {
                    "id": sm_antenna.get("id"),
                    "height": 100
                }
            }
        },
        "ap": {
            "name": z_name,
            "latitude": ap_lat,
            "longitude": ap_lon,
            "maximum_height": 100,
            "is_network_site": True,
            "ap_list": [
                {
                    "mac": z_dev["mac"],
                    "radios": [
                        {
                            "equipment": {
                                "band": "60 GHz",
                                "product": ap_hw,
                                "range_units": "kilometers",
                                "sm_range": 1
                            },
                            "antennas": [
                                {
                                    "id": ap_antenna.get("id"),
                                    "azimuth": z_dev.get("azimuth", 0),
                                    "height": 100,
                                    "beamwidth": ap_antenna.get("beamwidth")
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    planner_response = run_link_planner_prediction(request_body)
    if "data" not in planner_response:
        return planner_response

    pred = planner_response["data"]
    return {
        "name": link_name,
        "a_node_name": a_name,
        "z_node_name": z_name,
        "data": [
            {
                "name": link_name,
                "network": network_id,
                "a_node_name": a_name,
                "z_node_name": z_name,
                "direction": f"{z_name} to {a_name}",
                "predicted_rssi": pred["sm_receive_level_dbm"],
                "predicted_rx_mcs": extract_mcs_index(pred["sm_rx_max_usable_mode"]),
                "predicted_fade_margin": pred["link_fade_margin_max_usable_mode_sm"]
            },
            {
                "name": link_name,
                "network": network_id,
                "a_node_name": a_name,
                "z_node_name": z_name,
                "direction": f"{a_name} to {z_name}",
                "predicted_rssi": pred["ap_receive_level_dbm"],
                "predicted_rx_mcs": extract_mcs_index(pred["ap_rx_max_usable_mode"]),
                "predicted_fade_margin": pred["link_fade_margin_max_usable_mode_ap"]
            }
        ]
    }
