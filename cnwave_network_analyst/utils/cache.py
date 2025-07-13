from typing import Dict, List, Optional
from collections import defaultdict
from tools.cnmaestro import get_devices, get_links

_selected_network_id: Optional[str] = None
_network_nodes: Dict[str, Dict[str, str]] = defaultdict(dict)   # network_id -> node_name -> mac
_network_links: Dict[str, Dict[str, str]] = defaultdict(dict)   # network_id -> link_name -> a_node_mac

def set_selected_network(network_id: str):
    global _selected_network_id
    _selected_network_id = network_id

def get_selected_network() -> Optional[str]:
    return _selected_network_id

def cache_nodes_for_network(network_id: str):
    """
    Fetches devices from tools.cnmaestro and stores node name to MAC mapping per network.
    Uses 'fields' to minimize response size.
    """
    response = get_devices(network=network_id, type="cnwave60", fields="name,mac")
    if not response or "data" not in response:
        return

    _network_nodes[network_id].clear()
    for node in response["data"]:
        name = node.get("name")
        mac = node.get("mac")
        if name and mac:
            _network_nodes[network_id][name] = mac

# Assume: _network_links is a dict[str, dict[str, dict[str, str | None]]]

def cache_links_for_network(network_id: str) -> None:
    """
    Fetch links from tools.cnmaestro and cache them locally.

    After the call, `_network_links[network_id]` looks like:
        {
            "link-A-B": {"a_node_mac": "00:04:56:AA:BB:CC",
                         "z_node_mac": "00:04:56:DD:EE:FF"},
            ...
        }

    Notes
    -----
    • Uses the `fields` query to minimise payload.
    • Gracefully returns if the API response is missing/invalid.
    """
    resp = get_links(network_id=network_id,
                     fields="name,a_node_mac,z_node_mac")   # <─ grab both MACs
    if not (isinstance(resp, dict) and "data" in resp):
        return

    # Ensure network entry exists, then wipe old cache
    _network_links.setdefault(network_id, {}).clear()

    for link in resp["data"]:
        name = link.get("name")
        if not name:
            continue

        _network_links[network_id][name] = {
            "a_node_mac": link.get("a_node_mac"),
            "z_node_mac": link.get("z_node_mac")
        }


def get_node_mac_from_name(network_id: str, node_name: str) -> Optional[str]:
    mac = _network_nodes.get(network_id, {}).get(node_name)
    if mac:
        return mac

    # Auto-fetch and try again
    cache_nodes_for_network(network_id)
    return _network_nodes.get(network_id, {}).get(node_name)

from typing import Optional, Tuple, Dict

# ------------------------------------------------------------------
# expected structure after caching:
# _network_links = {
#     "net-123": {
#         "link-A-B": {"a_node_mac": "00:04:56:AA:BB:CC",
#                      "z_node_mac": "00:04:56:DD:EE:FF"},
#         ...
#     }
# }
# ------------------------------------------------------------------

def get_link_macs(network_id: str, link_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (a_node_mac, z_node_mac) for the specified link.

    Notes
    -----
    • If the link isn’t cached yet, we transparently call `cache_links_for_network`
      to hydrate `_network_links`, then retry.
    • Returns (None, None) if the link still cannot be found.
    """
    def _lookup() -> Optional[Dict[str, str]]:
        return _network_links.get(network_id, {}).get(link_name)

    entry = _lookup()
    if entry:
        return entry.get("a_node_mac"), entry.get("z_node_mac")

    # Auto-fetch → populate cache → second attempt
    cache_links_for_network(network_id)
    entry = _lookup()
    if entry:
        return entry.get("a_node_mac"), entry.get("z_node_mac")

    # Not found
    return None, None


def reset_cache():
    _network_nodes.clear()
    _network_links.clear()
