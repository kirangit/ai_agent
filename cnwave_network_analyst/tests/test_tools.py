import os
import json
from dotenv import load_dotenv
from utils.logger_setup import init_logging

from tools.cnmaestro import (
    get_networks,
    get_network_counts,
    get_devices,
    get_sites,
    get_site,
    get_links,
    get_network_links_statistics,
    get_link_statistics_for_device,
    get_single_link_statistics_for_device,
    get_device_link_performance,
    get_device_overrides,
    get_network_device_statistics,
    get_device_statistics_by_mac
)

from tools.weather_api import get_weather
from tools.link_planner import get_link_planner_prediction

# Load environment and logging
load_dotenv()
init_logging()

# Define which tests to run
TESTS_TO_RUN = {
#    "get_networks",
    "get_network_counts"
#     "get_devices",
#     "get_sites",
#     "get_site",
#    "get_links",
#    "get_network_links_statistics",
#    "get_link_statistics_for_device",
#    "get_single_link_statistics_for_device",
#    "get_device_link_performance",
#    "get_device_overrides"
#    "get_weather",
#    "get_network_device_statistics",
#    "get_device_statistics_by_mac",
#    "get_link_planner_prediction"
}

# Sample network, site, MAC, link name (update if needed)
NETWORK_ID = "V2K-OnboardE2E-with-WifiAPunderCN"
SITE_NAME = "CN16-V2000-D135"
DEVICE_MAC = "00:04:56:8B:00:26"
LINK_NAME = "link-CN7-V1000-0026-POP-V2000-d14d"

def run_test(name, func):
    if name in TESTS_TO_RUN:
        print(f"\n=== {name} ===")
        try:
            result = func()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"❌ {name} failed: {e}")

# Run selected tests
run_test("get_networks", lambda: get_networks())

run_test("get_network_counts", lambda: get_network_counts(network_id="60 GHz cnWave E2E-CarPark"))

run_test("get_devices", lambda: get_devices(network=NETWORK_ID))

run_test("get_sites", lambda: get_sites(network_id=NETWORK_ID))

run_test("get_site", lambda: get_site(network_id=NETWORK_ID, site_id=SITE_NAME))

run_test("get_links", lambda: get_links(network_id=NETWORK_ID))

run_test("get_network_links_statistics", lambda: get_network_links_statistics(network_id=NETWORK_ID))

run_test("get_link_statistics_for_device", lambda: get_link_statistics_for_device(mac=DEVICE_MAC))

run_test("get_single_link_statistics_for_device", lambda: get_single_link_statistics_for_device(mac=DEVICE_MAC, link_name=LINK_NAME))

run_test("get_network_device_statistics", lambda: get_network_device_statistics(network_id=NETWORK_ID))

run_test("get_device_statistics_by_mac", lambda: get_device_statistics_by_mac(mac=DEVICE_MAC))

run_test("get_link_planner_prediction", lambda: get_link_planner_prediction(network_id="One Network", link_name="link-V5K-DN1-V5K-DN2"))

run_test("get_device_link_performance", lambda: get_device_link_performance(
    mac=DEVICE_MAC,
    link_name=LINK_NAME,
    start_time="2025-07-04T12:00:00Z",
    stop_time="2025-07-04T13:00:00Z"
))

run_test("get_device_overrides", lambda: get_device_overrides(network_id=NETWORK_ID))

run_test("get_weather", lambda: get_weather(
    latitude=12.97,
    longitude=77.59,
    start_date="2025-07-01",
    end_date="2025-07-05"
))
