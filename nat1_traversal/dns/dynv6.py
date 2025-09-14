#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://dynv6.github.io/api-spec/

__author__ = "Guation"
__all__ = ["update_record", "init"]

import requests, json
from logging import debug, info, warning, error
from .UserAgent import USER_AGENT

__token: str = None

def init(id: str, token: str):
    global __token
    __token = token

def request(method: str, action: str, params: dict = None):
    global __token
    headers = {
        "Content-type": "application/json",
        "Authorization": "Bearer " + __token,
        "UserAgent": USER_AGENT,
    }
    debug("method=%s, action=%s, params=%s, headers=%s", method, action, params, headers)
    try:
        response = requests.request(method, "https://dynv6.com/api/v2" + action, json=params, headers=headers)
        r = response.content
        if response.status_code != 200:
            raise ValueError(
                '服务器拒绝了请求：action=%s, status_code=%d, response=%s' % (action, response.status_code, r)
            )
        else:
            j = json.loads(r)
            debug("action=%s, response=%s", action, j)
            return j
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            "%s 请求失败" % action
        ) from e

def search_zoneid(domain: str) -> int:
    domainPunycode1 = domain.encode('idna').decode('ascii')
    domainPunycode2 = domain.encode().decode('idna')
    for i in request("GET", "/zones"):
        if domainPunycode1 == i["name"] or domainPunycode2 == i["name"]:
            return i["id"]
    raise ValueError(
        "无法搜索到域名%s" % domain
    )

def search_recordid(sub_domain: str, zoneid: int) -> int:
    domainPunycode1 = sub_domain.encode('idna').decode('ascii')
    domainPunycode2 = sub_domain.encode().decode('idna')
    for i in request("GET", "/zones/%d/records" % zoneid):
        if domainPunycode1 == i["name"] or domainPunycode2 == i["name"]:
            return i["id"]
    debug("无法搜索到前缀%s", sub_domain)
    return None

def update_record(sub_domain: str, domain: str, record_type: str, value: str, /, **params):
    if record_type not in ["A", "SRV"]:
        raise ValueError(
            "不支持记录类型%s" % record_type
        )
    payload = {
        "name": sub_domain,
        "data": value,
        "type": record_type,
    }
    if record_type == "SRV":
        payload.update({
            "priority": params.get("priority", 10),
            "weight": params.get("weight", 0),
            "port": params["port"],
        })
    zoneid = search_zoneid(domain)
    recordid = search_recordid(sub_domain, zoneid)
    if recordid is None: # 新建
        return request("POST", "/zones/%d/records" % zoneid, payload)
    else: # 更新
        payload.update({
            "id": recordid,
            "zoneID": zoneid,
        })
        return request("PATCH", "/zones/%d/records/%d" % (zoneid, recordid), payload)
