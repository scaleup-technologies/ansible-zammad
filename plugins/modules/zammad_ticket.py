#!/usr/bin/python

# Copyright: (c) 2024-2025,
#  * Melvin Ziemann <ziemann.melvin@gmail.com>
#  * Sven Anders <ansible2025@sven.anders.hamburg>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type


DOCUMENTATION = r"""
---
author:
  - Melvin Ziemann (@cloucs) <ziemann.melvin@gmail.com>
  - Sven Anders (@tabacha) <ansible2025@sven.anders.hamburg>

module: zammad_ticket

short_description: Create, update, or close a Zammad ticket via the API.

version_added: "1.0.0"

description:
  - This module allows you to create, update, or close a Zammad ticket using the Zammad API.
  - User credentials and ticket details are passed as parameters.
  - When updating or creating, you can define various parameters like the ticket owner, customer, title, body, priority, etc.

options:
  zammad_access:
    description:
      - Dictionary containing the Zammad API credentials.
    required: true
    type: dict
    suboptions:
      zammad_url:
        description:
          - The fully qualified domain name of the Zammad instance (e.g., https://zammad.example.com).
        required: true
        type: str
      api_user:
        description:
          - The username used to authenticate with the Zammad API.
        required: false
        type: str
      api_secret:
        description:
          - The password or API key used to authenticate with the Zammad API.
        required: false
        type: str
      api_token:
        description:
          - The API token used to authenticate with the Zammad API.
        required: false
        type: str
  ticket_id:
    description:
      - The unique identifier of the ticket to update or close.
      - Required when updating or closing an existing ticket.
    required: false
    type: int
  state:
    description:
      - The state of the ticket (e.g., 'open', 'pending').
    required: false
    type: str
  owner:
    description:
      - The name of the owner for the ticket (e.g., 'John Doe'). Only required when creating or updating a ticket.
    required: false
    type: str
  customer:
    description:
      - The email address of the customer for the ticket.
    required: false
    type: str
  title:
    description:
      - The title of the ticket.
    required: false
    type: str
  group:
    description:
      - The group handling the ticket (e.g., 'Support').
    required: false
    type: str
  subject:
    description:
      - The subject for the ticket's article (e.g., 'Internet Outage').
    required: false
    type: str
  body:
    description:
      - The body content for the ticket's article (e.g., 'The internet is not working since this morning.').
    required: false
    type: str
  internal:
    description:
      - Indicates whether the article is internal (i.e., visible to agents only). Defaults to false.
    type: bool
    default: false
  priority:
    description:
      - The priority of the ticket (e.g., '1 low', '2 normal', '3 high').
    required: false
    type: str
  sender:
    description:
      - Indicates which user did create the article.
    choices:
      - Agent
      - Customer
      - System
    default: Agent
    required: false
    type: str
  content_type:
    description:
      - The content type of the article (e.g., 'text/html', 'text/plain').
    type: str
    default: 'text/plain'
    choices: ['text/html', 'text/plain']
  cc:
    description:
      - Comma-separated list of CC recipients for the ticket's article (e.g., 'a@example.com, b@example.com').
    required: false
    type: str
  custom_fields:
    description:
      - Custom objects that can be passed to the Zammad API to extend the functionality.
    required: false
    type: dict
    default: {}
"""

EXAMPLES = r"""
- name: Create a new ticket
  zammad_ticket:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
      api_token: "api_token"
    title: "Internet Outage"
    group: "Support"
    customer: "customer@example.com"
    subject: "Internet is down"
    body: "The internet is not working since this morning."
    internal: false
    state: "open"
    priority: "3 high"

- name: Update an existing ticket
  zammad_ticket:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
      api_toke: "api_token"
    ticket_id: 12345
    title: "Internet Outage - Follow Up"
    group: "Support"
    customer: "customer@example.com"
    subject: "Update on internet issue"
    body: "The internet issue is being worked on."
    internal: true
    state: "open"
    priority: "2 normal"

- name: Close a ticket
  zammad_ticket:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
      api_token: "api_token"
    ticket_id: 12345
    state: "closed"
"""

