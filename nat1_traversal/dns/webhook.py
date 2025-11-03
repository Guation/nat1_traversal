#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["update_record", "init"]

import requests, json
from logging import debug, info, warning, error
from .util import USER_AGENT, domain2punycode

__url: str = None
__token: str = None

def init(url: str, token: str):
    global __url, __token
    __url = url
    __token = token

def request(method: str, params: dict = None):
    global __token
    headers = {
        "Content-type": "application/json",
        "UserAgent": USER_AGENT,
    }
    if __token is not None:
        headers["Authorization"] = "Bearer " + __token
    debug("method=%s, url=%s, params=%s, headers=%s", method, __url, params, headers)
    try:
        response = requests.request(method, __url, json=params, headers=headers)
        r = response.content
        if response.status_code != 200:
            raise ValueError(
                '服务器拒绝了请求：url=%s, status_code=%d, response=%s' % (__url, response.status_code, r)
            )
        else:
            j = json.loads(r)
            debug("url=%s, response=%s", __url, j)
            return j
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            "%s 请求失败" % __url
        ) from e

def update_record(sub_domain: str, domain: str, record_type: str, value: str, /, **params):
    if record_type not in ["A", "SRV"]:
        raise ValueError(
            "不支持记录类型%s" % record_type
        )
    payload = {
        "name": sub_domain,
        "data": value,
        "type": record_type,
        "domain": domain,
    }
    if record_type == "SRV":
        payload.update({
            "priority": params.get("priority", 10),
            "weight": params.get("weight", 0),
            "port": params["port"],
        })
    return request("POST", payload)
