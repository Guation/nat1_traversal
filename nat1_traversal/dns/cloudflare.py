#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://developers.cloudflare.com/api/resources/dns/subresources/records/
# https://developers.cloudflare.com/api/resources/zones/

__author__ = "Guation"
__all__ = ["cloudflare"]

import requests, json
from nat1_traversal.dns.dns_base import dns_base
from logging import debug, info, warning, error

class cloudflare(dns_base):
    def request(self, method: str, action: str, params: dict = None):
        if self.id is None:
            headers = {
                "Content-type": "application/json",
                "Authorization": "Bearer " + self.token,
                "UserAgent": self.USER_AGENT,
            }
        else:
            headers = {
                "Content-type": "application/json",
                "X-Auth-Email": self.id,
                "X-Auth-Key": self.token,
                "User-Agent": self.USER_AGENT,
            }
        debug("method=%s, action=%s, params=%s, headers=%s", method, action, params, headers)
        try:
            response = requests.request(method, "https://api.cloudflare.com/client/v4" + action, json=params, headers=headers)
            r = response.content
            if response.status_code != 200:
                raise ValueError(
                    '服务器拒绝了请求：action=%s, status_code=%d, response=%s' % (action, response.status_code, r)
                )
            else:
                j = json.loads(r)
                if "success" in j:
                    debug("action=%s, response=%s", action, j)
                    return j["result"]
                else:
                    raise ValueError(
                        '服务器返回错误：action=%s, response=%s' % (action, j)
                    )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                "%s 请求失败" % action
            ) from e

    def search_zoneid(self, domain: str) -> str:
        domainPunycode = self.domain2punycode(domain)
        for i in self.request("GET", "/zones"):
            if self.domain2punycode(i["name"]) == domainPunycode:
                return i["id"]
        raise ValueError(
            "无法搜索到域名%s" % domain
        )

    def search_recordid(self, sub_domain: str, zoneid: str) -> str:
        domainPunycode = self.domain2punycode(sub_domain)
        for i in self.request("GET", "/zones/%s/dns_records" % zoneid):
            if self.domain2punycode(i["name"]) == domainPunycode:
                return i["id"]
        debug("无法搜索到前缀%s", sub_domain)
        return None

    def update_record(self, full_domain: str, zoneid: str, record_type: str, value: str, /, **params):
        if record_type not in ["A", "SRV"]:
            raise ValueError(
                "不支持记录类型%s" % record_type
            )
        payload = {
            "name": full_domain,
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
                    "target": value,
                }
            })
        recordid = self.search_recordid(full_domain, zoneid)
        if recordid is None: # 新建
            return self.request("POST", "/zones/%s/dns_records" % zoneid, payload)
        else: # 更新
            return self.request("PATCH", "/zones/%s/dns_records/%s" % (zoneid, recordid), payload)

    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        zoneid = self.search_zoneid(domain)
        self.update_record(f"{sub_domain}.{domain}", zoneid, "A", ip)
        self.update_record(f"{srv_prefix}{sub_domain}.{domain}", zoneid, "SRV", f"{sub_domain}.{domain}", port=port)
