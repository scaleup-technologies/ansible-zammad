#!/usr/bin/python

# Copyright: (c) 2024, Melvin Ziemann <ziemann.melvin@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import json
import base64

__metaclass__ = type

DOCUMENTATION = r"""
---
module: zammad_ticket_idoit

short_description: Updates a Zammad ticket with i-doit object IDs.

description:
  - This module allows you to associate or update i-doit object IDs for a specific ticket in the Zammad ticketing system.
  - It uses the Zammad API to securely perform the operation. The module can either add or remove object IDs from a ticket based on the specified state.
  - The module supports both adding and removing i-doit object associations.

author:
  - Melvin Ziemann (@cloucs)  <ziemann.melvin@gmail.com>

options:
  zammad_access:
    description:
      - Connection details for accessing the Zammad API.
    type: dict
    required: true
    suboptions:
      zammad_url:
        description:
          - The base URL for the Zammad instance (e.g., https://zammad.example.com).
        type: str
        required: true
      api_user:
        description:
          - The Zammad API user with appropriate permissions.
        type: str
        required: true
      api_secret:
        description:
          - The API secret or password for the specified user. This value is hidden in logs.
        type: str
        required: true
  ticket_id:
    description:
      - The ID of the Zammad ticket to be updated.
    type: int
    required: true
  object_ids:
    description:
      - A list of i-doit object IDs to associate with the ticket.
    type: list
    elements: str
    required: true
  state:
    description:
      - The desired state of the operation.
      - If "present", the i-doit object IDs will be added to the ticket.
      - If "absent", the i-doit object IDs will be removed from the ticket.
    type: str
    required: true
    choices:
      - present
      - absent

notes:
  - Ensure the API user has sufficient permissions to update tickets.
  - The Zammad instance must be reachable from the Ansible control node.
  - The module will fail if the API request to Zammad fails or returns an error.
  - If "absent" state is specified, an empty list is sent to remove existing i-doit object IDs.
"""

EXAMPLES = r"""
# Example usage of zammad_ticket_idoit module
- name: Associate i-doit object IDs with a Zammad ticket
  zammad_ticket_idoit:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "admin@example.com"
      api_secret: "secure_password"
    ticket_id: 12345
    object_ids: ["56789", "98765"]
    state: present

- name: Remove i-doit object IDs from a Zammad ticket
  zammad_ticket_idoit:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "admin@example.com"
      api_secret: "secure_password"
    ticket_id: 12345
    object_ids: ["56789"]
    state: absent
"""

RETURN = r"""
changed:
  description: Indicates if the ticket was successfully updated.
  returned: always
  type: bool
  sample: true
ticket_id:
  description: The ID of the ticket that was updated.
  returned: always
  type: int
  sample: 12345
status_code:
  description: HTTP status code returned by the Zammad API.
  returned: always
  type: int
  sample: 200
message:
  description: Additional details or error message, if applicable.
  returned: always
  type: str
  sample: "Ticket successfully updated."
"""


def make_request(module, method, zammad_url, api_user, api_secret, data, ticket_id=None, endpoint=None):
    headers = {"Content-type": "application/json"}
    auth = f"{api_user}:{api_secret}"
    encoded_auth = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
    headers["Authorization"] = f"Basic {encoded_auth}"
    url = f"{zammad_url}/api/v1/tickets/{ticket_id}" if ticket_id else f"{zammad_url}/api/v1/{endpoint or 'tickets/'}"
    data_json = json.dumps(data) if data else None
    response, info = fetch_url(
        module,
        url,
        method=method,
        data=data_json,
        headers=headers
    )
    if info["status"] >= 400:
        module.fail_json(msg=f"API request failed: {info['msg']}", status_code=info["status"])
    try:
        result = json.load(response)
    except json.JSONDecodeError:
        module.fail_json(msg="Failed to parse JSON response")
    return result, info["status"]


def change_idoit_object(module, zammad_url, api_user, api_secret, ticket_id, object_ids):
    data = {
        "preferences": {
            "idoit": {
                "object_ids": object_ids
            }
        }
    }
    return make_request(module, "PUT", zammad_url, api_user, api_secret, data, ticket_id)


def run_module():
    module_args = dict(
        zammad_access=dict(
            type="dict",
            required=True,
            options=dict(
                zammad_url=dict(type="str", required=True),
                api_user=dict(type="str", required=True),
                api_secret=dict(type="str", required=True, no_log=True),
            )
        ),
        ticket_id=dict(type="int", required=True),
        object_ids=dict(type="list", elements="str", required=True),
        state=dict(type="str", required=True, choices=["present", "absent"]),
    )

    result = dict(changed=False, ticket_id=None, status_code=0, message="")
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    zammad_access = module.params["zammad_access"]
    zammad_url = zammad_access["zammad_url"]
    api_user = zammad_access["api_user"]
    api_secret = zammad_access["api_secret"]
    state = module.params["state"]
    object_ids = module.params["object_ids"] if state == "present" else ["0"]

    try:
        ticket_data, status_code = change_idoit_object(
            module,
            zammad_url,
            api_user,
            api_secret,
            module.params["ticket_id"],
            object_ids,
        )

        result.update(changed=True, ticket_id=module.params["ticket_id"], status_code=status_code, message="Success")
        module.exit_json(**result)

    except ValueError as e:
        module.fail_json(msg=str(e), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
