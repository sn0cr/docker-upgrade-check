#!/usr/bin/env python3
# Example code to interface Docker api from
# https://gist.github.com/robv8r/fa66f5e0fdf001f425fe9facf2db6d49

# Copyright 2020-2023 Sn0cr
# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# This script ignores all non-semver version tags (see `parse_tags` if you want
# to change this -- they are ignored as they are not valid semver tags)

from typing import List, Optional
import requests
from semver import VersionInfo, compare

VERSION = VersionInfo.parse("1.0.0")
REGISTRY_URL = "https://registry-1.docker.io"

def get_docker_token(image_name):
    token_url = "https://auth.docker.io/token"
    params = {"service": "registry.docker.io", "scope": f"repository:{image_name}:pull"}
    try:
        result_json = requests.get(token_url, params=params).json()
        if "token" in result_json:
            return result_json["token"]
        else:
            return None
    except ValueError as ex:
        print("Docker API did not return JSON: " + str(ex))

def get_paginated_tags(url_suffix: str, headers:dict[str, str]) -> tuple[List[str], Optional[dict[str, str]]]:
    result = requests.get(REGISTRY_URL + url_suffix, headers=headers)
    result.raise_for_status()
    result_json = result.json()
    return result_json['tags'], result.links.get("next")

def list_tags(image_name: str, number_of_tags: int=100) -> List[str]:
    list_url = f"/v2/{image_name}/tags/list?n={number_of_tags}"
    token = get_docker_token(image_name)
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    tags: List[str] = []
    try:
        new_tags, next_page = get_paginated_tags(list_url, headers=headers)
        tags.extend(new_tags)
        while next_page:
            new_tags, next_page = get_paginated_tags(next_page['url'], headers=headers)
            tags.extend(new_tags)

    except ValueError as ex:
        print("Docker API did not return JSON: " + str(ex))

    return tags


def parse_tags(image_tags: List[str]) -> List[str]:
    from functools import cmp_to_key
    tags_parsed: List[str] = []
    for tag in image_tags:
        tag = tag.replace(".ce.", "+")
        if VersionInfo.isvalid(tag):
            tags_parsed.append(tag)
    tags_parsed.sort(key=cmp_to_key(compare))
    return tags_parsed

def most_recent_tag(image_name: str) -> str:
    tags = list_tags(image_name, number_of_tags=100)
    return parse_tags(tags)[-1]

if __name__ == "__main__":
    print(most_recent_tag("gitlab/gitlab-ce"))