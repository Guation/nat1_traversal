#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://github.com/MikeWang000000/Natter/blob/master/natter-check/natter-check.py
# https://blog.csdn.net/yuzhenchao1980/article/details/135756786

import os, socket, struct, traceback
from logging import debug, info, warning, error

MTU         = 1500
STUN_HOST   = "stun.hot-chilli.net"
STUN_PORT   = 3478
MAGIC_COOKIE    = 0x2112A442
BIND_REQUEST    = 0x0001
BIND_RESPONSE   = 0x0101
FAMILY_IPV4     = 0x01
FAMILY_IPV6     = 0x02
CHANGE_PORT     = 0x0002
CHANGE_IP       = 0x0004
ATTRIB_MAPPED_ADDRESS      = 0x0001
ATTRIB_CHANGE_REQUEST      = 0x0003
ATTRIB_XOR_MAPPED_ADDRESS  = 0x0020
ATTRIB_OTHER_ADDRESS       = 0x802C

def _random_tran_id():
    # type: () -> bytes
    # Compatible with rfc3489, rfc5389 and rfc8489
    return struct.pack("!L", MAGIC_COOKIE) + os.urandom(12)

def _pack_stun_message(msg_type, tran_id, payload = b""):
    # type: (bytes, bytes, bytes) -> bytes
    return struct.pack("!HH", msg_type, len(payload)) + tran_id + payload

def _unpack_stun_message(data):
    # type: (bytes) -> tuple[bytes, bytes, bytes]
    msg_type, msg_length = struct.unpack("!HH", data[:4])
    tran_id = data[4:20]
    payload = data[20:20 + msg_length]
    return msg_type, tran_id, payload

def _extract_mapped_addr(payload):
    # type: (bytes) -> socket._RetAddress
    while payload:
        attrib_type, attrib_length = struct.unpack("!HH", payload[:4])
        attrib_value = payload[4:4 + attrib_length]
        payload = payload[4 + attrib_length:]
        if attrib_type == ATTRIB_MAPPED_ADDRESS:
            _, family, port = struct.unpack("!BBH", attrib_value[:4])
            if family == FAMILY_IPV4:
                ip = socket.inet_ntoa(attrib_value[4:8])
                return ip, port
        elif attrib_type == ATTRIB_XOR_MAPPED_ADDRESS:
            # rfc5389 and rfc8489
            _, family, xor_port = struct.unpack("!BBH", attrib_value[:4])
            if family == FAMILY_IPV4:
                xor_iip, = struct.unpack("!L", attrib_value[4:8])
                ip = socket.inet_ntoa(struct.pack("!L", MAGIC_COOKIE ^ xor_iip))
                port = (MAGIC_COOKIE >> 16) ^ xor_port
                return ip, port
    return None

def _extract_other_addr(payload):
    # type: (bytes) -> socket._RetAddress
    while payload:
        attrib_type, attrib_length = struct.unpack("!HH", payload[:4])
        attrib_value = payload[4:4 + attrib_length]
        payload = payload[4 + attrib_length:]
        if attrib_type == ATTRIB_OTHER_ADDRESS:
            _, family, port = struct.unpack("!BBH", attrib_value[:4])
            if family == FAMILY_IPV4:
                ip = socket.inet_ntoa(attrib_value[4:8])
                return ip, port
    return None

def new_tcp_socket():
    # type: () -> socket.socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_REUSEADDR"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return sock

