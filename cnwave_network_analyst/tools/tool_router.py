
import json
import logging

from .cnmaestro import get_sites
from .cnmaestro import get_devices
from .cnmaestro import get_links

def route_tool_call(tool_call):
    import json
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    logger = logging.getLogger("cnmaestro")
    logger.info(f"Tool call: {name} with args {args}")

    match name:
        case "get_networks":
            from .cnmaestro import get_networks
            return get_networks(**args)

        case "get_network_counts":
            from .cnmaestro import get_network_counts
            return get_network_counts(**args)

        case "get_devices":
            return get_devices(**args)

        case "get_sites":
            return get_sites(**args)

        case "get_site":
            from .cnmaestro import get_site
            return get_site(**args)

        case "get_links":
            return get_links(**args)

        case "get_network_links_statistics":
            from .cnmaestro import get_network_links_statistics
            return get_network_links_statistics(**args)

        case "get_link_statistics_for_device":
            from .cnmaestro import get_link_statistics_for_device
            return get_link_statistics_for_device(**args)

        case "get_single_link_statistics_for_device":
            from .cnmaestro import get_single_link_statistics_for_device
            try:
                return get_single_link_statistics_for_device(**args)
            except TypeError as e:
                return {"status": "error", "message": f"Missing required parameters: {str(e)}"}

        case "get_device_link_performance":
            from .cnmaestro import get_device_link_performance
            return get_device_link_performance(**args)

        case "get_weather":
            from .weather_api import get_weather
            return get_weather(**args)

        case "get_current_utc_time":
            from .weather_api import get_current_utc_time
            return get_current_utc_time(**args)
        
        case "get_device_overrides":
            from .cnmaestro import get_device_overrides
            return get_device_overrides(**args)

        case "get_controller_info":
            from .cnmaestro import get_controller_info
            return get_controller_info(**args)

        case "get_network_device_statistics":
            from .cnmaestro import get_network_device_statistics
            return get_network_device_statistics(**args)

        case "get_device_statistics_by_mac":
            from .cnmaestro import get_device_statistics_by_mac
            return get_device_statistics_by_mac(**args)

        case "get_link_planner_prediction":
            from .link_planner import get_link_planner_prediction
            return get_link_planner_prediction(**args)

        case "compute_rain_attenuation":
            from .weather_api import compute_rain_attenuation
            return compute_rain_attenuation(**args)

        case "get_mac_for_node":
            from .cnmaestro import get_mac_for_node
            return get_mac_for_node(**args)

        case "get_macs_for_link":
            from .cnmaestro import get_macs_for_link
            return get_macs_for_link(**args)

        case "create_visual_map":
            from utils.map import handle_create_visual_map
            return handle_create_visual_map(**args)

        case _: return {'error': f'Unknown tool: {name}'}