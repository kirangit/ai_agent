import json
from function_router import route_function_call

result = route_function_call("get_networks", json.dumps({}))
print("Available Networks:", result)
'''
create_network_args = {
    "name": "test_network_01"
}

result = route_function_call("create_network", json.dumps(create_network_args))
print("Created Network:", result)

create_site_args = {
    "network_id": "test_network_01",
    "name": "test_site_01",
    "latitude": 12.97,
    "longitude": 77.59
}

result = route_function_call("create_site", json.dumps(create_site_args))
print("Created Site:", result)

get_sites_args = {
    "network_id": "test_network_01"  # this is the name of the network, not ID
}

result = route_function_call("get_sites", json.dumps(get_sites_args))
print("Sites under Network:", result)
'''

