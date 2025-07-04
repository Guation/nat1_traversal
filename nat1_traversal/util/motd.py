#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://github.com/FragLand/minestat/blob/master/Python/minestat/__init__.py

import socket, struct, json, traceback, requests
import dns.resolver as resolver
from logging import debug, info, warning, error
from .stun import new_tcp_socket

def unpack_varint(sock: socket.socket) -> int:
    """ Small helper method for unpacking an int from an varint (streamed from socket). """
    data = 0
    for i in range(5):
        ordinal = sock.recv(1)

        if len(ordinal) == 0:
            break

        byte = ord(ordinal)
        data |= (byte & 0x7F) << 7 * i

        if not byte & 0x80:
            break

    return data

def pack_varint(data) -> bytes:
    """ Small helper method for packing a varint from an int. """
    ordinal = b''

    while True:
        byte = data & 0x7F
        data >>= 7
        ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

        if data == 0:
            break

    return ordinal

def recv_exact(sock: socket.socket, size: int) -> bytearray:
    """
    Helper function for receiving a specific amount of data. Works around the problems of `socket.recv`.
    Throws a ConnectionAbortedError if the connection was closed while waiting for data.

    :param sock: Open socket to receive data from
    :param size: Amount of bytes of data to receive
    :return: bytearray with the received data
    """
    data = bytearray()

    while len(data) < size:
        temp_data = bytearray(sock.recv(size - len(data)))

      # If the connection was closed, `sock.recv` returns an empty string
        if not temp_data:
            raise ConnectionAbortedError

        data += temp_data

    return data

def description2str(data):
    # type: (dict | str) -> str
    if type(data) == str:
        return data
    out = data['text']
    if 'extra' in data:
        for i in data['extra']:
            out += description2str(i)
    return out

def srv_query(srv_prefix, address, port):
    # type: (str, str, int) -> tuple[str, int]
    try:
        srv_record = resolver.resolve(srv_prefix + address, "SRV")[0]
        debug("SRV record %s", srv_record)
        port = int(srv_record.port)
        address = str(srv_record.target)[:-1]
    except (resolver.dns.exception.DNSException, OSError):
        debug("query srv record fail.\n%s", traceback.format_exc())
    return (address, port)

def mcje_query(address, port):
    # type: (str, int) -> tuple[bool, str]
    """
    Method for querying a modern (MC Java >= 1.7) server with the SLP protocol.
    This protocol is based on encoded JSON, see the documentation at wiki.vg below
    for a full packet description.

    See https://wiki.vg/Server_List_Ping#Current
    """
    sock = new_tcp_socket()
    sock.settimeout(10)

    try:
        sock.connect((address, port))
    except socket.timeout:
        debug("connect timeout\n%s", traceback.format_exc())
        return False, 'timeout'
    except ConnectionRefusedError:
        debug("connect error\n%s", traceback.format_exc())
        return False, 'connect fail'
    except OSError:
        debug("os error\n%s", traceback.format_exc())
        return False, 'OSError'

    # Construct Handshake packet
    req_data = bytearray([0x00])
    # Add protocol version. If pinging to determine version, use `-1`
    req_data += bytearray([0xff, 0xff, 0xff, 0xff, 0x0f])
    # Add server address length
    req_data += pack_varint(len(address))
    # Server address. Encoded with UTF8
    req_data += bytearray(address, "utf8")
    # Server port
    req_data += struct.pack(">H", port)
    # Next packet state (1 for status, 2 for login)
    req_data += bytearray([0x01])

    # Prepend full packet length
    req_data = pack_varint(len(req_data)) + req_data

    # Now actually send the constructed client request
    sock.send(req_data)

    # Now send empty "Request" packet
    # varint len, 0x00
    sock.send(bytearray([0x01, 0x00]))

    # Do all the receiving in a try-catch, to reduce duplication of error handling
    try:
        # Receive answer: full packet length as varint
        packet_len = unpack_varint(sock)

        # Check if full packet length seems acceptable
        if packet_len < 3:
            debug('packet_len < 3')
            return False, 'packet_len < 3'

        # Receive actual packet id
        packet_id = unpack_varint(sock)

        # If we receive a packet with id 0x19, something went wrong.
        # Usually the payload is JSON text, telling us what exactly.
        # We could stop here, and display something to the user, as this is not normal
        # behaviour, maybe a bug somewhere here.

        # Instead I am just going to check for the correct packet id: 0x00
        if packet_id != 0:
            debug('packet_id != 0')
            return False, 'packet_id != 0'

        # Receive & unpack payload length
        content_len = unpack_varint(sock)

        # Receive full payload
        payload_raw = recv_exact(sock, content_len)

    except socket.timeout:
        debug("connect timeout\n%s", traceback.format_exc())
        return False, 'timeout'
    except (ConnectionResetError, ConnectionAbortedError):
        debug("connect error\n%s", traceback.format_exc())
        return False, 'ConnectionResetError, ConnectionAbortedError'
    except OSError:
        debug("os error\n%s", traceback.format_exc())
        return False, 'OSError'
    finally:
        sock.close()

    # Parse and save to object attributes
    try:
        payload_dict = json.loads(payload_raw)
        out_dict = {}
        out_dict["version"] = payload_dict["version"]
        out_dict["description"] = description2str(payload_dict["description"])
        out_dict["players"] = {"max": payload_dict["players"]["max"], "online": payload_dict["players"]["online"]}
        if "sample" in payload_dict["players"]:
            out_dict["players"]["list"] = list(sorted(i["name"] for i in payload_dict["players"]["sample"]))
        else:
            out_dict["players"]["list"] = []

        debug("server(%s:%s) motd %s", address, port, out_dict)
    except Exception:
        debug(traceback.format_exc())
        return False, "motd parse fail."

    return True, json.dumps(out_dict, ensure_ascii = False)

def tcp_query(address, port):
    # type: (str, int) -> tuple[bool, str]
    sock = new_tcp_socket()
    sock.settimeout(10)
    try:
        sock.connect((address, port))
    except socket.timeout:
        debug("connect timeout\n%s", traceback.format_exc())
        return False, 'timeout'
    except ConnectionRefusedError:
        debug("connect error\n%s", traceback.format_exc())
        return False, 'connect fail'
    except OSError:
        debug("os error\n%s", traceback.format_exc())
        return False, 'OSError'
    return True, 'port available confirm.'
