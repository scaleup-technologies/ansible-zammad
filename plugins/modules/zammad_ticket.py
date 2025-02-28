#!/usr/bin/python

# Copyright: (c) 2024, Melvin Ziemann <ziemann.melvin@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type


DOCUMENTATION = r"""
---
author:
  - Melvin Ziemann (@cloucs) <ziemann.melvin@gmail.com>

module: zammad_ticket

short_description: Create, update, or close a Zammad ticket via the API.

version_added: "1.0.0"

description:
  - This module allows you to create, update, or close a Zammad ticket using the Zammad API.
  - User credentials and ticket details are passed as parameters.
  - You can create or update a ticket based on the desired state (present), or close a ticket with (absent).
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
        required: true
        type: str
      api_secret:
        description:
          - The password or API key used to authenticate with the Zammad API.
        required: true
        type: str
  state:
    description:
      - The desired state of the ticket.
      - Use C(present) to create or update a ticket, and C(absent) to close a ticket.
    required: true
    type: str
    choices: ["present", "absent"]
  ticket_id:
    description:
      - The unique identifier of the ticket to update or close.
      - Required when updating or closing an existing ticket.
    required: false
    type: int
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
    required: false
    type: bool
    default: false
  ticket_state:
    description:
      - The state of the ticket (e.g., 'open', 'pending'). This defines the current state of the ticket.
    required: false
    type: str
  priority:
    description:
      - The priority of the ticket (e.g., '1 low', '2 normal', '3 high').
    required: false
    type: str
"""

