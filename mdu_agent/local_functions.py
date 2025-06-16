
import ipaddress
import requests
import json
import ipaddress

# Accessible by function_router
CNMAESTRO_URL = None  # Will be injected or set from main.py if needed

def is_valid_name(name):
    """Check if the given name is valid based on allowed characters: alphanumeric, hyphen, and underscore."""
    return all(c.isalnum() or c in ['-', '_'] for c in name)

def generate_vlan_interface(vlan_id, subnet_base, name=None):
    """
    Helper function to generate a single VLAN interface configuration.
    
    Args:
        vlan_id (int): VLAN ID.
        subnet_base (str): Subnet in CIDR format (e.g., '192.168.1.0/24').
        name (str): Optional name for the VLAN interface.

    Returns:
        dict: VLAN interface configuration.
    """
    base_net = ipaddress.ip_network(subnet_base)
    hosts = list(base_net.hosts())

    return {
        "name": name or f"VLAN-{vlan_id}",
        "dhcp": "dhcp_pool",
        "ip_addr": str(hosts[0]),
        "ip_mode": "static",
        "vlan_id": vlan_id,
        "dhcp_relay": {
            "enable": False
        },
        "subnet_mask": "255.255.255.0",
        "dhcp_pool_config": {
            "dhcp_pool_enable": True,
            "dhcp_pool_domain_name": "cambium",
            "dhcp_pool_start_address": str(hosts[50]),
            "dhcp_pool_end_address": str(hosts[150]),
            "dhcp_pool_primary_dns_server": str(hosts[0])
        },
        "rate_limit_rules": {
            "rate_limit": "disable"
        },
        "management_access": "enable"
    }

def normalize_subnet(subnet_str):
    """
    Ensure the subnet is in valid CIDR format.
    If no prefix is specified, assume /24.
    """
    if '/' not in subnet_str:
        subnet_str += '/24'
    return ipaddress.ip_network(subnet_str, strict=False)

def generate_nse_group_config(
    nse_group,
    resident_unit_count,
    resident_vlan_mode,
    community_vlan_id,
    community_dhcp_subnet,
    resident_start_vlan_id,
    resident_start_subnet,
    default_dhcp_subnet
):
    """
    Generate the full NSE group configuration JSON for cnMaestro API.
    
    Args:
        group_name (str): Name of the NSE group.
        resident_unit_count (int): Number of residential units.
        resident_vlan_mode (str): 'shared' or 'per_unit'.
        community_vlan_id (int): VLAN ID for the community SSID.
        community_dhcp_subnet (str): Subnet for the community VLAN.
        resident_start_vlan_id (int): Starting VLAN ID for residential units.
        resident_start_subnet (str): Starting subnet for residential units.
        default_dhcp_subnet (str): Subnet for the default VLAN (VLAN 1).

    Returns:
        dict: NSE group JSON config ready to send via API.
    """
    # Load base configuration
    with open("base_configs/nse_base_config.json") as f:
        nse_config = json.load(f)

    # Assign group name
    nse_config["name"] = nse_group

    community_dhcp_subnet = normalize_subnet(community_dhcp_subnet)
    resident_start_subnet = normalize_subnet(resident_start_subnet)
    default_dhcp_subnet = normalize_subnet(default_dhcp_subnet)

    # Reset or initialize lan_interfaces
    nse_config["network"]["lan_interfaces"] = []

    # Add default VLAN (VLAN 1)
    nse_config["network"]["lan_interfaces"].append(
        generate_vlan_interface(1, default_dhcp_subnet, name="VLAN-1")
    )

    # Add community VLAN
    nse_config["network"]["lan_interfaces"].append(
        generate_vlan_interface(community_vlan_id, community_dhcp_subnet, name=f"VLAN-{community_vlan_id}")
    )

    # Add resident VLANs
    if resident_vlan_mode == "shared":
        # One shared VLAN for all residential units
        nse_config["network"]["lan_interfaces"].append(
            generate_vlan_interface(resident_start_vlan_id, resident_start_subnet, name=f"VLAN-{resident_start_vlan_id}")
        )
    elif resident_vlan_mode == "per_unit":
        base = ipaddress.ip_network(resident_start_subnet, strict=False)
        if base.prefixlen != 24:
            raise ValueError("Only /24 subnets supported for per-unit VLAN allocation")

        start_ip_int = int(base.network_address)
        for i in range(resident_unit_count):
            vlan_id = resident_start_vlan_id + i

            # Each /24 subnet is offset by 256 IPs
            subnet_ip_int = start_ip_int + (i << 8)  # i * 256
            subnet = ipaddress.ip_network((subnet_ip_int, 24))

            nse_config["network"]["lan_interfaces"].append(
                generate_vlan_interface(vlan_id, str(subnet), name=f"VLAN-{vlan_id}")
            )
    else:
        raise ValueError("Invalid resident_vlan_mode. Must be 'shared' or 'per_unit'.")

    return nse_config
