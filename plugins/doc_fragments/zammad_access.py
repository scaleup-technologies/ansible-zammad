# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r"""options:
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
        required: false
      api_secret:
        description:
          - The API secret or password for the specified user. This value is hidden in logs.
        type: str
        required: false
      api_token:
        description:
          - The API token used to authenticate with the Zammad API.
        required: false
        type: str
"""
