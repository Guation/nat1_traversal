#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://github.com/FragLand/minestat/blob/master/Python/minestat/__init__.py

import socket, struct, json, traceback, time, io, re
import dns.resolver as resolver
from logging import debug, info, warning, error
from .stun import new_tcp_socket, new_udp_socket, new_tcp_socket_advanced, new_udp_socket_advanced

RAKNET_MAGIC = bytearray([0x00, 0xff, 0xff, 0x00, 0xfe, 0xfe, 0xfe, 0xfe, 0xfd, 0xfd, 0xfd, 0xfd, 0x12, 0x34, 0x56, 0x78])
MOTD_INDEX = ["edition", "motd_1", "protocol_version", "version", "current_players", "max_players",
                  "server_uid", "motd_2", "gamemode", "gamemode_numeric", "port_ipv4", "port_ipv6"]
STRIP_MOTD = re.compile(r'§[0-9a-v]')


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

def srv_query(srv_prefix, address, port, default_port):
    # type: (str, str, int, int) -> tuple[str, int]
    if port != 0:
        return (address, port)
    try:
        srv_record = resolver.resolve(srv_prefix + address, "SRV")[0]
        debug("SRV record %s", srv_record)
        port = int(srv_record.port)
        address = str(srv_record.target)[:-1]
    except (resolver.dns.exception.DNSException, OSError):
        debug("query srv record fail.\n%s", traceback.format_exc())
        port = default_port
    return (address, port)

def mcje_query(address, port, family = socket.AF_INET):
    # type: (str, int, int) -> tuple[bool, str]
    """
    Method for querying a modern (MC Java >= 1.7) server with the SLP protocol.
    This protocol is based on encoded JSON, see the documentation at wiki.vg below
    for a full packet description.

    See https://minecraft.wiki/w/Java_Edition_protocol/Server_List_Ping#Current
    """
    sock = new_tcp_socket_advanced(family = family)
    sock.settimeout(5)

    try:
        sock.connect((address, port))
    except socket.gaierror:
        debug("DNS query failed\n%s", traceback.format_exc())
        return False, 'DNS query failed'
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
        out_dict["description"] = STRIP_MOTD.sub('', description2str(payload_dict["description"])).splitlines()
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
    sock.settimeout(5)
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

def mcbe_query(address, port, family = socket.AF_INET):
    # type: (str, int, int) -> tuple[bool, str]
    """
    Method for querying a Bedrock server (Minecraft PE, Windows 10 or Education Edition).
    The protocol is based on the RakNet protocol.

    See https://minecraft.wiki/w/RakNet#Unconnected_Ping

    Note: This method currently works as if the connection is handled via TCP (as if no packet loss might occur).
    Packet loss handling should be implemented (resending).
    """

    # Create socket with type DGRAM (for UDP)
    sock = new_udp_socket_advanced(family = family)
    sock.settimeout(10)

    try:
        sock.connect((address, port))
    except socket.timeout:
        debug("connect timeout\n%s", traceback.format_exc())
        return False, 'timeout'
    except OSError:
        debug("os error\n%s", traceback.format_exc())
        return False, 'OSError'

    # Construct the `Unconnected_Ping` packet
    # Packet ID - 0x01
    req_data = bytearray([0x01])
    # current unix timestamp in ms as signed long (64-bit) LE-encoded
    req_data += struct.pack("<q", int(time.time() * 1000))
    # RakNet MAGIC (0x00ffff00fefefefefdfdfdfd12345678)
    req_data += RAKNET_MAGIC
    # Client GUID - as signed long (64-bit) LE-encoded
    req_data += struct.pack("<q", 0x02)

    sock.send(req_data)

    # Do all the receiving in a try-catch, to reduce duplication of error handling

    # response packet:
    # byte - 0x1C - Unconnected Pong
    # long - timestamp
    # long - server GUID
    # 16 byte - magic
    # short - Server ID string length
    # string - Server ID string
    try:
        response_buffer, response_addr = sock.recvfrom(1024)
        response_stream = io.BytesIO(response_buffer)

        # Receive packet id
        packet_id = response_stream.read(1)

        # Response packet ID should always be 0x1c
        if packet_id != b'\x1c':
            debug(f"packet_id == {packet_id} != \\x1c")
            return False, "packet_id != \\x1c"

        # Receive (& ignore) response timestamp
        response_timestamp = struct.unpack("<q", response_stream.read(8))

        # Server GUID
        response_server_guid = struct.unpack("<q", response_stream.read(8))

        # Magic
        response_magic = response_stream.read(16)
        if response_magic != RAKNET_MAGIC:
            debug(f"response_magic == {response_magic} != RAKNET_MAGIC")
            return False, "response_magic != RAKNET_MAGIC"

        # Server ID string length
        response_id_string_length = struct.unpack(">h", response_stream.read(2))

        # Receive server ID string
        response_id_string = response_stream.read().decode("utf8")

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
    
    try:
        payload_dict = {e: f for e, f in zip(MOTD_INDEX, response_id_string.split(";"))}
        out_dict = {}
        out_dict["version"] = {
            "name": payload_dict["version"] + " (" + payload_dict["edition"] + ")",
            "protocol": int(payload_dict["protocol_version"])
        }
        try:
            out_dict["description"] = [STRIP_MOTD.sub('', payload_dict["motd_1"]), STRIP_MOTD.sub('', payload_dict["motd_2"])]
        except KeyError:  # older Bedrock server versions do not respond with the secondary MotD.
            out_dict["description"] = [STRIP_MOTD.sub('', payload_dict["motd_1"])]
        out_dict["players"] = {"max": int(payload_dict["max_players"]), "online": int(payload_dict["current_players"])}
        debug("server(%s:%s) motd %s", address, port, out_dict)
    except Exception:
        debug(traceback.format_exc())
        return False, "motd parse fail."

    return True, json.dumps(out_dict, ensure_ascii = False)

def udp_query(address, port):
    # type: (str, int) -> tuple[bool, str]
    import sys
    error("通用UDP仅支持转发模式")
    sys.exit(1)
    return False, "Unsupported"
