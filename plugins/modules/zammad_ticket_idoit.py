#!/usr/bin/python

# Copyright: (c) 2024, Melvin Ziemann <ziemann.melvin@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type


DOCUMENTATION = r"""
---
module: zammad_ticket_idoit

short_description: Updates a Zammad ticket with i-doit object IDs.

description:
  - This module allows you to associate or update an i-doit object ID for a specific ticket in the Zammad ticketing system.
  - It uses the Zammad API to perform the operation securely.

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
  object_id:
    description:
      - The i-doit object ID to associate with the ticket.
    type: str
    required: true

notes:
  - Ensure the API user has sufficient permissions to update tickets.
  - The Zammad instance must be reachable from the Ansible control node.
"""

EXAMPLES = r"""
# Example usage of zammad_ticket_idoit module
- name: Associate an i-doit object with a Zammad ticket
  zammad_change_idoit_object:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "admin@example.com"
      api_secret: "secure_password"
    ticket_id: 12345
    object_id: "56789"
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible_collections.ansible_zammad.plugins.module_utils.requests import make_request
import json
import base64


def change_idoit_object(module, zammad_url, api_user, api_secret, ticket_id, object_id):
    data = {
        "preferences": {
            "idoit": {
                "object_ids": [object_id]
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
                api_secret=dict(type="str", required=True, no_log=True)
            )
        ),
        ticket_id=dict(type="int", required=True),
        object_id=dict(type="str", required=True)
    )

    module_args = {**module_args}

    result = dict(changed=False, ticket_id=None, status_code=0, message="")
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    zammad_access = module.params["zammad_access"]
    zammad_url = zammad_access["zammad_url"]
    api_user = zammad_access["api_user"]
    api_secret = zammad_access["api_secret"]

    try:
        ticket_data, status_code = change_idoit_object(
            module,
            zammad_url,
            api_user,
            api_secret,
            module.params["ticket_id"],
            module.params["object_id"]
        )

        module.exit_json(**result)

    except ValueError as e:
        module.fail_json(msg=str(e), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
