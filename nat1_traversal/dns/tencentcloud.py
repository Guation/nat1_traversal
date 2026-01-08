#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["update_record", "init"]

import time, hashlib, hmac, requests, json
from logging import debug, info, warning, error
from .util import USER_AGENT, domain2punycode

__id: str = None
__token: str = None

def init(id: str, token: str):
    global __id, __token
    __id = id
    __token = token

def hmac_sha256(key: bytes, data: str) -> bytes:
    return hmac.new(key, data.encode("utf-8"), hashlib.sha256).digest()

def request(action: str, params: dict = None):
    timestamp = int(time.time())
    date = time.strftime('%Y-%m-%d', time.gmtime(timestamp))
    headers = {
        "content-type": "application/json",
        "host": "dnspod.tencentcloudapi.com",
        "x-tc-action": action,
        "x-tc-version": "2021-03-23",
        "x-tc-timestamp": str(timestamp)
    }
    headers = dict(sorted(headers.items()))
    canonical_headers = "\n".join(f"{k}:{v.lower()}" for k, v in headers.items()) + "\n"
    signed_headers = ";".join(headers.keys())
    params_string = json.dumps(params, separators=(',', ":"))
    canonical_request = "\n".join(["POST", "/", "", canonical_headers, signed_headers, hashlib.sha256(params_string.encode("utf-8")).hexdigest()])
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    secretSigning = hmac_sha256(hmac_sha256(hmac_sha256(b"TC3" + __token.encode("utf-8"), date), "dnspod"), "tc3_request")
    credentialScope = f"{date}/dnspod/tc3_request"
    signature = hmac_sha256(secretSigning, f"TC3-HMAC-SHA256\n{timestamp}\n{credentialScope}\n{hashed_canonical_request}").hex().lower()
    headers["Authorization"] = f"TC3-HMAC-SHA256 Credential={__id}/{credentialScope}, SignedHeaders={signed_headers}, Signature={signature}"
    headers["User-Agent"] = USER_AGENT
    debug("action=%s, params=%s, headers=%s", action, params, headers)
    try:
        response = requests.request("POST", f"https://{headers['host']}/", headers=headers, data=params_string)
        r = response.content
        if response.status_code != 200:
            raise ValueError(
                '服务器拒绝了请求：action=%s, status_code=%d, response=%s' % (action, response.status_code, r)
            )
        else:
            j = json.loads(r)["Response"]
            if "Error" in j:
                raise ValueError(
                    '服务器返回错误：action=%s, response=%s' % (action, j)
                )
            else:
                debug("action=%s, response=%s", action, j)
                return j
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            "%s 请求失败" % action
        ) from e

def search_recordid(sub_domain: str, domain: str) -> int:
    domainPunycode = domain2punycode(sub_domain)
    params = {
        "Domain": domain,
        "Limit": 1000
    }
    for i in request("DescribeRecordList", params)["RecordList"]:
        if domain2punycode(i["Name"]) == domainPunycode:
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
