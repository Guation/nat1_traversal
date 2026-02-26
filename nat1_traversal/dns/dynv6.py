#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://dynv6.github.io/api-spec/

__author__ = "Guation"
__all__ = ["dynv6"]

import requests, json
from nat1_traversal.dns.dns_base import dns_base
from logging import debug, info, warning, error

class dynv6(dns_base):
    def request(self, method: str, action: str, params: dict = None):
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer " + self.token,
            "User-Agent": self.USER_AGENT,
        }
        debug("method=%s, action=%s, params=%s, headers=%s", method, action, params, headers)
        try:
            response = requests.request(method, "https://dynv6.com/api/v2" + action, json=params, headers=headers, timeout=15.0)
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
        except requests.Timeout:
            raise ValueError(
                "%s 请求超时" % action
            ) from e
        except Exception as e:
            raise ValueError(
                "%s 请求失败" % action
            ) from e

    def search_zoneid(self, domain: str) -> int:
        domainPunycode = self.domain2punycode(domain)
        for i in self.request("GET", "/zones"):
            if self.domain2punycode(i["name"]) == domainPunycode:
                return i["id"]
        raise ValueError(
            "无法搜索到域名%s" % domain
        )

    def search_recordid(self, sub_domain: str, zoneid: int) -> int:
        domainPunycode = self.domain2punycode(sub_domain)
        for i in self.request("GET", "/zones/%d/records" % zoneid):
            if self.domain2punycode(i["name"]) == domainPunycode:
                return i["id"]
        debug("无法搜索到前缀%s", sub_domain)
        return None

    def update_record(self, sub_domain: str, zoneid: int, record_type: str, value: str, /, **params):
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
        recordid = self.search_recordid(sub_domain, zoneid)
        if recordid is None: # 新建
            return self.request("POST", "/zones/%d/records" % zoneid, payload)
        else: # 更新
            payload.update({
                "id": recordid,
                "zoneID": zoneid,
            })
            return self.request("PATCH", "/zones/%d/records/%d" % (zoneid, recordid), payload)

    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        zoneid = self.search_zoneid(domain)
        self.update_record(sub_domain, zoneid, "A", ip)
        self.update_record(srv_prefix + sub_domain, zoneid, "SRV", sub_domain, port=port)
