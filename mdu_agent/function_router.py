from memory import get as get_mem, set as set_mem

import json
from api_caller import load_cnmaestro_credentials, get_bearer_token, get_api, post_api
from local_functions import *
import logging

# Load cnMaestro credentials and get bearer token
client_id, client_secret, cnmaestro_url = load_cnmaestro_credentials()
token = get_bearer_token(client_id, client_secret, cnmaestro_url)

def route_function_call(function_name, arguments):
    """
    Routes GPT's requested function to either a local function or a cnMaestro API call.
    """
    logging.info(f"Routing: {function_name} with args: {arguments}")

    if isinstance(arguments, str):
        try:
            args = json.loads(arguments)
        except Exception as e:
            return f"Invalid JSON in arguments: {e}"
    else:
        args = arguments

    # === Local Functions ===
#    if function_name == "generate_nse_group_config":
#        return generate_nse_group_config(**args)
    
# === Memory-aware Local/Remote Logic ===
    if function_name == "create_network":
        result = post_api("networks", token, cnmaestro_url, args)
        set_mem("network_id", args["name"])
        return result

    elif function_name == "get_networks":
        return get_api("networks", token, cnmaestro_url)

    elif function_name == "create_site":
        set_mem("site_id", args["name"])
        return post_api(f"networks/{args['network_id']}/sites", token, cnmaestro_url, {
            "name": args["name"],
            "latitude": args["latitude"],
            "longitude": args["longitude"]
        })

    elif function_name == "get_sites":
        return get_api(f"networks/{args["network_id"]}/sites", token, cnmaestro_url)

    elif function_name == "create_nse_group":
        config = generate_nse_group_config(**args)
        return post_api("nse/nse_groups", token, cnmaestro_url, config)

    elif function_name == "onboard_device":
        return post_api("devices", token, cnmaestro_url, {
            "nse_group": args["nse_group"],
            "approved": True,
            "type": "nse",
            "msn": args["msn"]
        })

# === cnMaestro API Calls ===

    elif function_name == "get_networks":
        return get_api("networks", token, cnmaestro_url)

    elif function_name == "create_network":
        return post_api("networks", token, cnmaestro_url, args)

    elif function_name == "get_nse_groups":
        return get_api("nse/nse_groups", token, cnmaestro_url)

    elif function_name == "create_nse_group":
        return post_api("nse/nse_groups", token, cnmaestro_url, args)

    elif function_name == "get_sites":
        return get_api(f"networks/{args['network_id']}/sites", token, cnmaestro_url)

    elif function_name == "create_site":
        return post_api(f"networks/{args['network_id']}/sites", token, cnmaestro_url, {
            "name": args["name"],
            "latitude": args["latitude"],
            "longitude": args["longitude"]
        })

    elif function_name == "claim_nse_device":
        return post_api("devices", token, cnmaestro_url, {
            "nse_group": args["nse_group"],
            "approved": True,
            "type": "nse",
            "msn": args["msn"]
        })

    elif function_name == "create_resident_wlan_profile":
        return post_api("wifi_enterprise/wlans", token, cnmaestro_url, {
            "name": args["profile_name"],
            "description": "resident-mdu",
            "basic": {
                "passphrase": "12345678",
                "security": "wpa2-psk",
                "ssid": "cnPilot"
            },
            "epsk_settings": {
                "mode": "local",
                "enable_base_personal_ssid": True
            }
        })

    elif function_name == "create_community_wlan_profile":
        return post_api("wifi_enterprise/wlans", token, cnmaestro_url, {
            "name": args["profile_name"],
            "description": "community-mdu",
            "basic": {
                "passphrase": "12345678",
                "security": "wpa2-psk",
                "ssid": "cnPilot"
            },
            "epsk_settings": {
                "mode": "local",
                "enable_base_personal_ssid": False
            }
        })

    elif function_name == "create_ap_group":
        # Derive allowed VLAN string
        if args["resident_vlan_mode"] == "per_unit":
            start = args["resident_start_vlan_id"]
            end = start + args["resident_unit_count"]
            resident_vlan_str = f"{start}-{end - 1}"
        else:  # shared mode
            resident_vlan_str = str(args["resident_start_vlan_id"])

        # Combine resident VLAN(s) with community VLAN
        all_vlans = ["1", resident_vlan_str, str(args["community_vlan_id"])]
        allowed_vlan_str = ",".join(all_vlans)

        return post_api("wifi_enterprise/ap_groups", token, cnmaestro_url, {
            "name": args["ap_group_name"],
            "description": "MDU AP Group",
            "ethernet_ports": {
                "interface_eth1_mode": "trunk",
                "interface_eth1_allowed_vlan": allowed_vlan_str,
                "interface_eth2_mode": "trunk",
                "interface_eth2_allowed_vlan": allowed_vlan_str
            },
            "management": {
                "time_zone": "asia-kolkata"
            },
            "wlans": [
                args["residential_wlan_profile"],
                args["community_wlan_profile"]
            ]
        })

    else:
        return f"Unknown function: {function_name}"
