#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["edgeone"]

from logging import debug, info, warning, error
from .tencentcloud_common import tencentcloud_common

class edgeone(tencentcloud_common):
    def request(self, action: str, params: dict = None):
        return self.tencentcloud_request("teo.tencentcloudapi.com", action, "2022-09-01", params)

    def search_zoneid(self, domain: str) -> str:
        domainPunycode = self.domain2punycode(domain)
        for i in self.request("DescribeZones", {})["Zones"]:
            if self.domain2punycode(i["ZoneName"]) == domainPunycode:
                return i["ZoneId"]
        raise ValueError(
            "无法搜索到域名%s" % domain
        )

    def search_recordid(self, sub_domain: str, zoneid: str) -> str:
        domainPunycode = self.domain2punycode(sub_domain)
        params = {
            "ZoneId": zoneid,
            "Limit": 200
        }
        for i in self.request("DescribeAccelerationDomains", params)["AccelerationDomains"]:
            if self.domain2punycode(i["DomainName"]) == domainPunycode:
                return i["DomainName"]
        raise ValueError(
            "无法搜索到前缀%s" % sub_domain
        )

    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        if srv_prefix != "_web._tcp.":
            raise ValueError(
                "edgeone平台只支持type为web"
            )
        zoneid = self.search_zoneid(domain)
        recordid = self.search_recordid(f"{sub_domain}.{domain}", zoneid)
        payload = {
            "ZoneId": zoneid,
            "DomainName": recordid,
            "OriginInfo": {
                "OriginType": "IP_DOMAIN",
                "Origin": ip
            },
            "HttpOriginPort": port,
            "HttpsOriginPort": port,
        }
        return self.request("ModifyAccelerationDomain", payload)
