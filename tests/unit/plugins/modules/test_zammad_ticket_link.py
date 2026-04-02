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

BASE_ARGS = {
    "zammad_access": {
        "zammad_url": "https://example.com",
        "api_token": "my_api_token",
    },
    "source_ticket_number": "42001",
    "target_ticket_id": 5,
    "link_type": "normal",
}

# GET /api/v1/links response when NO link exists yet
LINKS_RESPONSE_EMPTY = json.dumps({"links": [], "assets": {"Ticket": {}}}).encode()

# GET /api/v1/links response when the link already exists
LINKS_RESPONSE_EXISTS = json.dumps(
    {
        "links": [{"link_type": "normal", "link_object": "Ticket", "link_object_value": 41}],
        "assets": {
            "Ticket": {
                "41": {"id": 41, "number": "42001"},
            }
        },
    }
).encode()


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


def test_add_link_not_yet_existing():
    fake_get = MagicMock()
    fake_get.read.return_value = LINKS_RESPONSE_EMPTY
    fake_post = MagicMock()
    fake_post.read.return_value = b"{}"

    with patch(
        FETCH_URL_METHOD,
        side_effect=[
            (fake_get, {"status": 200, "msg": "OK"}),
            (fake_post, {"status": 201, "msg": "Created"}),
        ],
    ) as mock_fetch_url:
        set_module_args({**BASE_ARGS, "state": "present"})
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
            assert result["status_code"] == 201
        assert mock_fetch_url.call_count == 2

        get_call = mock_fetch_url.call_args_list[0]
        assert get_call[0][1] == "https://example.com/api/v1/links?link_object=Ticket&link_object_value=5"
        assert get_call[1]["method"] == "GET"

        post_call = mock_fetch_url.call_args_list[1]
        assert post_call[0][1] == "https://example.com/api/v1/links/add"
        assert post_call[1]["method"] == "POST"
        assert json.loads(post_call[1]["data"]) == {
            "link_type": "normal",
            "link_object_source": "Ticket",
            "link_object_source_number": "42001",
            "link_object_target": "Ticket",
            "link_object_target_value": 5,
        }


def test_add_link_already_exists():
    fake_get = MagicMock()
    fake_get.read.return_value = LINKS_RESPONSE_EXISTS

    with patch(
        FETCH_URL_METHOD,
        side_effect=[(fake_get, {"status": 200, "msg": "OK"})],
    ) as mock_fetch_url:
        set_module_args({**BASE_ARGS, "state": "present"})
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is False
        assert mock_fetch_url.call_count == 1


def test_remove_link_exists():
    fake_get = MagicMock()
    fake_get.read.return_value = LINKS_RESPONSE_EXISTS
    fake_delete = MagicMock()
    fake_delete.read.return_value = b"{}"

    with patch(
        FETCH_URL_METHOD,
        side_effect=[
            (fake_get, {"status": 200, "msg": "OK"}),
            (fake_delete, {"status": 200, "msg": "OK"}),
        ],
    ) as mock_fetch_url:
        set_module_args({**BASE_ARGS, "state": "absent"})
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
            assert result["status_code"] == 200
        assert mock_fetch_url.call_count == 2

        delete_call = mock_fetch_url.call_args_list[1]
        assert delete_call[0][1] == "https://example.com/api/v1/links/remove"
        assert delete_call[1]["method"] == "DELETE"
        # DELETE needs link_object_source_value (internal ID=41), not source_number
        assert json.loads(delete_call[1]["data"]) == {
            "link_type": "normal",
            "link_object_source": "Ticket",
            "link_object_source_value": 41,
            "link_object_target": "Ticket",
            "link_object_target_value": 5,
        }


def test_remove_link_not_existing():
    fake_get = MagicMock()
    fake_get.read.return_value = LINKS_RESPONSE_EMPTY

    with patch(
        FETCH_URL_METHOD,
        side_effect=[(fake_get, {"status": 200, "msg": "OK"})],
    ) as mock_fetch_url:
        set_module_args({**BASE_ARGS, "state": "absent"})
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is False
        assert mock_fetch_url.call_count == 1


def test_add_link_default_link_type():
    fake_get = MagicMock()
    fake_get.read.return_value = LINKS_RESPONSE_EMPTY
    fake_post = MagicMock()
    fake_post.read.return_value = b"{}"

    with patch(
        FETCH_URL_METHOD,
        side_effect=[
            (fake_get, {"status": 200, "msg": "OK"}),
            (fake_post, {"status": 201, "msg": "Created"}),
        ],
    ) as mock_fetch_url:
        args = {k: v for k, v in BASE_ARGS.items() if k != "link_type"}
        set_module_args(args)
        try:
            zammad_ticket_link.main()
        except AnsibleExitJson as e:
            result = e.args[0]
            assert result["changed"] is True
        assert mock_fetch_url.call_count == 2
        post_call = mock_fetch_url.call_args_list[1]
        assert json.loads(post_call[1]["data"])["link_type"] == "normal"
