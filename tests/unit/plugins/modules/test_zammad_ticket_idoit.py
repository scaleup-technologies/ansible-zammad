from __future__ import absolute_import, division, print_function

import json
import pytest
from unittest.mock import patch, MagicMock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from plugins.modules import zammad_ticket_idoit

__metaclass__ = type

MY_COLLECTION = "scaleuptechnologies.zammad"
FETCH_URL_METHOD = (
    f"ansible_collections.{MY_COLLECTION}.plugins.module_utils.http_request.fetch_url"
)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def set_module_args(args):
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)
    if hasattr(basic, "_ANSIBLE_PROFILE"):
        basic._ANSIBLE_PROFILE = "legacy"


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
        zammad_ticket_idoit.main()


def test_module_key_does_not_exist_before():
    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = b'{"preferences": {}}'
    fake_info_1 = {"status": 200, "msg": "OK"}

    fake_response_2 = MagicMock()
    fake_response_2.read.return_value = b'{"preferences": {"idoit": {"object_ids": ["123"]}}}'
    fake_info_2 = {"status": 200, "msg": "OK"}

    with patch(
        FETCH_URL_METHOD,
        side_effect=[(fake_response_1, fake_info_1), (fake_response_2, fake_info_2)],
    ) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_user": "user",
                    "api_secret": "secret",
                },
                "ticket_id": 1,
                "object_ids": ["123"],
                "state": "present",
            }
        )
        try:
            zammad_ticket_idoit.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 2

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets/1?expand=true"
        assert first_call_args[1]["method"] == "GET"
        assert first_call_args[1]["data"] is None

        # Überprüfen der übergebenen Parameter beim zweiten Aufruf
        second_call_args = mock_fetch_url.call_args_list[1]
        assert second_call_args[0][1] == "https://example.com/api/v1/integration/idoit_ticket_update"
        assert second_call_args[1]["method"] == "POST"
        assert json.loads(second_call_args[1]["data"]) == {"ticket_id": 1, "object_ids": ["123"]}


def test_module_no_changes():

    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = b'{"preferences": {"idoit": {"object_ids": ["123"]}}}'
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
                "ticket_id": 1,
                "object_ids": ["123"],
                "state": "present",
            }
        )
        try:
            zammad_ticket_idoit.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is False
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 1

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets/1?expand=true"
        assert first_call_args[1]["method"] == "GET"
        assert first_call_args[1]["data"] is None


def test_module_success():
    fake_response_1 = MagicMock()
    fake_response_1.read.return_value = b'{"preferences": {"idoit": {"object_ids": []}}}'
    fake_info_1 = {"status": 200, "msg": "OK"}

    fake_response_2 = MagicMock()
    fake_response_2.read.return_value = b'{"preferences": {"idoit": {"object_ids": ["123"]}}}'
    fake_info_2 = {"status": 200, "msg": "OK"}

    with patch(
        FETCH_URL_METHOD,
        side_effect=[(fake_response_1, fake_info_1), (fake_response_2, fake_info_2)],
    ) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_user": "user",
                    "api_secret": "secret",
                },
                "ticket_id": 1,
                "object_ids": ["123"],
                "state": "present",
            }
        )
        try:
            zammad_ticket_idoit.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        # Überprüfen, dass fetch_url zweimal aufgerufen wurde
        assert mock_fetch_url.call_count == 2

        # Überprüfen der übergebenen Parameter beim ersten Aufruf
        first_call_args = mock_fetch_url.call_args_list[0]
        assert first_call_args[0][1] == "https://example.com/api/v1/tickets/1?expand=true"
        assert first_call_args[1]["method"] == "GET"
        assert first_call_args[1]["data"] is None

        # Überprüfen der übergebenen Parameter beim zweiten Aufruf
        second_call_args = mock_fetch_url.call_args_list[1]
        assert second_call_args[0][1] == "https://example.com/api/v1/integration/idoit_ticket_update"
        assert second_call_args[1]["method"] == "POST"
        assert json.loads(second_call_args[1]["data"]) == {"ticket_id": 1, "object_ids": ["123"]}
