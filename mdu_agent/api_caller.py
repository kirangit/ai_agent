import requests
import json
import os
import logging

# Load cnMaestro credentials from file
def load_cnmaestro_credentials():
    with open("credentials/cnmaestro.json") as f:
        creds = json.load(f)
    return creds["client_id"], creds["client_secret"], creds["cnmaestro_url"]

# Get bearer token using client credentials
def get_bearer_token(client_id, client_secret, cn_maestro_url):
    """Get bearer token using client credentials."""
    url = f"https://{cn_maestro_url}/api/v2/access/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Make authenticated GET request
def get_api(endpoint, token, cn_maestro_url):
    endpoint = endpoint.lstrip('/')  # Remove leading slash if present
    url = f"https://{cn_maestro_url}/api/v2/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "accept": "*/*"}
    response = requests.get(url, headers=headers)
    logging.info(f"GET {url} returned {response.status_code}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {"status": "error", "code": response.status_code, "details": response.text}
    
    logging.info(json.dumps(response.json(), indent=2))
    logging.info("\n\n\n")
    return response.json()

# Make authenticated POST request
def post_api(endpoint, token, cn_maestro_url, body, params=None):
    endpoint = endpoint.lstrip('/')  # Remove leading slash if present
    url = f"https://{cn_maestro_url}/api/v2/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "*/*",
        "Content-Type": "application/json"
    }
    logging.info(url)
    logging.info(json.dumps(body, indent=2))
    logging.info("\n\n\n")
    response = requests.post(url, headers=headers, data=json.dumps(body), params=params)
    logging.info(f"Response: {response.status_code} - {response.text}")

    if response.status_code == 422:
        error_msg = response.json().get("error", {}).get("message", "")
        if "Device is already claimed" in error_msg:
            return {"status": "ok", "message": "Device is already claimed. Continuing setup."}

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {"status": "error", "code": response.status_code, "details": response.text}
    
    if not response.ok:
        #print("Error:", response.status_code, response.text)
        logging.info(f"POST {url} returned {response.status_code}: {response.text}")

    return response.json()
