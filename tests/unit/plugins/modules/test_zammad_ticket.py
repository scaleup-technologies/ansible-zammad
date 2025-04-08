# Description: Unittest for zammad_ticket module

from __future__ import absolute_import, division, print_function

import json
import pytest
from unittest.mock import patch, MagicMock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from plugins.modules import zammad_ticket
import os.path

__metaclass__ = type

MY_COLLECTION = "scaleuptechnologies.zammad"
FETCH_URL_METHOD = (
    f"ansible_collections.{MY_COLLECTION}.plugins.module_utils.http_request.fetch_url"
)

fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture_file(filename):
    with open(os.path.join(fixture_path, filename), "r") as f:
        return f.read()


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def set_module_args(args):
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)


def exit_json(*args, **kwargs):
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


def get_bin_path(self, arg, required=False):
    if arg.endswith("my_command"):
        return "/usr/bin/my_command"
    elif required:
        fail_json(msg="%r not found !" % arg)


@pytest.fixture(autouse=True)
def mock_ansible_module():
    with patch.multiple(
        basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json, get_bin_path=get_bin_path
    ):
        yield


def test_module_fail_when_required_args_missing():
    with pytest.raises(AnsibleFailJson):
        set_module_args({})
        zammad_ticket.main()


def test_auth_secret_missing():
    set_module_args(
        {
            "zammad_access": {
                "zammad_url": "https://example.com",
                "api_user": "user",
            },
            "title": "Internet Outage",
            "group": "Support",
            "customer": "customer@example.com",
            "subject": "Internet is down",
            "body": "The internet is not working since this morning.",
            "internal": "false",
            "state": "open",
            "priority": "3 high",
        }
    )
    try:
        zammad_ticket.main()
    except AnsibleFailJson as e:
        result = e.args[0]
        assert result["msg"] == "Missing required zammad_access parameters: api_secret."


def test_auth_missing():
    set_module_args(
        {
            "zammad_access": {
                "zammad_url": "https://example.com",
            },
            "title": "Internet Outage",
            "group": "Support",
            "customer": "customer@example.com",
            "subject": "Internet is down",
            "body": "The internet is not working since this morning.",
            "internal": "false",
            "state": "open",
            "priority": "3 high",
        }
    )
    try:
        zammad_ticket.main()
    except AnsibleFailJson as e:
        result = e.args[0]
        assert (
            result["msg"]
            == "Missing required zammad_access parameters: api_token or api_user and api_secret."
        )


def test_create_new_ticket():
    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = b'{"preferences": {"idoit": {"object_ids": []}}}'
    fake_info_1 = {"status": 200, "msg": "OK"}

    with patch(
        FETCH_URL_METHOD,
        side_effect=[(fake_response_1, fake_info_1)],
    ) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_user": "user",
                    "api_secret": "secret",
                },
                "title": "Internet Outage",
                "group": "Support",
                "customer": "customer@example.com",
                "subject": "Internet is down",
                "body": "The internet is not working since this morning.",
                "internal": "false",
                "state": "open",
                "priority": "3 high",
            }
        )
        try:
            zammad_ticket.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 1

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets"
        assert first_call_args[1]["method"] == "POST"
        expected_data = {
            "customer": "customer@example.com",
            "title": "Internet Outage",
            "group": "Support",
            "state": "open",
            "priority": "3 high",
            "article": {
                "subject": "Internet is down",
                "body": "The internet is not working since this morning.",
                "type": "note",
                "internal": "false",
                "content_type": "text/plain",
                "sender": "Agent",
            },
        }
        assert json.loads(first_call_args[1]["data"]) == expected_data


def test_update_ticket_piority():

    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = read_fixture_file("ticket42.json")
    fake_info_1 = {"status": 200, "msg": "OK"}

    fake_response_2 = MagicMock()
    fake_response_2.read.return_value = read_fixture_file("articles42.json")

    fake_info_2 = {"status": 200, "msg": "OK"}

    fake_response_3 = MagicMock()
    fake_response_3.read.return_value = '{"id": 42}'
    fake_info_3 = {"status": 201, "msg": "OK"}
    with patch(
        FETCH_URL_METHOD,
        side_effect=[
            (fake_response_1, fake_info_1),
            (fake_response_2, fake_info_2),
            (fake_response_3, fake_info_3),
        ],
    ) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_token": "my_api_token",
                },
                "ticket_id": 42,
                "priority": "3 high",
            }
        )
        try:
            zammad_ticket.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 3

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets/42?expand=true"
        assert first_call_args[1]["method"] == "GET"

        secnd_call_args = mock_fetch_url.call_args_list[1]
        assert secnd_call_args[0][1] == "https://example.com/api/v1/ticket_articles/by_ticket/42"
        assert secnd_call_args[1]["method"] == "GET"
        third_call_args = mock_fetch_url.call_args_list[2]
        assert third_call_args[0][1] == "https://example.com/api/v1/tickets/42"
        print(json.dumps(dict(third_call_args[1])))
        assert third_call_args[1]["method"] == "PUT"
        expected_data = {
            "priority": "3 high",
        }
        assert json.loads(third_call_args[1]["data"]) == expected_data


