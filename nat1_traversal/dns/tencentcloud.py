#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["update_record", "init"]

from tencentcloud.common.common_client import CommonClient
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from logging import debug, info, warning, error
from .UserAgent import USER_AGENT

__id: str = None
__token: str = None

def init(id: str, token: str):
    global __id, __token
    __id = id
    __token = token

def request(action: str, params: dict = None):
    headers = {
        "UserAgent": USER_AGENT,
    }
    cred = credential.Credential(__id, __token)
    httpProfile = HttpProfile()
    httpProfile.endpoint = "dnspod.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    common_client = CommonClient("dnspod", "2021-03-23", cred, "", profile=clientProfile)
    debug("action=%s, params=%s", action, params)
    try:
        return common_client.call_json("DescribeRecordList", params, headers)["Response"]
    except TencentCloudSDKException as e:
        raise ValueError(
            "%s 请求失败" % action
        ) from e

def search_recordid(sub_domain: str, domain: str) -> int:
    params = {
        "Domain": domain,
        "Limit": 1000
    }
    for i in request("DescribeRecordList", params)["RecordList"]:
        if sub_domain == i["Name"]:
            return i["RecordId"]
    debug("无法搜索到前缀%s", sub_domain)
    return None

def update_record(sub_domain: str, domain: str, record_type: str, value: str, /, **params):
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
        payload["Value"] = f'{params.get("priority", 10)} {params.get("weight", 0)} {params["port"]} {value}.{domain}.'
    recordid = search_recordid(sub_domain, domain)
    if recordid is None: # 新建
        return request("CreateRecord", params)
    else: # 更新
        payload["RecordId"] = recordid
        return request("ModifyRecord", params)
