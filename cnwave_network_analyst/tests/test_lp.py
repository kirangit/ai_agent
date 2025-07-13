
import requests
import json

url = "https://apitest.lp.cambiumnetworks.com/cnmaestro/v1/sm_performance?secret=366201e83fb14e6d6827fdc2fe7276b2"
headers = {
    "Content-Type": "application/json"
}

request_body = {
  "sm": {
    "name": "CN7-V1000-0026",
    "latitude": 12.937185000755278,
    "longitude": 77.6991796227167,
    "is_network_site": False,
    "maximum_height": 100,
    "sm": {
      "name": "",
      "description": "",
      "mac": "00:04:56:8B:00:26",
      "ap_mac": "30:CB:C7:73:D1:4D",
      "equipment": {
        "band": "60 GHz",
        "product": "V1000"
      },
      "antenna": {
        "id": "6b5f7168-8d8c-4862-91a7-ac86787451f8",
        "height": 100,
        "beamwidth": 90.0
      }
    }
  },
  "ap": {
    "name": "POP-V2000-d14d",
    "latitude": 12.937669190612096,
    "longitude": 77.70109995955912,
    "maximum_height": 100,
    "is_network_site": True,
    "ap_list": [
      {
        "mac": "30:CB:C7:73:D1:4D",
        "radios": [
          {
            "equipment": {
              "band": "60 GHz",
              "product": "V2000",
              "range_units": "kilometers",
              "sm_range": 1
            },
            "antennas": [
              {
                "id": "8bbd9c95-732d-49dc-9a27-c44827308f96",
                "azimuth": 0,
                "height": 100,
                "beamwidth": 20.0
              }
            ]
          }
        ]
      }
    ]
  }
}

response = requests.post(url, headers=headers, data=json.dumps(request_body))
print("Status:", response.status_code)
try:
    print("Response:", json.dumps(response.json(), indent=2))
except Exception as e:
    print("Error decoding JSON:", e)
    print("Raw Response:", response.text)
