#!/usr/bin/env python3
# Example code to interface Docker api from
# https://gist.github.com/robv8r/fa66f5e0fdf001f425fe9facf2db6d49

# Copyright 2020 Sn0cr
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

import requests
from semver import VersionInfo, compare

VERSION = VersionInfo.parse("1.0.0")

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
        print("Docker API did not return JSON: " + ex)


def list_tags(image_name, number_of_tags=25):
    list_url = f"https://registry-1.docker.io/v2/{image_name}/tags/list"
    if number_of_tags:
        list_url += f"?n={number_of_tags}"
    token = get_docker_token(image_name)
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    try:
        result = requests.get(list_url, headers=headers)
        result_json = result.json()
        return result_json
    except ValueError as ex:
        print("Docker API did not return JSON: " + ex)


def parse_tags(image_tags):
    from functools import cmp_to_key
    tags = image_tags["tags"]
    tags_parsed = []
    for tag in tags:
        tag = tag.replace(".ce.", "+")
        if VersionInfo.isvalid(tag):
            tags_parsed.append(tag)
    tags_parsed.sort(key=cmp_to_key(compare))
    return tags_parsed

def most_recent_tag(image_name):
    tags = list_tags(image_name)
    return parse_tags(tags)[-1]

if __name__ == "__main__":
    print(most_recent_tag("gitlab/gitlab-ce"))