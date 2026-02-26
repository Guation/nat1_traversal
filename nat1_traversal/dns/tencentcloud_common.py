#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["tencentcloud_common"]

import time, hashlib, hmac, requests, json
from nat1_traversal.dns.dns_base import dns_base
from logging import debug, info, warning, error

class tencentcloud_common(dns_base):
    def hmac_sha256(self, key: bytes, data: str) -> bytes:
        return hmac.new(key, data.encode("utf-8"), hashlib.sha256).digest()

    def tencentcloud_request(self, endpoint: str, action: str, version: str, params: dict):
        timestamp = int(time.time())
        date = time.strftime('%Y-%m-%d', time.gmtime(timestamp))
        product = endpoint.split(".")[0]
        headers = {
            "content-type": "application/json",
            "host": endpoint,
            "x-tc-action": action,
            "x-tc-version": version,
            "x-tc-timestamp": str(timestamp)
        }
        headers = dict(sorted(headers.items()))
        canonical_headers = "\n".join(f"{k}:{v.lower()}" for k, v in headers.items()) + "\n"
        signed_headers = ";".join(headers.keys())
        params_string = json.dumps(params)
        canonical_request = "\n".join(["POST", "/", "", canonical_headers, signed_headers, hashlib.sha256(params_string.encode("utf-8")).hexdigest()])
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        secretSigning = self.hmac_sha256(self.hmac_sha256(self.hmac_sha256(b"TC3" + self.token.encode("utf-8"), date), product), "tc3_request")
        credentialScope = f"{date}/{product}/tc3_request"
        signature = self.hmac_sha256(secretSigning, f"TC3-HMAC-SHA256\n{timestamp}\n{credentialScope}\n{hashed_canonical_request}").hex().lower()
        headers["Authorization"] = f"TC3-HMAC-SHA256 Credential={self.id}/{credentialScope}, SignedHeaders={signed_headers}, Signature={signature}"
        headers["User-Agent"] = self.USER_AGENT
        debug("action=%s, params=%s, headers=%s", action, params, headers)
        try:
            response = requests.request("POST", f"https://{headers['host']}/", headers=headers, data=params_string, timeout=15.0)
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
        except requests.Timeout:
            raise ValueError(
                "%s 请求超时" % action
            ) from e
        except Exception as e:
            raise ValueError(
                "%s 请求失败" % action
            ) from e
