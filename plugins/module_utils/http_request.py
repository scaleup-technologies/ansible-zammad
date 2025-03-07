# Copyright: (c) 2024, Melvin Ziemann <ziemann.melvin@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.urls import fetch_url
import json
import base64


__metaclass__ = type


def make_request(module, method, zammad_access, data, ticket_id=None, endpoint=None, expand=False):
    zammad_url = zammad_access["zammad_url"]
    api_user = zammad_access.get("api_user")
    api_secret = zammad_access.get("api_secret")
    api_token = zammad_access.get("api_token")
    headers = {"Content-type": "application/json"}

    if api_token:
        headers["Authorization"] = f"Token {api_token}"
    else:
        auth = f"{api_user}:{api_secret}"
        encoded_auth = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Basic {encoded_auth}"

    url = (
        f"{zammad_url}/api/v1/tickets/{ticket_id}"
        if ticket_id
        else f"{zammad_url}/api/v1/{endpoint or 'tickets/'}"
    )
    if expand:
        url = f"{url}?expand=true"
    data_json = json.dumps(data) if data else None
    response, info = fetch_url(module, url, method=method, data=data_json, headers=headers)
    if info["status"] >= 400:
        module.fail_json(msg=f"API request failed: {info['msg']}", status_code=info["status"])
    try:
        result = json.load(response)
    except json.JSONDecodeError:
        module.fail_json(msg="Failed to parse JSON response")
    return result, info["status"]


def validate_zammad_access(module, zammad_access):
    if not any(zammad_access.get(param) for param in ["api_token", "api_user", "api_secret"]):
        module.fail_json(
            msg="Missing required zammad_access parameters: api_token or api_user and api_secret."
        )

    if not zammad_access.get("api_token"):
        for param in ["api_user", "api_secret"]:
            if not (zammad_access.get(param)):
                module.fail_json(msg=f"Missing required zammad_access parameters: {param}.")