def single_test(stun, source, timeout = 3):
    # type: (socket._Address, socket._Address, int) -> tuple[socket._RetAddress, socket._RetAddress, socket._RetAddress, socket._RetAddress]
    # rfc5389 and rfc8489 only
    tran_id = _random_tran_id()
    with new_tcp_socket() as sock:
        sock.settimeout(timeout)
        try:
            sock.bind(source)
        except OSError as e:
            raise ValueError(
                "无法绑定到指定地址 %s" % source
            ) from e
        try:
            sock.connect(stun)
        except ConnectionError as e:
            raise ValueError(
                "无法连接到stun服务器"
            ) from e
        data = _pack_stun_message(BIND_REQUEST, tran_id)
        sock.sendall(data)
        try:
            buf = sock.recv(MTU)
        except TimeoutError as e:
            raise ValueError(
                "未从stun服务器收到有效信息，请尝试关闭透明代理后重试。"
            ) from e
        msg_type, msg_id, payload = _unpack_stun_message(buf)
        if tran_id == msg_id and msg_type == BIND_RESPONSE:
            source_addr = sock.getsockname()
            distination_addr = sock.getpeername()
            mapped_addr = _extract_mapped_addr(payload)
            other_addr = _extract_other_addr(payload)
            debug("source_addr=%s, distination_addr=%s, mapped_addr=%s, other_addr=%s", source_addr, distination_addr, mapped_addr, other_addr)
            return (source_addr, distination_addr, mapped_addr, other_addr)
        else:
            raise ValueError(
                "stun服务器响应异常 %s" % buf
            )

def get_self_ip_port(local):
    # type: (socket._Address) -> socket._RetAddress
    return single_test((STUN_HOST, STUN_PORT), local)[2]

def _loop_connect_test(local, remote, timeout = 1):
    # type: (socket._Address, socket._Address, int) -> bool
    import threading
    test_data = os.urandom(16)
    def helper():
        nonlocal test_data, remote, timeout
        try:
            with new_tcp_socket() as sock:
                sock.settimeout(timeout)
                sock.connect(remote)
                sock.send(test_data)
        except (socket.timeout, ConnectionError):
            pass

    try:
        with new_tcp_socket() as sock:
            sock.settimeout(timeout)
            sock.bind(local)
            sock.listen(1)
            threading.Thread(target=helper).start()
            sub_sock, _ = sock.accept()
            if sub_sock.recv(16) == test_data:
                return True
            else:
                return False
    except socket.timeout:
        return False

def _loop_connect(local, remote, timeout = 1):
    # type: (socket._Address, socket._Address, int) -> None
    try:
        with new_tcp_socket() as sock:
            sock.settimeout(timeout)
            sock.bind(local)
            sock.connect(remote)
    except socket.timeout:
        pass

def nat_type_test(local = None):
    # type: (socket._Address) -> tuple[bool, int]
    try:
        source_addr, distination_addr, mapped_addr, other_addr = single_test((STUN_HOST, STUN_PORT), ("0.0.0.0", 0) if local is None else local)
    except ValueError as e:
        error(e)
        debug(traceback.format_exc())
        return False, -1
    if source_addr == mapped_addr: # 内外地址一样，直接是公网IP
        info("OPEN INTERNET")
        return True, 0
    if other_addr is None:
        error("UnsupportedServer")
        return False, -1
    if distination_addr[0] == other_addr[0]:
        error("UnsupportedServer")
        return False, -1
    _, _, mapped_addr2, _ = single_test(other_addr, source_addr) # 使用同一端口连不同IP
    if mapped_addr == mapped_addr2: # 返回地址一样是锥形
        if _loop_connect_test(source_addr, mapped_addr): # 回环测试，能连进来是全锥
            if mapped_addr[1] == source_addr[1]: # 内外端口一样，可能是有公网IP（云服务器环境）
                test_arr = [single_test(distination_addr, (source_addr[0], 0)) for _ in range(3)] # 随机检测3个端口
                if len(set(x[0][1] for x in test_arr)) == 3 and all(x[0][1] == x[2][1] for x in test_arr): # 如果3个端口内外都相同就认为是有公网IP
                    info("OPEN INTERNET")
                    return True, 0
                else: # 不一样的话是映射巧合
                    info("FULL CONE")
                    return True, 1
            else:
                info("FULL CONE")
                return True, 1
        else: # 连不进来是防火墙阻断或者限制锥
            _loop_connect(source_addr, mapped_addr) # 本地端口往自己IP发一次请求
            if _loop_connect_test(source_addr, mapped_addr): # 此时能通是IP受限
                info("RESTRICTED CONE")
                return False, 2
            else: # 还是通不了是端口受限，或者防火墙
                info("PORT RESTRICTED CONE")
                return False, 3
    else: # 不一样是对称型
        info("SYMMETRIC")
        return False, 4
