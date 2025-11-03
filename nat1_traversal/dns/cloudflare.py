#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://developers.cloudflare.com/api/resources/dns/subresources/records/
# https://developers.cloudflare.com/api/resources/zones/

__author__ = "Guation"
__all__ = ["update_record", "init"]

import requests, json
from logging import debug, info, warning, error
from .util import USER_AGENT, domain2punycode

__id: str = None
__token: str = None

def init(id: str, token: str):
    global __id, __token
    __id = id
    __token = token

def request(method: str, action: str, params: dict = None):
    global __id, __token
    if __id is None:
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer " + __token,
            "UserAgent": USER_AGENT,
        }
    else:
        headers = {
            "Content-type": "application/json",
            "X-Auth-Email": __id,
            "X-Auth-Key": __token,
            "UserAgent": USER_AGENT,
        }
    debug("method=%s, action=%s, params=%s, headers=%s", method, action, params, headers)
    try:
        response = requests.request(method, "https://api.cloudflare.com/client/v4" + action, json=params, headers=headers)
        r = response.content
        if response.status_code != 200:
            raise ValueError(
                'action=%s, status_code=%d, response=%s' % (action, response.status_code, r)
            )
        else:
            j = json.loads(r)
            if j.get("success"):
                debug("action=%s, response=%s", action, j)
                return j["result"]
            else:
                raise ValueError(
                    'action=%s, response=%s' % (action, j)
                )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            "%s 请求失败" % action
        ) from e

def search_zoneid(domain: str) -> str:
    domainPunycode = domain2punycode(domain)
    for i in request("GET", "/zones"):
        if domain2punycode(i["name"]) == domainPunycode:
            return i["id"]
    raise ValueError(
        "无法搜索到域名%s" % domain
    )

def search_recordid(sub_domain: str, zoneid: str) -> str:
    domainPunycode = domain2punycode(sub_domain)
    for i in request("GET", "/zones/%s/dns_records" % zoneid):
        if domain2punycode(i["name"]) == domainPunycode:
            return i["id"]
    debug("无法搜索到前缀%s", sub_domain)
    return None

def update_record(sub_domain: str, domain: str, record_type: str, value: str, /, **params):
    if record_type not in ["A", "SRV"]:
        raise ValueError(
            "不支持记录类型%s" % record_type
        )
    sub_domain = f"{sub_domain}.{domain}"
    payload = {
        "name": sub_domain,
        "proxied": False,
        "type": record_type,
    }
    if record_type == "A":
        payload.update({
            "content": value,
        })
    elif record_type == "SRV":
        payload.update({
            "data":{
                "priority": params.get("priority", 10),
                "weight": params.get("weight", 0),
                "port": params["port"],
                "target": f"{value}.{domain}",
            }
        })
    zoneid = search_zoneid(domain)
    recordid = search_recordid(sub_domain, zoneid)
    if recordid is None: # 新建
        return request("POST", "/zones/%s/dns_records" % zoneid, payload)
    else: # 更新
        return request("PATCH", "/zones/%s/dns_records/%s" % (zoneid, recordid), payload)
