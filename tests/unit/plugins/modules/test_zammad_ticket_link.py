# Description: Unittest for zammad_ticket_link module

from __future__ import absolute_import, division, print_function

import json
import pytest
from unittest.mock import patch, MagicMock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from plugins.modules import zammad_ticket_link

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
        zammad_ticket_link.main()


def test_add_link():
    fake_response = MagicMock()
    fake_response.read.return_value = b"{}"
    fake_info = {"status": 201, "msg": "Created"}

    with patch(FETCH_URL_METHOD, side_effect=[(fake_response, fake_info)]) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_token": "my_api_token",
                },
                "source_ticket_number": "42001",
                "target_ticket_id": 12345,
                "link_type": "normal",
                "state": "present",
            }
        )
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
            assert result["status_code"] == 201
        assert mock_fetch_url.call_count == 1

        call_args = mock_fetch_url.call_args_list[0]
        assert call_args[0][1] == "https://example.com/api/v1/links/add"
        assert call_args[1]["method"] == "POST"
        assert json.loads(call_args[1]["data"]) == {
            "link_type": "normal",
            "link_object_source": "Ticket",
            "link_object_source_number": "42001",
            "link_object_target": "Ticket",
            "link_object_target_value": 12345,
        }


def test_remove_link():
    fake_response = MagicMock()
    fake_response.read.return_value = b"{}"
    fake_info = {"status": 200, "msg": "OK"}

    with patch(FETCH_URL_METHOD, side_effect=[(fake_response, fake_info)]) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_user": "user",
                    "api_secret": "secret",
                },
                "source_ticket_number": "42001",
                "target_ticket_id": 12345,
                "link_type": "normal",
                "state": "absent",
            }
        )
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
            assert result["status_code"] == 200
        assert mock_fetch_url.call_count == 1

        call_args = mock_fetch_url.call_args_list[0]
        assert call_args[0][1] == "https://example.com/api/v1/links/remove"
        assert call_args[1]["method"] == "DELETE"
        assert json.loads(call_args[1]["data"]) == {
            "link_type": "normal",
            "link_object_source": "Ticket",
            "link_object_source_number": "42001",
            "link_object_target": "Ticket",
            "link_object_target_value": 12345,
        }


def test_add_link_default_link_type():
    fake_response = MagicMock()
    fake_response.read.return_value = b"{}"
    fake_info = {"status": 201, "msg": "Created"}

    with patch(FETCH_URL_METHOD, side_effect=[(fake_response, fake_info)]) as mock_fetch_url:
        set_module_args(
            {
                "zammad_access": {
                    "zammad_url": "https://example.com",
                    "api_token": "my_api_token",
                },
                "source_ticket_number": "42001",
                "target_ticket_id": 12345,
            }
        )
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        assert mock_fetch_url.call_count == 1

        call_args = mock_fetch_url.call_args_list[0]
        assert call_args[1]["method"] == "POST"
        assert json.loads(call_args[1]["data"])["link_type"] == "normal"
