import folium
from math import sin, cos, radians
from typing import List, Dict
import os

SECTOR_RADIUS = 0.00005
SECTOR_COLORS = ['blue', '#1E90FF', 'green', 'yellow']

def draw_sector(map_obj, center, radius, azimuth, coverage_angle, color, popup=None):
    num_points = 30
    start_angle = azimuth - coverage_angle / 2
    end_angle = azimuth + coverage_angle / 2
    points = [center]
    for i in range(num_points + 1):
        angle = radians(start_angle + (end_angle - start_angle) * i / num_points)
        dx = radius * cos(angle)
        dy = radius * sin(angle)
        points.append([center[0] + dy, center[1] + dx])
    points.append(center)
    folium.Polygon(points, color=color, fill=True, fill_color=color, popup=popup).add_to(map_obj)

def get_hw_model(hardware_version: str) -> str:
    version = hardware_version.upper()
    if "V5000" in version:
        return "V5000"
    elif "V3000" in version:
        return "V3000"
    elif "V1000" in version:
        return "V1000"
    elif "V2000" in version:
        return "V2000"
    return "OTHER"

def create_visual_map_from_data(sites: List[Dict], nodes: List[Dict], links: List[Dict], output_file: str) -> str:
    m = folium.Map(
        location=[sites[0]["location"]["coordinates"][1], sites[0]["location"]["coordinates"][0]],
        zoom_start=18, max_zoom=30
    )

    mac_node_map = {n["mac"].upper(): n for n in nodes if "mac" in n}

    for node in nodes:
        site = next((s for s in sites if s["name"] == node.get("site")), None)
        if not site:
            continue
        lat = site["location"]["coordinates"][1]
        lon = site["location"]["coordinates"][0]
        hw_model = get_hw_model(node.get("hardware_version", ""))
        azimuth = node.get("azimuth", 0)

        if hw_model == "V5000":
            for idx in range(2):
                sector_az = (azimuth + 180 + (idx * 140)) % 360
                color = SECTOR_COLORS[idx % len(SECTOR_COLORS)]
                draw_sector(m, [lat, lon], SECTOR_RADIUS, sector_az, 140, color, popup=node["name"])
        elif hw_model in ("V1000", "V3000", "V2000"):
            color = "#4B0082" if hw_model == "V1000" else "#FF6600"
            draw_sector(m, [lat, lon], SECTOR_RADIUS, azimuth, 90, color, popup=node["name"])
        else:
            folium.Marker([lat, lon], popup=node["name"], tooltip=node["name"]).add_to(m)

    name_node_map = {node["name"]: node for node in nodes}

    for link in links:
        a_node = name_node_map.get(link.get("a_node_name"))
        z_node = name_node_map.get(link.get("z_node_name"))
        if not a_node or not z_node:
            continue

        a_site = next((s for s in sites if s["name"] == a_node.get("site")), None)
        z_site = next((s for s in sites if s["name"] == z_node.get("site")), None)
        if not a_site or not z_site:
            continue

        a_lat, a_lon = a_site["location"]["coordinates"][1], a_site["location"]["coordinates"][0]
        z_lat, z_lon = z_site["location"]["coordinates"][1], z_site["location"]["coordinates"][0]

        color = "green" if link.get("status", "").lower() == "online" else "red"

        folium.PolyLine([[a_lat, a_lon], [z_lat, z_lon]],
                        color=color,
                        popup=folium.Popup(link["name"], parse_html=True),
                        tooltip=folium.Tooltip(link["name"])).add_to(m)
        m.save(output_file)
    return output_file

def create_visual_map(network_id: str, sites: List[Dict], nodes: List[Dict], links: List[Dict]) -> Dict[str, str]:
    filename = f"visual_map_{network_id}.html"
    local_path = f"/var/www/html/shared/ai/cnwave_agent/maps/{filename}"
    web_url = f"http://10.110.206.11/shared/ai/cnwave_agent/maps/{filename}"

    # Generate the map file
    output_path = create_visual_map_from_data(sites, nodes, links, local_path)
    abs_path = os.path.abspath(output_path)

    return {
        "map_name": filename,
        "file_path": abs_path,
        "file_url": web_url,
        "message": f"✅ Visual map for '{network_id}' saved at: [📍 View Map]({web_url})"
    }

def handle_create_visual_map(network_id: str) -> dict:
    """
    Wrapper for the create_visual_map tool call.
    Fetches sites, devices, and links, then renders map.
    Returns a dict with map file path and URL.
    """
    from tools.cnmaestro import get_sites, get_devices, get_links

    try:
        sites_resp = get_sites(network_id=network_id)
        nodes_resp = get_devices(network=network_id)
        links_resp = get_links(network_id=network_id)

        if not all(isinstance(resp, dict) and "data" in resp for resp in [sites_resp, nodes_resp, links_resp]):
            raise ValueError("One or more API responses were malformed or incomplete.")

        return create_visual_map(
            network_id,
            sites=sites_resp["data"],
            nodes=nodes_resp["data"],
            links=links_resp["data"]
        )

    except Exception as e:
        return {
            "error": f"❌ Unable to generate map for '{network_id}'. Reason: {str(e)}"
        }

