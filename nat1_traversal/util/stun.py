#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://github.com/MikeWang000000/Natter/blob/master/natter-check/natter-check.py
# https://blog.csdn.net/yuzhenchao1980/article/details/135756786
# https://cloud.tencent.com.cn/developer/article/1934525
# https://cloud.tencent.com/developer/article/2419665
# https://cloud.tencent.com/developer/article/2419666

import os, socket, struct, traceback
import dns.resolver as resolver
from logging import debug, info, warning, error

MTU             = 1500
TCP_STUN_HOST   = "turn.cloud-rtc.com"
TCP_STUN_PORT   = 80
UDP_STUN_HOST   = "stun.douyucdn.cn"
UDP_STUN_PORT   = 18000
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

TYPE_TCP = 1
TYPE_UDP = 2

def _random_tran_id():
    # type: () -> bytes
    # Compatible with rfc3489, rfc5389 and rfc8489
    return struct.pack("!L", MAGIC_COOKIE) + os.urandom(12)

def _pack_stun_message(msg_type, tran_id, payload = b""):
    # type: (bytes, bytes, bytes) -> bytes
    return struct.pack("!HH", msg_type, len(payload)) + tran_id + payload

def _unpack_stun_message(data):
    # type: (bytes) -> tuple[bytes, bytes, bytes]
    if len(data) < 4:
        raise ValueError(
            "STUN数据包长度过短 %s" % data
        )
    msg_type, msg_length = struct.unpack("!HH", data[:4])
    tran_id = data[4:20]
    payload = data[20:20 + msg_length]
    if len(payload) != msg_length:
        raise ValueError(
            "STUN数据包已损坏 %s" % data
        )
    return msg_type, tran_id, payload

def _extract_mapped_addr(payload):
    # type: (bytes) -> socket._RetAddress
    try:
        while payload:
            attrib_type, attrib_length = struct.unpack("!HH", payload[:4])
            attrib_value = payload[4:4 + attrib_length]
            payload = payload[4 + attrib_length:]
            if attrib_type == ATTRIB_XOR_MAPPED_ADDRESS:
                # rfc5389 and rfc8489
                _, family, xor_port = struct.unpack("!BBH", attrib_value[:4])
                if family == FAMILY_IPV4:
                    xor_iip, = struct.unpack("!L", attrib_value[4:8])
                    ip = socket.inet_ntoa(struct.pack("!L", MAGIC_COOKIE ^ xor_iip))
                    port = (MAGIC_COOKIE >> 16) ^ xor_port
                    return ip, port
        return None
    except (struct.error, OSError) as e:
        raise ValueError(
            "无法从STUN中解析MAPPED_ADDRESS %s" % payload
        ) from e

def _extract_other_addr(payload):
    # type: (bytes) -> socket._RetAddress
    try:
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
    except (struct.error, OSError) as e:
        raise ValueError(
            "无法从STUN中解析OTHER_ADDRESS %s" % payload
        ) from e

def resolve_stun_ip(host: str):
    try:
        return [str(x.address) for x in resolver.resolve(host, "A")]
    except (resolver.dns.exception.DNSException, OSError):
        error("stun服务器地址解析失败\n%s" % traceback.format_exc())
        return []

def new_tcp_socket():
    # type: () -> socket.socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return sock

def new_tcp_socket_advanced(*, reuseport = False, family = socket.AF_INET):
    # type: (None, bool, int) -> socket.socket
    sock = socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if reuseport and hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return sock

def new_udp_socket():
    # type: () -> socket.socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    return sock

