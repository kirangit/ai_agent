
import sys
import os
import unittest
import json

# Add parent directory to sys.path to import local_functions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from local_functions import generate_nse_group_config

class TestGenerateNSEGroupConfig(unittest.TestCase):

    def test_shared_vlan_mode(self):
        config = generate_nse_group_config(
            nse_group_name="TestGroupShared",
            resident_unit_count=3,
            resident_vlan_mode="shared",
            community_vlan_id=2,
            community_dhcp_subnet="192.168.100.0",
            resident_start_vlan_id=300,
            resident_start_subnet="192.168.110.0",
            default_dhcp_subnet="192.168.200.0"
        )
        print("\nShared VLAN Mode Config:")
        print(json.dumps(config, indent=2))
        self.assertEqual(config["name"], "TestGroupShared")
        self.assertEqual(len(config["lan_interfaces"]), 3)

    def test_per_unit_vlan_mode(self):
        config = generate_nse_group_config(
            nse_group_name="TestGroupPerUnit",
            resident_unit_count=2,
            resident_vlan_mode="per_unit",
            community_vlan_id=10,
            community_dhcp_subnet="192.168.50.0/24",
            resident_start_vlan_id=300,
            resident_start_subnet="192.168.60.0",
            default_dhcp_subnet="192.168.40.0"
        )
        print("\nPer Unit VLAN Mode Config:")
        print(json.dumps(config, indent=2))
        self.assertEqual(config["name"], "TestGroupPerUnit")
        self.assertEqual(len(config["lan_interfaces"]), 4)

if __name__ == '__main__':
    unittest.main()
