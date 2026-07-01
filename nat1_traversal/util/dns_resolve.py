#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import requests
from logging import debug, info, warning, error

def resolve(qname: str, qtype: str) -> list[dict]:
    for _ in range(3):
        try:
            response = requests.request("GET", "https://223.5.5.5/resolve", params={"name": qname, "type": qtype}, timeout=5.0)
            if response.status_code != 200:
                error("dns服务器拒绝了请求 %d", response.status_code)
                debug(response.text)
                return []
            j = response.json() # type: dict
            debug("qname=%s, qtype=%s, response=%s", qname, qtype, j)
            if j.get("Status") != 0:
                return []
            qtype = j["Question"]["type"]
            return list(filter(lambda x: x["type"] == qtype, j.get("Answer", [])))
        except requests.exceptions.RequestException:
            debug("dns请求失败", stack_info=True)
            continue
    return []
