from urllib.parse import urlparse

import environ
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

env = environ.Env()
USE_GATEWAY = env.bool("USE_GATEWAY", default=False)
KOBO_HOST = env("KOBO_HOST", default="http://127.0.0.1:6001")
# Don't verify localhost (self-signed cert)
SSL_VERIFY = env.bool("KOBO_SSL_VERIFY", default=("localhost" in KOBO_HOST))

# TODO: Further support Kobo integration by creating an endpoint for VAs coming
#       in via REST Services feature (uploaded as soon as they're filled out)


# Prefer usage of token over username password, but provide this util method
# just in case
def get_kobo_api_token(username, password):
    basic = HTTPBasicAuth(username, password)

    # Support advanced networking setups by allowing explicit use of external
    # docker network gateways
    if USE_GATEWAY:
        DOCKER_GATEWAY = env("DOCKER_GATEWAY", default="https://172.18.0.1")
        url = f"{DOCKER_GATEWAY}/token/?format=json"
        headers = {"Host": KOBO_HOST}
        response = requests.get(url, headers=headers, auth=basic, verify=SSL_VERIFY)
    else:
        url = f"{KOBO_HOST}/token/?format=json"
        response = requests.get(url, auth=basic, verify=SSL_VERIFY)

    response.raise_for_status()
    data = response.json()

    token = data["token"]
    return {"Authorization": f"Token {token}"}


def download_responses(token, asset_id, batch_size=5000, next_page=None):
    if not token or not asset_id:
        raise AttributeError(
            "Must specify either --token and --asset_id arguments or "
            "KOBO_API_TOKEN and KOBO_ASSET_ID environment variables."
        )

    # Support advanced networking setups by allowing explicit use of external
    # docker network gateways
    params = "?format=json" + f"&limit={batch_size}" + "&start=0&sort={%22_id%22:-1}"
    if USE_GATEWAY:
        DOCKER_GATEWAY = env("DOCKER_GATEWAY", default="https://172.18.0.1")
        if next_page is None:
            resource_uri = f"{DOCKER_GATEWAY}/api/v2/assets/{asset_id}/data/{params}"
        else:
            next_info = urlparse(next_page)
            resource_uri = f"{DOCKER_GATEWAY}{next_info.path}?{next_info.query}"
        headers = {"Authorization": f"Token {token}", "Host": KOBO_HOST}
    else:
        resource_uri = (
            f"{KOBO_HOST}/api/v2/assets/{asset_id}/data/{params}"
            if next_page is None
            else next_page
        )
        headers = {"Authorization": f"Token {token}"}

    response = requests.get(resource_uri, headers=headers, verify=SSL_VERIFY)
    response.raise_for_status()
    data = response.json()
    if "results" in data:
        parsed_results = []
        next_results = data["next"]
        for result in data["results"]:
            parsed_data = {}
            # Kobo column heading are in format group/subgroup/field, keep only field
            for key, value in result.items():
                new_key = key.split("/")[-1] if "/" in key else key
                parsed_data[new_key] = value
            parsed_results.append(parsed_data)
        return pd.DataFrame(parsed_results), next_results
    else:
        return pd.DataFrame([]), None