def test_equal_ticket_piority():

    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = read_fixture_file("ticket42.json")
    fake_info_1 = {"status": 200, "msg": "OK"}

    fake_response_2 = MagicMock()
    fake_response_2.read.return_value = read_fixture_file("articles42.json")

    fake_info_2 = {"status": 200, "msg": "OK"}

    fake_response_3 = MagicMock()
    fake_response_3.read.return_value = '{"id": 42}'
    fake_info_3 = {"status": 201, "msg": "OK"}
    with patch(
        FETCH_URL_METHOD,
        side_effect=[
            (fake_response_1, fake_info_1),
            (fake_response_2, fake_info_2),
            (fake_response_3, fake_info_3),
        ],
    ) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_token": "my_api_token",
                },
                "ticket_id": 42,
                "priority": "2 normal",
            }
        )
        try:
            zammad_ticket.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is False
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 2

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets/42?expand=true"
        assert first_call_args[1]["method"] == "GET"

        secnd_call_args = mock_fetch_url.call_args_list[1]
        assert secnd_call_args[0][1] == "https://example.com/api/v1/ticket_articles/by_ticket/42"
        assert secnd_call_args[1]["method"] == "GET"


def test_update_ticket_new_article_and_priority():

    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = read_fixture_file("ticket42.json")
    fake_info_1 = {"status": 200, "msg": "OK"}

    fake_response_2 = MagicMock()
    fake_response_2.read.return_value = read_fixture_file("articles42.json")

    fake_info_2 = {"status": 200, "msg": "OK"}

    fake_response_3 = MagicMock()
    fake_response_3.read.return_value = '{"id": 42}'
    fake_info_3 = {"status": 201, "msg": "OK"}
    with patch(
        FETCH_URL_METHOD,
        side_effect=[
            (fake_response_1, fake_info_1),
            (fake_response_2, fake_info_2),
            (fake_response_3, fake_info_3),
        ],
    ) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_token": "my_api_token",
                },
                "ticket_id": 42,
                "priority": "3 high",
                "subject": "Internet is down",
                "body": "The internet is not working since this morning.",
            }
        )
        try:
            zammad_ticket.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 3

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets/42?expand=true"
        assert first_call_args[1]["method"] == "GET"

        secnd_call_args = mock_fetch_url.call_args_list[1]
        assert secnd_call_args[0][1] == "https://example.com/api/v1/ticket_articles/by_ticket/42"
        assert secnd_call_args[1]["method"] == "GET"
        third_call_args = mock_fetch_url.call_args_list[2]
        assert third_call_args[0][1] == "https://example.com/api/v1/tickets/42"
        print(json.dumps(dict(third_call_args[1])))
        assert third_call_args[1]["method"] == "PUT"
        expected_data = {
            "article": {
                "body": "The internet is not working since this morning.",
                "content_type": "text/plain",
                "internal": "false",
                "sender": "Agent",
                "subject": "Internet is down",
                "type": "note",
            },
            "priority": "3 high",
        }
        assert json.loads(third_call_args[1]["data"]) == expected_data


def test_update_ticket_new_article():

    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = read_fixture_file("ticket42.json")
    fake_info_1 = {"status": 200, "msg": "OK"}

    fake_response_2 = MagicMock()
    fake_response_2.read.return_value = read_fixture_file("articles42.json")

    fake_info_2 = {"status": 200, "msg": "OK"}

    fake_response_3 = MagicMock()
    fake_response_3.read.return_value = '{"id": 42}'
    fake_info_3 = {"status": 201, "msg": "OK"}
    with patch(
        FETCH_URL_METHOD,
        side_effect=[
            (fake_response_1, fake_info_1),
            (fake_response_2, fake_info_2),
            (fake_response_3, fake_info_3),
        ],
    ) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_token": "my_api_token",
                },
                "ticket_id": 42,
                "subject": "Internet is down",
                "body": "The internet is not working since this morning.",
            }
        )
        try:
            zammad_ticket.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 3

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets/42?expand=true"
        assert first_call_args[1]["method"] == "GET"

        secnd_call_args = mock_fetch_url.call_args_list[1]
        assert secnd_call_args[0][1] == "https://example.com/api/v1/ticket_articles/by_ticket/42"
        assert secnd_call_args[1]["method"] == "GET"
        third_call_args = mock_fetch_url.call_args_list[2]
        assert third_call_args[0][1] == "https://example.com/api/v1/ticket_articles"
        print(json.dumps(dict(third_call_args[1])))
        assert third_call_args[1]["method"] == "POST"
        expected_data = {
            "body": "The internet is not working since this morning.",
            "content_type": "text/plain",
            "internal": "false",
            "sender": "Agent",
            "subject": "Internet is down",
            "ticket_id": 42,
            "type": "note",
        }
        assert json.loads(third_call_args[1]["data"]) == expected_data
