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
  - This module allows you to associate or update i-doit object IDs for a specific ticket in the Zammad ticketing system.
  - It uses the Zammad API to securely perform the operation. The module can either add or remove object IDs from a ticket based on the specified state.
  - The module supports both adding and removing i-doit object associations.

author:
  - Melvin Ziemann (@cloucs)  <ziemann.melvin@gmail.com>

options:
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
extends_documentation_fragment:
  - scaleuptechnologies.zammad.zammad_access
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
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.scaleuptechnologies.zammad.plugins.module_utils.http_request import (
    make_request,
    validate_zammad_access,
)


def get_ticket(module, zammad_access, ticket_id):
    return make_request(module, "GET", zammad_access, None, ticket_id, expand=True)


def change_idoit_object(module, zammad_access, ticket_id, object_ids):
    data = {"ticket_id": ticket_id, "object_ids": object_ids}
    return make_request(module, "POST", zammad_access, data, endpoint="integration/idoit_ticket_update")


def run_module():
    module_args = dict(
        zammad_access=dict(
            type="dict",
            required=True,
            options=dict(
                zammad_url=dict(type="str", required=True),
                api_user=dict(type="str", required=False),
                api_secret=dict(type="str", required=False, no_log=True),
                api_token=dict(type="str", required=False, no_log=True),
            ),
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
    validate_zammad_access(module, zammad_access)
    state = module.params["state"]
    object_ids = module.params["object_ids"] if state == "present" else ["0"]

    try:
        ticket_data, status_code = get_ticket(module, zammad_access, module.params["ticket_id"])
        if status_code != 200:
            module.fail_json(msg="Failed to retrieve ticket data", status_code=status_code)
        old_object_ids = []
        if "preferences" in ticket_data and "idoit" in ticket_data["preferences"]:
            old_object_ids = ticket_data["preferences"]["idoit"]["object_ids"]
        if state == "present":
            new_object_ids = list(set(old_object_ids + object_ids))
        else:
            new_object_ids = list(set(old_object_ids) - set(object_ids))
        if set(old_object_ids) != set(new_object_ids):
            ticket_data, status_code = change_idoit_object(
                module,
                zammad_access,
                module.params["ticket_id"],
                object_ids,
            )

            result.update(
                changed=True,
                ticket_id=module.params["ticket_id"],
                status_code=status_code,
                message="Success",
            )
        else:
            result.update(
                changed=False,
                ticket_id=module.params["ticket_id"],
                status_code=status_code,
                message="Success",
            )
        module.exit_json(**result)

    except ValueError as e:
        module.fail_json(msg=str(e), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