def new_udp_socket_advanced(*, reuseport = False, family = socket.AF_INET):
    # type: (None, bool, int) -> socket.socket
    sock = socket.socket(family, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if reuseport and hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    return sock

def tcp_single_test(stun, source, timeout = 3):
    # type: (socket._Address, socket._Address, int) -> tuple[socket._RetAddress, socket._RetAddress, socket._RetAddress, socket._RetAddress]
    # rfc5389 and rfc8489 only
    tran_id = _random_tran_id()
    with new_tcp_socket_advanced(reuseport=True) as sock:
        sock.settimeout(timeout)
        try:
            sock.bind(source)
        except OSError as e:
            raise ValueError(
                "无法绑定到指定地址 %s" % source
            ) from e
        try:
            sock.connect(stun)
        except OSError as e:
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
            debug("stun source_addr=%s, distination_addr=%s, mapped_addr=%s, other_addr=%s", source_addr, distination_addr, mapped_addr, other_addr)
            return (source_addr, distination_addr, mapped_addr, other_addr)
        else:
            raise ValueError(
                "stun服务器响应异常 %s" % buf
            )

def udp_single_test(stun, source, change_ip = False, change_port = False, timeout = 3, repeat = 3):
    # type: (socket._Address, socket._Address, bool, bool, int, int) -> tuple[socket._RetAddress, socket._RetAddress, socket._RetAddress, socket._RetAddress]
    # rfc5389 and rfc8489 only
    tran_id = _random_tran_id()
    with new_udp_socket_advanced(reuseport=True) as sock:
        sock.settimeout(timeout)
        try:
            sock.bind(source)
        except OSError as e:
            raise ValueError(
                "无法绑定到指定地址 %s" % source
            ) from e
        try:
            distination_addr = socket.getaddrinfo(*stun, family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)[0][4]
        except OSError as e:
            raise ValueError(
                "无法解析stun服务器"
            ) from e
        flags = 0
        if change_ip:
            flags |= CHANGE_IP
        if change_port:
            flags |= CHANGE_PORT
        if flags:
            payload = struct.pack("!HHL", ATTRIB_CHANGE_REQUEST, 0x4, flags)
            data = _pack_stun_message(BIND_REQUEST, tran_id, payload)
        else:
            data = _pack_stun_message(BIND_REQUEST, tran_id)
        for _ in range(repeat):
            sock.sendto(data, distination_addr)
        for _ in range(repeat * 2):
            try:
                buf, addr = sock.recvfrom(MTU)
                if change_ip ^ (addr[0] != distination_addr[0]) or change_port ^ (addr[1] != distination_addr[1]):
                    debug("drop CHANGE_IP=%s CHANGE_PORT=%s distination_addr=%s buf=%s addr=%s", change_ip, change_port, distination_addr, buf, addr)
                    continue
                break
            except TimeoutError as e:
                raise TimeoutError(
                    "未从stun服务器收到有效信息。"
                ) from e
        else:
            raise TimeoutError(
                "未从stun服务器收到有效信息。"
            ) 
        msg_type, msg_id, payload = _unpack_stun_message(buf)
        if tran_id == msg_id and msg_type == BIND_RESPONSE:
            source_addr = sock.getsockname()
            mapped_addr = _extract_mapped_addr(payload)
            other_addr = _extract_other_addr(payload)
            debug("stun source_addr=%s, distination_addr=%s, mapped_addr=%s, other_addr=%s", source_addr, distination_addr, mapped_addr, other_addr)
            return (source_addr, distination_addr, mapped_addr, other_addr)
        else:
            raise ValueError(
                "stun服务器响应异常 %s" % buf
            )

def get_self_ip_port(local, _type):
    # type: (socket._Address, int) -> socket._RetAddress
    if _type is TYPE_TCP:
        return tcp_single_test((TCP_STUN_HOST, TCP_STUN_PORT), local)[2]
    else:
        return udp_single_test((UDP_STUN_HOST, UDP_STUN_PORT), local)[2]

def addr_available(local, _type):
    # type: (socket._Address, int) -> socket._RetAddress
    with new_tcp_socket_advanced(reuseport=True) if _type is TYPE_TCP else new_udp_socket_advanced(reuseport=True) as sock:
        try:
            sock.bind(local)
        except OSError as e:
            raise ValueError(
                "无法绑定到指定地址 %s:%d" % local
            ) from e
        return sock.getsockname()

def _loop_connect_test(local, remote):
    # type: (socket._Address, socket._Address) -> bool
    import threading
    test_data = os.urandom(16)
    def helper():
        nonlocal test_data, remote
        try:
            with new_tcp_socket() as sock:
                sock.settimeout(1)
                sock.connect(remote)
                sock.send(test_data)
        except (socket.timeout, ConnectionError):
            debug(traceback.format_exc())

    try:
        with new_tcp_socket() as sock:
            sock.settimeout(2)
            sock.bind(local)
            sock.listen(1)
            threading.Thread(target=helper).start()
            sub_sock, _ = sock.accept()
            if sub_sock.recv(16) == test_data:
                return True
            else:
                return False
    except socket.timeout:
        debug(traceback.format_exc())
        return False

def _loop_connect(local, remote, timeout = 1):
    # type: (socket._Address, socket._Address, int) -> None
    try:
        with new_tcp_socket() as sock:
            sock.settimeout(timeout)
            sock.bind(local)
            sock.connect(remote)
    except socket.timeout:
        debug(traceback.format_exc())

def tcp_nat_type_test(local):
    # type: (socket._Address) -> tuple[bool, int]
    stun_address = resolve_stun_ip(TCP_STUN_HOST)
    if len(stun_address) < 2:
        error("UnsupportedServer")
        return False, -1
    try:
        source_addr, _, mapped_addr, _ = tcp_single_test((stun_address[0], TCP_STUN_PORT), ("0.0.0.0", 0) if local is None else local)
    except ValueError as e:
        error(e)
        debug(traceback.format_exc())
        return False, -1
    if source_addr == mapped_addr: # 内外地址一样，直接是公网IP
        info("OPEN INTERNET")
        return True, 0
    _, _, mapped_addr2, _ = tcp_single_test((stun_address[1], TCP_STUN_PORT), source_addr) # 使用同一端口连不同IP
    if mapped_addr == mapped_addr2: # 返回地址一样是锥形
        info("Endpoint-Independent Mapping")
        if _loop_connect_test(source_addr, mapped_addr): # 回环测试，能连进来是全锥
            if mapped_addr[1] == source_addr[1]: # 内外端口一样，可能是有公网IP（云服务器环境）
                info("Endpoint-Independent Filtering")
                test_arr = [tcp_single_test((stun_address[0], TCP_STUN_PORT), (source_addr[0], 0)) for _ in range(3)] # 随机检测3个端口
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
                info("Address-Dependent Filtering")
                info("RESTRICTED CONE")
                return False, 2
            else: # 还是通不了是端口受限，或者防火墙
                info("Address and Port-Dependent Filtering")
                info("PORT RESTRICTED CONE")
                return False, 3
    else: # 不一样是对称型
        info("Address and Port-Dependent Mapping")
        info("SYMMETRIC")
        return False, 4

def udp_nat_type_test(local):
    # type: (socket._Address) -> tuple[bool, int]
    stun_address = resolve_stun_ip(UDP_STUN_HOST)
    if len(stun_address) < 2:
        error("UnsupportedServer")
        return False, -1
    try:
        source_addr, _, mapped_addr, _ = udp_single_test((stun_address[0], UDP_STUN_PORT), ("0.0.0.0", 0) if local is None else local)
    except ValueError as e:
        error(e)
        debug(traceback.format_exc())
        return False, -1
    if source_addr == mapped_addr: # 内外地址一样，直接是公网IP
        info("OPEN INTERNET")
        return True, 0
    _, _, mapped_addr2, _ = udp_single_test((stun_address[1], UDP_STUN_PORT), source_addr) # 使用同一端口连不同IP
    if mapped_addr == mapped_addr2: # 返回地址一样是锥形
        info("Endpoint-Independent Mapping")
        try:
            udp_single_test((stun_address[0], UDP_STUN_PORT), source_addr, change_ip=True, change_port=True)
            info("Endpoint-Independent Filtering")# 换了IP能连进来是全锥
            test_arr = [udp_single_test((stun_address[0], UDP_STUN_PORT), (source_addr[0], 0)) for _ in range(3)] # 随机检测3个端口
            if len(set(x[0][1] for x in test_arr)) == 3 and all(x[0][1] == x[2][1] for x in test_arr): # 如果3个端口内外都相同就认为是有公网IP
                info("OPEN INTERNET")
                return True, 0
            else: # 不一样的话是映射巧合
                info("FULL CONE")
                return True, 1
        except TimeoutError as e:
            debug(e)
            debug(traceback.format_exc())
        except ValueError as e:
            error(e)
            debug(traceback.format_exc())
            return False, -1
        try:
            udp_single_test((stun_address[0], UDP_STUN_PORT), source_addr, change_port=True) # 换了端口能连进来的是IP限制锥
            info("Address-Dependent Filtering")
            info("RESTRICTED CONE")
            return False, 2
        except TimeoutError as e: # 还连不进来就是端口限制锥了
            debug(e)
            debug(traceback.format_exc())
            info("Address and Port-Dependent Filtering")
            info("PORT RESTRICTED CONE")
            return False, 3
        except ValueError as e:
            error(e)
            debug(traceback.format_exc())
            return False, -1
    else: # 不一样是对称型
        info("Address and Port-Dependent Mapping")
        info("SYMMETRIC")
        return False, 4

def nat_type_test(local, _type):
    # type: (socket._Address, int) -> tuple[bool, int]
    if _type is TYPE_TCP:
        return tcp_nat_type_test(local)
    else:
        return udp_nat_type_test(local)
