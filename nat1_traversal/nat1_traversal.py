#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://github.com/Guation/nat1_traversal

__author__ = "Guation"

import os, argparse, sys, json, traceback, socket, time, threading, multiprocessing
from logging import debug, info, warning, error, DEBUG, INFO, basicConfig
from nat1_traversal.util.stun import nat_type_test, get_self_ip_port, addr_available, TYPE_TCP, TYPE_UDP
from nat1_traversal.util.tcp_port_forwarder import start_tcp_port_forward
from nat1_traversal.util.udp_port_forwarder import start_udp_port_forward
from nat1_traversal.util.motd import mcje_query, srv_query, tcp_query, mcbe_query, udp_query
from nat1_traversal.util.addr_tool import convert_addr, convert_mc_host
from nat1_traversal.util.version import VERSION

def register_exit():
    import signal
    force_exit = False
    def stop(signum, frame):
        nonlocal force_exit
        if force_exit:
            warning("强制退出")
            os._exit(1)
        else:
            info("用户退出")
            force_exit = True
            sys.exit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

def init_logger(debug: bool) -> None:
    if debug:
        basicConfig(
            level=DEBUG,
            format='[%(levelname)8s] %(asctime)s <%(module)s.%(funcName)s>:%(lineno)d\n[%(levelname)8s] %(message)s')
    else:
        basicConfig(
            level=INFO,
            format='[%(levelname)8s] %(message)s')

class logger_filter:
    def __init__(self, max_tick: int):
        self.buff_tick = 0
        self.buff_msg = ""
        self.max_tick = max_tick

    def __call__(self, msg) -> bool:
        self.buff_tick += 1
        if self.buff_msg == msg and self.buff_tick < self.max_tick:
            return False
        else:
            self.buff_tick = 0
            self.buff_msg = msg
            return True

def forward_main(local_addr, remote_addr, mapped_addr, debug, _type):
    # type: (socket._Address, socket._Address, socket._Address, bool, int) -> None
    init_logger(debug)
    if _type is TYPE_TCP:
        start_tcp_port_forward(local_addr, remote_addr, mapped_addr)
    elif _type is TYPE_UDP:
        start_udp_port_forward(local_addr, remote_addr, mapped_addr)

