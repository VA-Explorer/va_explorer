import os

import pandas as pd
import requests

KOBO_HOST = os.environ.get("KOBO_HOST", "http://127.0.0.1:5003")
# Don't verify localhost (self-signed cert)
SSL_VERIFY = os.environ.get(
    "KOBO_SSL_VERIFY", not KOBO_HOST.startswith("http://localhost")
)

# TODO: Further support Kobo integration by creating an endpoint for VAs coming
#       in via REST Services feature (uploaded as soon as they're filled out)

def download_responses(token, asset_id):
    if not token or not asset_id:
        raise AttributeError(
            "Must specify either --token and --asset_id arguments or \
                KOBO_API_TOKEN and KOBO_ASSET_ID environment variables."
        )

    resource_uri = f"{KOBO_HOST}/api/v2/assets/{asset_id}/data.json"
    auth_header = {"Authorization": f"Token {token}"}
    response = requests.get(resource_uri, headers=auth_header, verify=SSL_VERIFY)
    response.raise_for_status()
    data = response.json()
    if "results" in data:
        parsed_results = list()
        for result in data["results"]:
            parsed_data = {}
            # Kobo column heading are in format group/subgroup/field, keep only field
            for key, value in result.items():
                new_key = key.split("/")[-1] if "/" in key else key
                parsed_data[new_key] = value
            parsed_results.append(parsed_data)
        return pd.DataFrame(parsed_results)
    else:
        return []
