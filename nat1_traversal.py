#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://github.com/Guation/nat1_traversal

__author__ = "Guation"

import os, argparse, sys, json, traceback, socket, importlib, time, threading
from logging import debug, info, warning, error, DEBUG, INFO, basicConfig
from util.stun import nat_type_test, get_self_ip_port
from util.port_forwarder import start_port_forward
from util.motd import motd_query

def _convert_port(s_port: str) -> int:
    try:
        i_port = int(s_port)
    except ValueError as e:
        raise ValueError(
            "端口不是数字"
        ) from e
    if i_port >= 0 and i_port <= 65535:
        return i_port
    else:
        raise ValueError(
            "端口应该在0-65535之间"
        )

def _convert_ip(ip: str) -> str:
    try:
        return socket.inet_ntoa(socket.inet_aton(ip))
    except OSError as e:
        raise ValueError(
            "IP格式错误"
        ) from e

def convert_addr(addr, default_ip):
    # type: (str, str) -> socket._RetAddress | None
    if not addr:
        return None
    tmp = addr.split(":")
    if len(tmp) == 1:
        return (default_ip, _convert_port(tmp[0]))
    elif len(tmp) == 2:
        return (_convert_ip(tmp[0]), _convert_port(tmp[1]))
    else:
        raise ValueError(
            "地址格式错误"
        )

def main():
    parser = argparse.ArgumentParser(description='tcp port forwarder', add_help=False, allow_abbrev=False, usage=argparse.SUPPRESS)

    parser.add_argument('-h', '--help', dest='H', action='store_true')
    parser.add_argument('-l', '--local', dest='L', type=str)
    parser.add_argument('-r', '--remote', dest='R', type=str)
    parser.add_argument('-c', '--config', dest='C', type=str, default="config.json")
    parser.add_argument('-d', '--debug', dest='D', action='store_true')
    parser.add_argument('-v', '--version', dest='V', action='store_true')
    parser.add_argument('-t', '--nat-type-test', dest='T', action='store_true')
    args = parser.parse_args()
    if args.D:
        basicConfig(
            level=DEBUG,
            format='[%(levelname)8s] %(asctime)s <%(module)s.%(funcName)s>:%(lineno)d\n[%(levelname)8s] %(message)s')
    else:
        basicConfig(
            level=INFO,
            format='[%(levelname)8s] %(message)s')
    if args.H:
        info(
            "\n%s [-h] [-l] [-r] [-c] [-d] [-v]"
            "\n-h  --help                              显示本帮助"
            "\n-l  --local [local ip:]<local port>     本地监听地址，省略ip时默认为0.0.0.0"
            "\n-r  --remote [remote ip:]<remote port>  转发目的地址，省略ip时默认为127.0.0.1"
            "\n-c  --config <config.json>              DDNS配置文件"
            "\n-d  --debug                             Debug模式"
            "\n-v  --version                           显示版本"
            "\n-t  --nat-type-test                     NAT类型测试（仅参考）"
        , sys.argv[0])
        exit(0)
    if args.V:
        info("1.0.0")
        exit(0)
    try:
        local_addr = convert_addr(args.L, "0.0.0.0")
    except ValueError as e:
        error("--local: %s", e)
        debug(traceback.format_exc())
        exit(1)
    if args.T:
        info("正在进行NAT类型测试")
        info("NAT%s", nat_type_test(local_addr)[1])
        exit(0)
    if not os.path.isfile(args.C):
        error("DDNS配置文件 %s 未找到" , os.path.abspath(args.C))
        exit(1)
    config = {
        "dns": "no_dns",
        "id": None,
        "token": "",
        "domain": "example.com",
        "sub_domain": "mc"
    }
    try:
        with open(args.C, "r") as f:
            config_s1 = f.read()
            config.update(json.loads(config_s1))
        config_s2 = json.dumps(config, indent=4, ensure_ascii=False)
        if config_s1 != config_s2:
            with open(args.C, "w") as f:
                f.write(config_s2)
                f.flush()
    except Exception:
        error("DDNS配置文件 %s 读取失败", os.path.abspath(args.C))
        debug(traceback.format_exc())
        exit(1)
    if not config["dns"]:
        config["dns"] = "no_dns"
    try:
        dns = importlib.import_module("dns/" + config["dns"])
        info("使用的DNS供应商为 %s", config["dns"])
    except Exception:
        error("不受支持的DNS供应商 %s", config["dns"])
        debug(traceback.format_exc())
        exit(1)
    dns.id = config["id"]
    dns.token = config["token"]
    try:
        remote_addr = convert_addr(args.R, "127.0.0.1")
    except ValueError as e:
        error("--remote: %s", e)
        debug(traceback.format_exc())
        exit(1)
    if local_addr is None:
        error("缺少参数 --local")
        exit(1)
    if remote_addr is None:
        def update_dns(ip, port):
            nonlocal dns, config
            dns.update_record(config["sub_domain"], config["domain"], "A", ip)
            dns.update_record("_minecraft._tcp." + config["sub_domain"], config["domain"], "A", config["sub_domain"], port=port)
        while True:
            status, msg = motd_query("127.0.0.1", local_addr[1])
            if not status:
                warning("server not online", msg)
                time.sleep(10)
                continue
            ip, port = get_self_ip_port()
            threading.Thread(target=update_dns, args=(ip, port)).start()
            buff_tick = 0
            buff_msg = ""
            while True:
                time.sleep(1)
                status, msg = motd_query(ip, port)
                if not status:
                    print("remote offline. restart.")
                    break
                else:
                    if buff_msg == msg:
                        buff_tick += 1
                        if buff_tick < 1800:
                            continue
                    buff_tick = 0
                    buff_msg = msg
                    info("server status: %s", msg)
    else:
        start_port_forward(*local_addr, *remote_addr, *get_self_ip_port(local_addr))

if __name__ == "__main__":
    main()
