
# memory.py

# Simple in-memory state tracker for the CLI chatbot session

memory = {
    "network_id": None,
    "site_id": None,
    "nse_group_name": None,
    "resident_vlan_range": None,
    "resident_vlan_mode": None,
    "wifi_profile_community": None,
    "wifi_profile_residential": None,
    "ap_group_name": None
}

def set(key, value):
    """Set a value in the session memory."""
    memory[key] = value

def get(key):
    """Get a value from session memory."""
    return memory.get(key)

def reset():
    """Clear all memory entries."""
    for key in memory:
        memory[key] = None

def dump():
    """Return the full memory dictionary."""
    return memory.copy()
