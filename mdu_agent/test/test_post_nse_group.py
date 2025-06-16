
import json
from local_functions import generate_nse_group_config
from api_caller import post_api, get_bearer_token

# Input parameters for the NSE Group creation
params = {
    "nse_group_name": "TestGroup03",
    "resident_unit_count": 3,
    "resident_vlan_mode": "per_unit",  # or "shared"
    "community_vlan_id": 2,
    "community_dhcp_subnet": "192.168.102.0",
    "resident_start_vlan_id": 300,
    "resident_start_subnet": "192.168.103.0",
    "default_dhcp_subnet": "192.168.101.0"
}

# Generate the JSON config body
nse_group_config = generate_nse_group_config(**params)

# Load credentials
with open("credentials/cnmaestro.json") as f:
    creds = json.load(f)

token = get_bearer_token(
    creds["client_id"],
    creds["client_secret"],
    creds["cnmaestro_url"]
)

# POST to /nse/nse_groups
response = post_api(
    endpoint="nse/nse_groups",
    token=token,
    cn_maestro_url=creds["cnmaestro_url"],
    body=nse_group_config
)

# Print response
print(response)