RETURN = r"""
ticket_id:
  description: The ID of the created or updated support ticket.
  type: int
  returned: always
  sample: 12345
status_code:
  description: The status code returned by the Zammad API.
  type: int
  returned: always
  sample: 200
message:
  description: A message indicating the result of the operation (success or failure).
  type: str
  returned: always
  sample: "Ticket created successfully."
"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.scaleuptechnologies.zammad.plugins.module_utils.http_request import (
    make_request,
    validate_zammad_access,
)


def create_ticket(module, zammad_access, data: dict):
    return make_request(module, "POST", zammad_access, data)


def update_ticket(module, zammad_access, ticket_id, data: dict):
    return make_request(module, "PUT", zammad_access, data, ticket_id)


def create_article(
    module,
    zammad_access,
    ticket_id,
    subject: str,
    body: str,
    internal: bool,
    content_type: str,
    sender: str,
    cc: str = None,
):
    data = {
        "ticket_id": ticket_id,
        "subject": subject,
        "body": body,
        "type": "note",
        "internal": str(internal).lower(),
        "content_type": content_type,
        "sender": sender,
    }
    if cc:
        data["cc"] = cc
    return make_request(module, "POST", zammad_access, data, endpoint="ticket_articles")


def get_ticket(module, zammad_access, ticket_id):
    return make_request(module, "GET", zammad_access, {}, ticket_id, expand=True)


def get_ticket_articles(module, zammad_access, ticket_id):
    return make_request(
        module,
        "GET",
        zammad_access,
        {},
        endpoint=f"ticket_articles/by_ticket/{ticket_id}",
    )


def get_last_article_data(ticket_articles, article_object):
    return ticket_articles[-1][f"{article_object}"]


def validate_params(module, required_params):
    zammad_access = module.params.get("zammad_access", {})
    validate_zammad_access(module, zammad_access)

    for param in required_params:
        if param != "priority" and not module.params.get(param):
            module.fail_json(msg=f"Missing required parameter: {param}")


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
        ticket_id=dict(type="int", required=False),
        owner=dict(type="str", required=False),
        customer=dict(type="str", required=False),
        title=dict(type="str", required=False),
        group=dict(type="str", required=False),
        subject=dict(type="str", required=False),
        body=dict(type="str", required=False),
        internal=dict(type="bool", required=False, default="false"),
        state=dict(type="str", required=False),
        priority=dict(type="str", required=False),
        custom_fields=dict(type="dict", default={}),
        content_type=dict(
            type="str", required=False, default="text/plain", choices=["text/html", "text/plain"]
        ),
        sender=dict(
            type="str", choices=["Agent", "Customer", "System"], required=False, default="Agent"
        ),
        cc=dict(type="str", required=False),
    )

    module_args = {**module_args}

    result = dict(changed=False, ticket_id=None, status_code=0, message="")
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    zammad_access = module.params["zammad_access"]
    validate_zammad_access(module, zammad_access)

    try:
        ticket_keys = [
            "owner",
            "customer",
            "title",
            "group",
            "state",
            "priority",
        ]
        for custom_field_name in module.params["custom_fields"].keys():
            ticket_keys.append(custom_field_name)
        if module.params["ticket_id"]:
            validate_params(module, ["ticket_id"])
            ticket_data, status_code = get_ticket(module, zammad_access, module.params["ticket_id"])
            ticket_articles, status_code = get_ticket_articles(
                module, zammad_access, module.params["ticket_id"]
            )

            ticket_changes = False
            article_changes = False
            new_ticket_data = {}
            for key in ticket_keys:
                if key in module.params and module.params[key] is not None:
                    if key in module.params.keys():
                        new_value = module.params[key]
                    else:
                        new_value = module.params["custom_fields"][key]
                    if key not in ticket_data or new_value != ticket_data[key]:
                        ticket_changes = True
                        new_ticket_data[key] = new_value
            # We create a new article if the subject or body has changed
            for key in ["subject", "body"]:
                if key in module.params and module.params[key] is not None:
                    new_value = module.params[key]
                    if new_value != get_last_article_data(ticket_articles, key):
                        article_changes = True

            if ticket_changes:
                if article_changes:
                    new_ticket_data["article"] = {
                        "subject": module.params["subject"],
                        "body": module.params["body"],
                        "type": "note",
                        "internal": str(module.params["internal"]).lower(),
                        "content_type": module.params["content_type"],
                    }
                    if module.params["sender"]:
                        new_ticket_data["article"]["sender"] = module.params["sender"]
                    if module.params["cc"]:
                        new_ticket_data["article"]["cc"] = module.params["cc"]
                ticket_data, status_code = update_ticket(
                    module, zammad_access, module.params["ticket_id"], new_ticket_data
                )
            elif article_changes:
                article_data, status_code = create_article(
                    module,
                    zammad_access,
                    module.params["ticket_id"],
                    module.params["subject"],
                    module.params["body"],
                    module.params["internal"],
                    module.params["content_type"],
                    module.params["sender"],
                    module.params["cc"],
                )
            if ticket_changes:
                result.update(
                    {
                        "changed": True,
                        "ticket_id": module.params["ticket_id"],
                        "status_code": status_code,
                        "message": "Ticket updated successfully.",
                    }
                )
            elif article_changes:
                result.update(
                    {
                        "changed": True,
                        "ticket_id": module.params["ticket_id"],
                        "status_code": status_code,
                        "article_id": article_data["id"],
                        "message": "Article created successfully.",
                    }
                )
            else:
                result.update(
                    {
                        "changed": False,
                        "ticket_id": module.params["ticket_id"],
                        "message": "No changes required.",
                    }
                )

        else:
            # Keine Ticket-Id: Ticket neu erstellen
            validate_params(
                module,
                ["customer", "title", "group", "subject", "body", "state"],
            )
            ticket_data = {}
            for key in ticket_keys:
                if key in module.params and module.params[key] is not None:
                    ticket_data[key] = module.params[key]
            ticket_data["article"] = {
                "subject": module.params["subject"],
                "body": module.params["body"],
                "type": "note",
                "internal": str(module.params["internal"]).lower(),
                "content_type": module.params["content_type"],
            }
            if module.params["sender"]:
                ticket_data["article"]["sender"] = module.params["sender"]
            if module.params["cc"]:
                ticket_data["article"]["cc"] = module.params["cc"]
            ticket_data, status_code = create_ticket(module, zammad_access, ticket_data)
            result.update(
                {
                    "changed": True,
                    "ticket_id": ticket_data.get("id"),
                    "status_code": status_code,
                    "message": "Ticket created successfully.",
                }
            )

        module.exit_json(**result)

    except ValueError as e:
        module.fail_json(msg=str(e), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
