#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["tencentcloud"]

from logging import debug, info, warning, error
from .tencentcloud_common import tencentcloud_common

class tencentcloud(tencentcloud_common):
    def request(self, action: str, params: dict = None):
        return self.tencentcloud_request("dnspod.tencentcloudapi.com", action, "2021-03-23", params)

    def search_recordid(self, sub_domain: str, domain: str) -> int:
        domainPunycode = self.domain2punycode(sub_domain)
        params = {
            "Domain": domain,
            "Limit": 1000
        }
        for i in self.request("DescribeRecordList", params)["RecordList"]:
            if self.domain2punycode(i["Name"]) == domainPunycode:
                return i["RecordId"]
        debug("无法搜索到前缀%s", sub_domain)
        return None

    def update_record(self, sub_domain: str, domain: str, record_type: str, value: str, /, **params):
        if record_type not in ["A", "SRV"]:
            raise ValueError(
                "不支持记录类型%s" % record_type
            )
        payload = {
            "Domain": domain,
            "SubDomain": sub_domain,
            "RecordType": record_type,
            "RecordLine": "默认",
        }
        if record_type == "A":
            payload["Value"] = value
        elif record_type == "SRV":
            payload["Value"] = f'{params.get("priority", 10)} {params.get("weight", 0)} {params["port"]} {value}.'
        recordid = self.search_recordid(sub_domain, domain)
        if recordid is None: # 新建
            return self.request("CreateRecord", params)
        else: # 更新
            payload["RecordId"] = recordid
            return self.request("ModifyRecord", params)

    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        self.update_record(sub_domain, domain, "A", ip)
        self.update_record(srv_prefix + sub_domain, domain, "SRV", f"{sub_domain}.{domain}", port=port)