EXAMPLES = r"""
- name: Create a new ticket
  zammad_ticket:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
    state: "present"
    title: "Internet Outage"
    group: "Support"
    customer: "customer@example.com"
    subject: "Internet is down"
    body: "The internet is not working since this morning."
    internal: false
    ticket_state: "open"
    priority: "3 high"

- name: Update an existing ticket
  zammad_ticket:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
    state: "present"
    ticket_id: 12345
    title: "Internet Outage - Follow Up"
    group: "Support"
    customer: "customer@example.com"
    subject: "Update on internet issue"
    body: "The internet issue is being worked on."
    internal: true
    ticket_state: "pending"
    priority: "2 normal"

- name: Close a ticket
  zammad_ticket:
    zammad_access:
      zammad_url: "https://zammad.example.com"
      api_user: "api_user"
      api_secret: "api_secret"
    state: "absent"
    ticket_id: 12345
    ticket_state: "closed"
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

#from ansible_collections.scaleuptechnologies.zammad_api.plugins.module_utils.http_request import make_request

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import json
import base64

def make_request(module, method, zammad_url, api_user, api_secret, api_token, data, ticket_id=None, endpoint=None):
    headers = {"Content-type": "application/json"}

    if api_token:
        headers["Authorization"] = f"Token {api_token}"
    else:
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


def create_ticket(module, zammad_url, api_user, api_secret, api_token, owner, customer, title, group, subject, body, internal, ticket_state, priority):
    article = {
        "subject": subject,
        "body": body,
        "type": "note",
        "internal": str(internal).lower()
    }
    data = {
        "article": article,
        **{key: value for key, value in {
            "owner_id": owner,
            "title": title,
            "group": group,
            "state": ticket_state,
            "customer": customer,
            **({"priority": priority} if priority is not None else {})
        }.items() if value is not None}
    }
    return make_request(module, "POST", zammad_url, api_user, api_secret, api_token, data)


def update_ticket(module, zammad_url, api_user, api_secret, api_token, ticket_id, owner, customer, title, group, subject, body, internal, ticket_state, priority):
    article = {}
    if body:
        article = {
            "subject": subject,
            "body": body,
            "type": "note",
            "internal": str(internal).lower()
        }
    data = {
        "article": article,
        **{key: value for key, value in {
            "owner_id": owner,
            "title": title,
            "group": group,
            "state": ticket_state,
            **({"priority": priority} if priority is not None else {})        }.items() if value is not None}
    }
    return make_request(module, "PUT", zammad_url, api_user, api_secret, api_token, data, ticket_id)


def close_ticket(module, zammad_url, api_user, api_secret, api_token, ticket_id):
    data = {"state": "closed"}
    return make_request(module, "PUT", zammad_url, api_user, api_secret, api_token, data, ticket_id)


def get_ticket(module, zammad_url, api_user, api_secret, api_token, ticket_id):
    return make_request(module, "GET", zammad_url, api_user, api_secret, api_token, {}, ticket_id)


def get_users(module, zammad_url, api_user, api_secret, api_token):
    return make_request(module, "GET", zammad_url, api_user, api_secret, api_token, {}, endpoint="users")


def get_customer_email(ticket_data, customers):
    customer_id = ticket_data.get("customer_id")
    for customer in customers:
        if customer["id"] == customer_id:
            return customer["email"]


def get_owner_name(ticket_data, owners):
    owner_id = ticket_data.get("owner_id")
    for owner in owners:
        if owner["id"] == owner_id:
            return owner["firstname"] + " " + owner["lastname"]


def get_owner_id(owner_name, owners):
    if owner_name is None:
        return
    firstname, lastname = owner_name.split(maxsplit=1)
    for owner in owners:
        if owner["firstname"] == firstname and owner["lastname"] == lastname:
            return owner["id"]


def get_groups(module, zammad_url, api_user, api_secret, api_token):
    return make_request(module, "GET", zammad_url, api_user, api_secret, api_token, {}, endpoint="groups")


def get_group_name(ticket_data, groups):
    group_id = ticket_data.get("group_id")
    for group in groups:
        if group["id"] == group_id:
            return group["name"]


def get_ticket_states(module, zammad_url, api_user, api_secret, api_token):
    return make_request(module, "GET", zammad_url, api_user, api_secret, api_token, {}, endpoint="ticket_states")


def get_ticket_state_name(ticket_data, ticket_states):
    ticket_state_id = ticket_data.get("state_id")
    for ticket_state in ticket_states:
        if ticket_state["id"] == ticket_state_id:
            return ticket_state["name"]


def get_priorities(module, zammad_url, api_user, api_secret, api_token):
    return make_request(module, "GET", zammad_url, api_user, api_secret, api_token, {}, endpoint="ticket_priorities")


def get_priority_name(ticket_data, priorities):
    priority_id = ticket_data.get("priority_id")
    for priority in priorities:
        if priority["id"] == priority_id:
            return priority["name"]


def get_ticket_articles(module, zammad_url, api_user, api_secret, api_token, ticket_id):
    return make_request(module, "GET", zammad_url, api_user, api_secret, api_token, {}, endpoint=f"ticket_articles/by_ticket/{ticket_id}")


def get_last_article_data(ticket_articles, article_object):
    return ticket_articles[-1][f"{article_object}"]


def validate_params(module, required_params):
    zammad_access = module.params.get("zammad_access", {})

    if not any(zammad_access.get(param) for param in ["api_token", "api_user", "api_secret"]):
        module.fail_json(msg="Missing required zammad_access parameters: api_token or api_user and api_secret.")

    #if not all(zammad_access.get(param) for param in ["zammad_url", "api_user", "api_secret"]):
    #    module.fail_json(msg="Missing required zammad_access parameters: zammad_url, api_user, and/or api_secret.")

    for param in required_params:
        if param != "priority" and not module.params.get(param):
            module.fail_json(msg=f"Missing required parameter: {param}")


def has_changes(current_ticket_data, ticket_data):
    for key, value in ticket_data.items():
        if value is not None:
            if current_ticket_data.get(key) != value:
                return True
    return False


def run_module():
    module_args = dict(
        zammad_access=dict(
            type="dict",
            required=True,
            options=dict(
                zammad_url=dict(type="str", required=True),
                api_user=dict(type="str", required=False),
                api_secret=dict(type="str", required=False, no_log=True),
                api_token=dict(type="str", equired=False, no_log=True)
            )
        ),
        state=dict(type="str", required=True, choices=("present", "absent")),
        ticket_id=dict(type="int", required=False),
        owner=dict(type="str", required=False, default=None),
        customer=dict(type="str", required=False, default=None),
        title=dict(type="str", required=False, default=None),
        group=dict(type="str", required=False, default=None),
        subject=dict(type="str", required=False, default=None),
        body=dict(type="str", required=False, default=None),
        internal=dict(type="bool", required=False, default="false"),
        ticket_state=dict(type="str", required=False, default=None),
        priority=dict(type="str", required=False, default=None)
    )

    module_args = {**module_args}

    result = dict(changed=False, ticket_id=None, status_code=0, message="")
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    zammad_access = module.params["zammad_access"]
    zammad_url = zammad_access["zammad_url"]
    api_user = zammad_access.get("api_user")
    api_secret = zammad_access.get("api_secret")
    api_token = zammad_access.get("api_token")

    try:
        users, status_code = get_users(module, zammad_url, api_user, api_secret, api_token)
        groups, status_code = get_groups(module, zammad_url, api_user, api_secret, api_token)
        ticket_states, status_code = get_ticket_states(module, zammad_url, api_user, api_secret, api_token)
        priorities, status_code = get_priorities(module, zammad_url, api_user, api_secret, api_token)

        state = module.params["state"]
        if state == "present" and module.params["ticket_id"]:
            validate_params(module, ["ticket_id"])
            ticket_data, status_code = get_ticket(module, zammad_url, api_user, api_secret, api_token, module.params["ticket_id"])
            ticket_articles, status_code = get_ticket_articles(module, zammad_url, api_user, api_secret, api_token, module.params["ticket_id"])

            current_ticket_data = {
                "owner": get_owner_name(ticket_data, users),
                "customer": get_customer_email(ticket_data, users),
                "title": ticket_data["title"],
                "group": get_group_name(ticket_data, groups),
                "subject": get_last_article_data(ticket_articles, "subject"),
                "body": get_last_article_data(ticket_articles, "body"),
                "internal": str(get_last_article_data(ticket_articles, "internal")).lower(),
                "ticket_state": get_ticket_state_name(ticket_data, ticket_states),
                "priority": get_priority_name(ticket_data, priorities)
            }

            ticket_data = {
                "owner": module.params["owner"],
                "customer": module.params["customer"],
                "title": module.params["title"],
                "group": module.params["group"],
                "subject": module.params["subject"],
                "body": module.params["body"],
                "internal": str(module.params["internal"]).lower(),
                "ticket_state": module.params["ticket_state"],
                "priority": module.params["priority"]
            }

            if has_changes(current_ticket_data, ticket_data):
                ticket_data, status_code = update_ticket(
                    module,
                    zammad_url,
                    api_user,
                    api_secret,
                    api_token,
                    module.params["ticket_id"],
                    get_owner_id(module.params["owner"], users),
                    module.params["customer"],
                    module.params["title"],
                    module.params["group"],
                    module.params["subject"],
                    module.params["body"],
                    module.params["internal"],
                    module.params["ticket_state"],
                    module.params["priority"]
                )
                result.update({
                    "changed": True,
                    "ticket_id": module.params["ticket_id"],
                    "status_code": status_code,
                    "message": "Ticket updated successfully."
                })
            else:
                result.update({
                    "changed": False,
                    "ticket_id": module.params["ticket_id"],
                    "message": "No changes required."
                })

        elif state == "present":
            validate_params(module, ["customer", "title", "group", "subject", "body", "ticket_state", "priority"])
            ticket_data, status_code = create_ticket(
                module,
                zammad_url,
                api_user,
                api_secret,
                api_token,
                get_owner_id(module.params["owner"], users),
                module.params["customer"],
                module.params["title"],
                module.params["group"],
                module.params["subject"],
                module.params["body"],
                module.params["internal"],
                module.params["ticket_state"],
                module.params["priority"]
            )
            result.update({
                "changed": True,
                "ticket_id": ticket_data.get("id"),
                "status_code": status_code,
                "message": "Ticket created successfully."
            })

        elif state == "absent":
            validate_params(module, ["ticket_id"])
            ticket_data, status_code = get_ticket(module, zammad_url, api_user, api_secret, api_token, module.params["ticket_id"])

            current_ticket_data = {"ticket_state": get_ticket_state_name(ticket_data, ticket_states)}

            ticket_data = {"ticket_state": module.params["ticket_state"]}

            if has_changes(current_ticket_data, ticket_data):
                ticket_data, status_code = close_ticket(module, zammad_url, api_user, api_secret, api_token, module.params["ticket_id"])
                result.update({
                    "changed": True,
                    "ticket_id": module.params["ticket_id"],
                    "status_code": status_code,
                    "message": "Ticket closed successfully."
                })
            else:
                result.update({
                    "changed": False,
                    "ticket_id": module.params["ticket_id"],
                    "message": "Ticket is already closed."
                })

        module.exit_json(**result)

    except ValueError as e:
        module.fail_json(msg=str(e), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