def main():
    parser = argparse.ArgumentParser(description='NAT1 Traversal', add_help=False, allow_abbrev=False, usage=argparse.SUPPRESS)
    parser.add_argument('-h', '--help', dest='H', action='store_true')
    parser.add_argument('-l', '--local', dest='L', type=str, nargs='?', const=':')
    parser.add_argument('-r', '--remote', dest='R', type=str, nargs='?', const=':')
    parser.add_argument('-c', '--config', dest='C', type=str, default="config.json")
    parser.add_argument('-d', '--debug', dest='D', action='store_true')
    parser.add_argument('-v', '--version', dest='V', action='store_true')
    parser.add_argument('-t', '--nat-type-test', dest='T', action='store_true')
    parser.add_argument('-q', '--query', dest='Q', type=str, nargs='?', const=':0')
    parser.add_argument('--query-java', dest='QJ', type=str, nargs='?', const=':0')
    parser.add_argument('--query-java-v6', dest='QJ6', type=str, nargs='?', const=':0')
    parser.add_argument('--query-bedrock', dest='QB', type=str, nargs='?', const=':0')
    parser.add_argument('--query-bedrock-v6', dest='QB6', type=str, nargs='?', const=':0')
    args = parser.parse_args()

    init_logger(args.D)

    if args.H:
        info(
            "\n%s [-h] [-l] [-r] [-c] [-d] [-v] [-q]"
            "\n-h  --help                              显示本帮助"
            "\n-l  --local [[ip]:[port]]               本地监听地址，省略ip时默认为0.0.0.0，省略port时默认为25565"
            "\n                                        此字段将覆盖config.json中的local字段"
            "\n-r  --remote [[ip]:[port]]              转发目的地址，省略ip时默认为127.0.0.1，省略port时默认为25565"
            "\n                                        此字段将覆盖config.json中的remote字段"
            "\n-c  --config <config.json>              DDNS配置文件，不指定时默认为当前目录的config.json"
            "\n-d  --debug                             Debug模式"
            "\n-v  --version                           显示版本"
            "\n-t  --nat-type-test                     NAT类型测试（仅参考）"
            "\n-q  --query [<host>[:port]]             MC服务器MOTD查询，IPv6优先（Java+Bedrock）"
            "\n    --query-java [<host>[:port]]        JE服务器MOTD查询，仅IPv4，省略port时默认为25565"
            "\n    --query-java-v6 [<host>[:port]]     JE服务器MOTD查询，仅IPv6，省略port时默认为25565"
            "\n    --query-bedrock [<host>[:port]]     BE服务器MOTD查询，仅IPv4，省略port时默认为19132"
            "\n    --query-bedrock-v6 [<host>[:port]]  BE服务器MOTD查询，仅IPv6，省略port时默认为19133"
            "\n"
            "\nconfig.json 详见README"
            "\ntype(String)                            mcje|mcbe|web|tcp|udp"
            "\ndns(String)                             no_dns|cloudflare|dynv6|webhook"
            "\nid(String|null)"
            "\ntoken(String|null)"
            "\ndomain(String)"
            "\nsub_domain(String)"
            "\nlocal(String|null)"
            "\nremote(String|null)"
        , sys.argv[0])
        sys.exit(0)
    if args.V:
        info(VERSION)
        sys.exit(0)
    if args.Q or args.QJ or args.QJ6 or args.QB or args.QB6:
        if args.Q or args.QJ or args.QJ6:
            server_ip, server_port = srv_query("_minecraft._tcp.", *convert_mc_host(args.Q or args.QJ6 or args.QJ), 25565)
            status = False
            if not status and (args.Q or args.QJ6):
                if not server_ip:
                    server_ip = "::1"
                status, msg = mcje_query(server_ip, server_port, socket.AF_INET6)
                if status:
                    info("MCJE: %s", msg)
            if not status and (args.Q or args.QJ):
                if not server_ip:
                    server_ip = "127.0.0.1"
                status, msg = mcje_query(server_ip, server_port, socket.AF_INET)
                if status:
                    info("MCJE: %s", msg)
            if not status:
                warning("MCJE: 服务器离线")
        if args.Q or args.QB or args.QB6:
            status = False
            if not status and (args.Q or args.QB6):
                server_ip, server_port = srv_query("_minecraft._udp.", *convert_mc_host(args.Q or args.QB6 or args.QB), 19133)
                if not server_ip:
                    server_ip = "::1"
                status, msg = mcbe_query(server_ip, server_port, socket.AF_INET6)
                if status:
                    info("MCBE: %s", msg)
            if not status and (args.Q or args.QB):
                server_ip, server_port = srv_query("_minecraft._udp.", *convert_mc_host(args.Q or args.QB6 or args.QB), 19132)
                if not server_ip:
                    server_ip = "127.0.0.1"
                status, msg = mcbe_query(server_ip, server_port, socket.AF_INET)
                if status:
                    info("MCBE: %s", msg)
            if not status:
                warning("MCBE: 服务器离线")
        sys.exit(0)
    try:
        local_addr = convert_addr(args.L, "0.0.0.0")
    except ValueError as e:
        error("参数 --local 解析错误: %s", e)
        error("查看帮助： %s --help", sys.argv[0])
        debug(traceback.format_exc())
        sys.exit(1)
    if args.T:
        info("正在进行NAT类型测试")
        info("TCP: NAT%s", nat_type_test(local_addr, TYPE_TCP)[1])
        info("UDP: NAT%s", nat_type_test(local_addr, TYPE_UDP)[1])
        sys.exit(0)
    config = {
        "type": "mcje",
        "dns": "no_dns",
        "id": None,
        "token": None,
        "domain": "",
        "sub_domain": "",
        "local": None,
        "remote": None
    }
    if not os.path.isfile(args.C):
        error("DDNS配置文件 %s 未找到" , os.path.abspath(args.C))
        try:
            if sys.stdin.isatty():
                gen_config = input("是否生成新配置[y/N]：")
                if gen_config.upper().startswith("Y"):
                    with open(args.C, "w") as f:
                        f.write(json.dumps(config, indent=4, ensure_ascii=False))
                        f.flush()
                    info("DDNS配置文件 %s 已生成" , os.path.abspath(args.C))
        except (EOFError, OSError):
            debug(traceback.format_exc())
        sys.exit(1)
    try:
        with open(args.C, "r") as f:
            config_s1 = f.read()
            config.update(json.loads(config_s1))
    except Exception:
        error("DDNS配置文件 %s 读取失败", os.path.abspath(args.C))
        debug(traceback.format_exc())
        sys.exit(1)
    try:
        config_s2 = json.dumps(config, indent=4, ensure_ascii=False)
        if config_s1 != config_s2:
            with open(args.C, "w") as f:
                f.write(config_s2)
                f.flush()
    except Exception:
        warning("DDNS配置文件 %s 回写失败", os.path.abspath(args.C))
        debug(traceback.format_exc())
    try:
        dns = getattr(getattr(__import__("nat1_traversal.dns." + config["dns"]), "dns"), config["dns"])
        assert hasattr(dns, "init")
        assert hasattr(dns, "update_record")
        info("使用的DNS供应商为 %s", config["dns"])
    except Exception:
        error("不受支持的DNS供应商 %s", config["dns"])
        debug(traceback.format_exc())
        sys.exit(1)
    dns.init(config["id"], config["token"])
    try:
        remote_addr = convert_addr(args.R, "127.0.0.1")
    except ValueError as e:
        error("参数 --remote 解析错误: %s", e)
        error("查看帮助： %s --help", sys.argv[0])
        debug(traceback.format_exc())
        sys.exit(1)
    if local_addr is None:
        try:
            local_addr = convert_addr(config["local"], "0.0.0.0")
        except ValueError as e:
            error("config 中 local 字段解析错误: %s", e)
            debug(traceback.format_exc())
            sys.exit(1)
    if remote_addr is None:
        try:
            remote_addr = convert_addr(config["remote"], "127.0.0.1")
        except ValueError as e:
            error("config 中 remote 字段解析错误: %s", e)
            debug(traceback.format_exc())
            sys.exit(1)
    if local_addr is None:
        error("缺少参数 --local")
        error("查看帮助： %s --help", sys.argv[0])
        sys.exit(1)
    if remote_addr is None and local_addr[1] == 0:
        error("共端口模式port不能为0")
        sys.exit(1)
    if config["type"] == "mcje":
        srv_prefix = "_minecraft._tcp."
        query_function = mcje_query
        socket_type = TYPE_TCP
    elif config["type"] == "web":
        srv_prefix = "_web._tcp."
        query_function = tcp_query
        socket_type = TYPE_TCP
    elif config["type"] == "tcp":
        srv_prefix = "_tcp."
        query_function = tcp_query
        socket_type = TYPE_TCP
    elif config["type"] == "mcbe":
        srv_prefix = "_minecraft._udp."
        query_function = mcbe_query
        socket_type = TYPE_UDP
    elif config["type"] == "udp":
        srv_prefix = "_udp."
        query_function = udp_query
        socket_type = TYPE_UDP
    else:
        error("不支持的type: %s", config["type"])
        sys.exit(1)
        return
    try:
        local_addr = addr_available(local_addr, socket_type)
    except ValueError as e:
        error("local地址不可用：%s", e)
        debug(traceback.format_exc())
        sys.exit(1)
    register_exit()
    def update_dns(ip: str, port: int):
        nonlocal dns, config, srv_prefix
        info("获取到映射地址： %s:%s", ip, port)
        for _ in range(3):
            try:
                dns.update_record(config["sub_domain"], config["domain"], "A", ip)
                dns.update_record(srv_prefix + config["sub_domain"], config["domain"], "SRV", config["sub_domain"], port=port)
                info("DDNS更新成功 %s.%s", config["sub_domain"], config["domain"])
                return
            except ValueError as e:
                error("DDNS更新失败： %s", e)
                time.sleep(3)
    if remote_addr is None:
        local_online_filter = logger_filter(60) # 相同日志60次合并成1次
        while True:
            status, msg = query_function("127.0.0.1", local_addr[1])
            if not status:
                if local_online_filter(msg):
                    warning("服务器不在线, %s", msg)
                time.sleep(10)
                continue
            try:
                mapped_addr = get_self_ip_port(local_addr, socket_type)
            except ValueError as e:
                error("获取映射地址失败：%s", e)
                debug(traceback.format_exc())
                time.sleep(10)
                continue
            threading.Thread(target=update_dns, args=mapped_addr).start()
            remote_online_filter = logger_filter(1800)
            while True:
                time.sleep(1)
                status, msg = query_function(*mapped_addr)
                if not status:
                    warning("映射地址离线，开始重新映射，%s", msg)
                    break
                else:
                    if remote_online_filter(msg):
                        info("MOTD: %s", msg)
    else:
        multiprocessing.set_start_method("spawn")
        while True:
            try:
                mapped_addr = get_self_ip_port(local_addr, socket_type)
            except ValueError as e:
                error("获取映射地址失败：%s", e)
                debug(traceback.format_exc())
                time.sleep(10)
                continue
            threading.Thread(target=update_dns, args=mapped_addr).start()
            forward_process = multiprocessing.Process(target=forward_main, args=(local_addr, remote_addr, mapped_addr, args.D, socket_type), daemon=True)
            forward_process.start()
            forward_process.join()
            warning("转发发生异常，可能是映射地址离线，开始重新转发")
            time.sleep(5)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
