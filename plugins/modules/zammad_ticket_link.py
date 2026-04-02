#!/usr/bin/python

# Copyright: (c) 2025, Sven Anders <ansible2025@sven.anders.hamburg>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type


DOCUMENTATION = r"""
---
author:
  - Sven Anders (@tabacha) <ansible2025@sven.anders.hamburg>

module: zammad_ticket_link

short_description: Add or remove a link between two Zammad tickets.

version_added: "2.1.0"

description:
  - This module allows you to link or unlink two Zammad tickets using the Zammad API.
  - Links are directional: the source ticket is identified by its ticket number, the target by its internal ID.

options:
  source_ticket_number:
    description:
      - The ticket number of the source ticket (e.g., '42001').
    required: true
    type: str
  target_ticket_id:
    description:
      - The internal ID of the target ticket to link to.
    required: true
    type: int
  link_type:
    description:
      - The type of the link to create or remove.
    type: str
    required: false
    default: normal
    choices:
      - normal
      - parent
      - child
  state:
    description:
      - Whether the link should exist or not.
    type: str
    required: false
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment:
  - scaleuptechnologies.zammad.zammad_access
notes:
  - The module checks existing links before adding or removing, so it is fully idempotent.
"""

EXAMPLES = r"""
- name: Link two tickets
  scaleuptechnologies.zammad.zammad_ticket_link:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_token: "my_api_token"
    source_ticket_number: "42001"
    target_ticket_id: 12345
    link_type: normal
    state: present

- name: Remove a link between two tickets
  scaleuptechnologies.zammad.zammad_ticket_link:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_token: "my_api_token"
    source_ticket_number: "42001"
    target_ticket_id: 12345
    link_type: normal
    state: absent
"""

RETURN = r"""
changed:
  description: Whether the link was added or removed.
  returned: always
  type: bool
  sample: true
status_code:
  description: HTTP status code returned by the Zammad API.
  returned: always
  type: int
  sample: 201
message:
  description: Result message.
  returned: always
  type: str
  sample: "Link created successfully."
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.scaleuptechnologies.zammad.plugins.module_utils.http_request import (
    make_request,
    validate_zammad_access,
)


def get_links(module, zammad_access, target_ticket_id):
    return make_request(
        module,
        "GET",
        zammad_access,
        None,
        endpoint="links",
        query_params={"link_object": "Ticket", "link_object_value": target_ticket_id},
    )


def find_link(links_data, source_ticket_number, link_type):
    """Return (exists, source_ticket_id) for the given source_ticket_number and link_type.

    The GET /api/v1/links response contains an assets.Ticket dict keyed by ticket ID,
    where each entry has a "number" field. We match by ticket number to get the internal
    source ID, then verify the link_type in the links array.
    The source ID is needed for DELETE /api/v1/links/remove (link_object_source_value).
    """
    ticket_assets = links_data.get("assets", {}).get("Ticket", {})
    source_id = None
    for ticket_id_str, ticket in ticket_assets.items():
        if str(ticket.get("number")) == str(source_ticket_number):
            source_id = int(ticket_id_str)
            break
    if source_id is None:
        return False, None
    for link in links_data.get("links", []):
        if link.get("link_type") == link_type and link.get("link_object_value") == source_id:
            return True, source_id
    return False, source_id


def add_link(module, zammad_access, source_ticket_number, target_ticket_id, link_type):
    data = {
        "link_type": link_type,
        "link_object_source": "Ticket",
        "link_object_source_number": str(source_ticket_number),
        "link_object_target": "Ticket",
        "link_object_target_value": int(target_ticket_id),
    }
    return make_request(module, "POST", zammad_access, data, endpoint="links/add")


def remove_link(module, zammad_access, source_ticket_id, target_ticket_id, link_type):
    # DELETE requires the source ticket's internal ID (link_object_source_value),
    # not its display number. link_object_source_number is only accepted by links/add.
    data = {
        "link_type": link_type,
        "link_object_source": "Ticket",
        "link_object_source_value": int(source_ticket_id),
        "link_object_target": "Ticket",
        "link_object_target_value": int(target_ticket_id),
    }
    return make_request(module, "DELETE", zammad_access, data, endpoint="links/remove")


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
        source_ticket_number=dict(type="str", required=True),
        target_ticket_id=dict(type="int", required=True),
        link_type=dict(
            type="str",
            required=False,
            default="normal",
            choices=["normal", "parent", "child"],
        ),
        state=dict(type="str", required=False, default="present", choices=["present", "absent"]),
    )

    result = dict(changed=False, status_code=0, message="")
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    zammad_access = module.params["zammad_access"]
    validate_zammad_access(module, zammad_access)

    source_ticket_number = module.params["source_ticket_number"]
    target_ticket_id = module.params["target_ticket_id"]
    link_type = module.params["link_type"]
    state = module.params["state"]

    try:
        links_data, status_code = get_links(module, zammad_access, target_ticket_id)
        already_linked, source_id = find_link(links_data, source_ticket_number, link_type)

        if state == "present":
            if already_linked:
                result.update(changed=False, status_code=status_code, message="Link already exists.")
            else:
                _, status_code = add_link(
                    module, zammad_access, source_ticket_number, target_ticket_id, link_type,
                )
                result.update(changed=True, status_code=status_code, message="Link created successfully.")
        else:
            if not already_linked:
                result.update(changed=False, status_code=status_code, message="Link does not exist.")
            else:
                _, status_code = remove_link(
                    module, zammad_access, source_id, target_ticket_id, link_type,
                )
                result.update(changed=True, status_code=status_code, message="Link removed successfully.")

        module.exit_json(**result)

    except ValueError as e:
        module.fail_json(msg=str(e), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
