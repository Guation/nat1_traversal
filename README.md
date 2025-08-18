# NAT1 Traversal

## 什么是NAT1 Traversal

### 项目背景

随着互联网发展对于IPv4地址的需求量逐步增大，IPv4地址的总量是固定的，ISP(Internet Service Provider)出于盈利目而更倾向于将公网IPv4地址用于商用宽带而非家用宽带。

为了减少在家用宽带的IPv4地址投入量，ISP采用了NAT(Network Address Translation)技术使多名家用宽带用户共用同一个公网IPv4地址，这么做的副作用就是家用宽带的用户尝试对外提供的互联网服务时变得不可寻址。

ISP最常使用的NAT方案为NAPT(Network Address Port Translation)，而在进行网络端口地址转换的过程中，对于端口的映射方案和对外部来源的处理策略又衍生出了四个常见的NAT等级：

| RFC3489 | RFC4787映射行为 | RFC4787过滤行为 | RFC4787端口分配行为 | 备注 |
|:--:|:--:|:--:|:--:|:--:|
|OPEN INTERNET（公网）|Endpoint-Independent Mapping（端点独立映射）|Endpoint-Independent Filtering（端点独立过滤）|Port Preservation（端口保留）|NAT0|
|**FULL CONE**（全锥）|Endpoint-Independent Mapping（端点独立映射）|Endpoint-Independent Filtering（端点独立过滤）|No Port Preservation（不保留端口）|NAT1|
|RESTRICTED CONE（IP限制锥）|Endpoint-Independent Mapping（端点独立映射）|Address-Dependent Filtering（地址独立过滤）|No Port Preservation（不保留端口）|NAT2|
|PORT RESTRICTED CONE（端口限制锥）|Endpoint-Independent Mapping（端点独立映射）|Address and Port-Dependent Filtering（地址与端口独立过滤）|No Port Preservation（不保留端口）|NAT3|
|**SYMMETRIC**（对称型）|Address and Port-Dependent Mapping（地址与端口独立映射）|Address and Port-Dependent Filtering（地址与端口独立过滤）|No Port Preservation（不保留端口）|NAT4|

其中对于ISP而言最常使用的策略为`FULL CONE`和`SYMMETRIC`。

- `FULL CONE`是一种宽松的解决方案，对于同一`iAddr:iPort`发起的请求始终对应到同一`eAddr:ePort`，直至该映射一段时间内不再使用时才会被释放。也就是说如果在释放前将映射重新标记为使用状态，那么映射将始终不会关闭，我们可以轻松的获取到内外端口的映射关系，`电信`通常采用这种方案。

- `SYMMETRIC`是一种严格的解决方案，对于同一个`iAddr:iPort`向不同的`dAddr:dPort`建立连接时将生成新的`eAddr:ePort`，由于每次向不同地址发起的连接都将更换新的来源地址，使得该方案的映射关系变得不可预测，`移动`通常采用这种方案。

### 项目目的

借助特定的公共STUN服务器，在`FULL CONE`中申请并维持一个`TCP/UDP`内外端口的映射关系，实现在家用宽带上对外提供互联网服务。

### 特化功能

在`Linux`平台为`Minecraft: Java Edition`和`Minecraft: Bedrock Edition`提供像租赁云服务器的一样的开服体验。

### 方案对比

|  | NAT1 Traversal | 租赁云服务器 | 内网穿透|
|:--|:--:|:--:|:--:|
|使用域名连接到服务器|✅|✅|✅|
|使用IP连接到服务器|⚠️ISP会定期更新IP 无法长期使用同一IP|✅|❓取决于供应商|
|控制台读取玩家IP|⚠️仅限Linux开服|✅|❌全为中转IP|
|非控制台读取玩家IP|⚠️转发日志记录|⚠️已从控制台读取|❓取决于供应商|
|配置难度|中等|简单|简单|
|自身网络限制|FULL CONE|无|无|
|费用|免费|昂贵|中等|
|可用性|单线<sup>1</sup>|单线/BGP<sup>2</sup>|单线/BGP<sup>2</sup>|
|上行速率/流量限制|无<sup>3</sup>|有|有|

1. 移动与电信联通之间跨运营商存在严重QoS现象，可能导致服务不可用
2. 单线或BGP取决于供应商，单线时同样存在跨运营商QoS现象
3. 无上行限制指不存在中转服务器的二次限制，实际使用时仍受到自身网络的上行限制

## 使用方法

### 命令行参数

```
$ python3 nat1_traversal.pyz -h
[    INFO] 
nat1_traversal.pyz [-h] [-l] [-r] [-c] [-d] [-v] [-q]
-h  --help                              显示本帮助
-l  --local [[ip]:[port]]               本地监听地址，省略ip时默认为0.0.0.0，省略port时默认为25565
                                        此字段将覆盖config.json中的local字段
-r  --remote [[ip]:[port]]              转发目的地址，省略ip时默认为127.0.0.1，省略port时默认为25565
                                        此字段将覆盖config.json中的remote字段
-c  --config <config.json>              DDNS配置文件
-d  --debug                             Debug模式
-v  --version                           显示版本
-t  --nat-type-test                     NAT类型测试（仅参考）
-q  --query [<host>[:port]]             MC服务器MOTD查询，IPv6优先（Java+Bedrock）
    --query-java [<host>[:port]]        JE服务器MOTD查询，仅IPv4，省略port时默认为25565
    --query-java-v6 [<host>[:port]]     JE服务器MOTD查询，仅IPv6，省略port时默认为25565
    --query-bedrock [<host>[:port]]     BE服务器MOTD查询，仅IPv4，省略port时默认为19132
    --query-bedrock-v6 [<host>[:port]]  BE服务器MOTD查询，仅IPv6，省略port时默认为19133
```

### NAT类型检测
#### Windows（无python3环境）
1. 从Releases下载`NAT1_Traversal_nt.zip`
2. 右键压缩包选择“解压到NAT1_Traversal_nt”
3. 在`NAT1_Traversal_nt`目录中按住`shift`并在空白处按右键，点击“在此处打开Powershell窗口”
4. 执行`.\nat1_traversal.exe -t`

#### Windows（有python3环境）
1. 从Releases下载`NAT1_Traversal.tgz`或`NAT1_Traversal.zip`
2. 右键压缩包选择“解压到NAT1_Traversal”
3. 在`NAT1_Traversal`目录中按住`shift`并在空白处按右键，点击“在此处打开Powershell窗口”
4. 执行`python nat1_traversal.pyz -t`

#### Linux/MacOS
1. 从Releases下载`NAT1_Traversal.tgz`
2. 打开命令行并`cd`到下载目录
3. 使用`tar -xzvf NAT1_Traversal.tgz -C NAT1_Traversal ; cd NAT1_Traversal`
3. 执行`python3 nat1_traversal.pyz -t`或`chmod +x nat1_traversal.pyz ; ./nat1_traversal.pyz -t`

#### 结果分析
- 如果结果显示为`SYMMETRIC`则代表您无法使用本项目的核心功能。

- 如果结果显示`RESTRICTED CONE`或`PORT RESTRICTED CONE`则代表您必须登录到光猫/路由器中进行“(PORT) RESTRICTED CONE 改 FULL CONE”的步骤。

- 如果结果显示`FULL CONE`则代表您可以直接使用本项目的核心功能而无需对网络进行配置。

- 如果结果显示`OPEN INTERNET`则代表您已经拥有公网IP地址，无需使用本项目。

### \(PORT\) RESTRICTED CONE 改 FULL CONE
#### 配置端口映射规则

当您的测试结果显示为`PORT RESTRICTED CONE`时可能并不代表运营商的NAT等级为`PORT RESTRICTED CONE`，

可能是由于光猫/路由器的防火墙使其表现行为与`PORT RESTRICTED CONE`一致。

您可以在光猫/路由器背面的铭牌中找到设备默认的管理地址和默认的管理员账户及密码。

部分路由器会要求您在首次登录时更改管理员密码，请以实际情况为准。

登录后在选项卡寻找类似“端口映射”、“端口转发”、“虚拟服务器”之类的字眼，并在选项卡中添加一条TCP规则，其中内外端口均填入25565（其他端口也可以，本例中使用25565），局域网IP填写运行nat1_traversal的主机IP。

如果您使用光猫+路由器的组合且光猫和路由器均处于路由模式而非桥接模式，则您需要在光猫和路由器中分别添加一条映射规则，在光猫中将端口映射的局域网IP指向路由器IP，而在路由器中将端口映射的局域网IP指向运行nat1_traversal的主机IP。

如果您的光猫/路由器拥有`DMZ`的配置选项（通常光猫配置DMZ需要超级管理员密码而光猫背面的密码为普通用户密码），您也可以使用`DMZ`将所有外部请求统一重定向到运行nat1_traversal的主机IP，此时无需再逐一对端口进行配置。

#### 再次检测NAT类型

此时需要在前一次的指令后指定测试端口`-l :25565`，由于我们只对25565进行了映射，如果不指定端口那么测试结果依旧是`PORT RESTRICTED CONE`

Windows使用`.\NAT1_Traversal.exe -t -l :25565`

MacOS/Linux使用`python3 NAT1_Traversal.pyz -t -l :25565`

此时如果测试结果为`FULL CONE`则代表您已完成配置，可进行开服。

### 修改 config.json 文件中的配置信息
对于不同dns供应商，我们都提供了形如`config.供应商名.json`的配置模板以供参考，您可以使用`-c /path/to/your_config.json`的方法指定您的配置路径，不使用`-c`指定路径时默认使用当前目录下的`config.json`。

当您在终端中运行本程序，且指定路径的配置文件不存在时，程序将询问您是否在该位置使用默认配置生成配置文件。当指定路径的父目录不存在时配置文件将生成失败。
#### 字段解释
- type: 映射的服务类型
  - mcje: JAVA版Minecraft，端口绑定到`_minecraft._tcp.`（默认）
  - mcbe: 基岩版Minecraft，端口绑定到`_minecraft._udp.`
  - web: HTTP/HTTPS网站，端口绑定到`_web._tcp.`
  - tcp: 通用TCP应用，端口绑定到`_tcp.`
  - udp: 通用UDP应用，端口绑定到`_udp.`

- dns: dns供应商名称
  - cloudflare
  - dynv6
  - no_dns: 不使用dns（默认）
  - webhook: 使用自定义URL接收POST消息

- id: 您登录dns管理界面的登录邮箱或者用户名，有些供应商无需提供此字段，此时值应为`null`

- token: 这是您在dns供应商处生成的管理令牌，请确保其对domain有管理权限

- domain: 您托管在dns供应商处的主域名，例如`example.com`

- sub_domain: 您想要绑定的子域名，此字段不包含主域名。例如您希望使用`mc.example.com`进服，那么您应该填入`mc`

- local: 本地监听地址，与命令行指令`--local`一致，优先级低于`--local`

- remote: 转发目的地址，与命令行指令`--remote`一致，优先级低于`--remote`

#### id和token的获取方法

- [cloudflare](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) 推荐使用`API Token`作为`token`而将`id`置为`null`，请确保token具有指定zone的edit权限。

- [dynv6](https://dynv6.com/keys) 使用`HTTP Tokens`作为`token`将`id`置为`null`，推荐设置为仅对指定zone有效。

- [webhook](./nat1_traversal/dns/webhook.py) 使用id作为POST请求的URL，URL需以`http://`或`https://`开头，当token不为`null`时请求头将携带`Bearer Authentication`参数。
  - A记录请求体：`{"name": "{sub_domain}", "data": "xx.xx.xx.xx", "type": "A", "domain": "{domain}"}`
  - SRV记录请求体：`{"name": "{srv_prefix}{sub_domain}", "data": "{sub_domain}", "type": "SRV", "domain": "{domain}", "priority": 10, "weight": 0, "port": yyyy}`

- [tencentcloud](https://console.cloud.tencent.com/cam) 新建用户->快速创建->访问方式:编程访问,用户权限:QcloudDNSPodFullAccess，使用`SecretId`作为`id`，使用`SecretKey`作为`token`。

- [alidns](https://ram.console.aliyun.com/users) 创建用户->使用永久 AccessKey 访问->添加权限:AliyunDNSFullAccess，使用`AccessKey ID`作为`id`，使用`AccessKey Secret`作为`token`。

### Minecraft: Java Edition 开服
#### Linux 3.9+ 共端口模式
利用[Linux内核在3.9](https://lwn.net/Articles/542629/)引入的`SO_REUSEPORT`特性可以使多个应用程序监听同一端口，

也就是意味着我们可以在MC服务器正在运行的同时使用和MC服务器相同的端口去申请并维持一个`TCP`内外端口的映射关系。

> 多个应用程序监听同一端口不仅都需要设置`SO_REUSEPORT`还需要应用程序都为同一用户运行。任意条件不满足后运行的应用程序都会抛出端口被占用的提示。

由于MC服务器本身未配置`SO_REUSEPORT`，我们需要使用Linux的`LD_PRELOAD`机制对JAVA的`bind`函数进行hook操作，使其在监听端口时激活`SO_REUSEPORT`特性。

在`hook_bind`文件夹中使用`make`指令生成`hook_bind.so`，复制该文件到您的服务器根目录中。

找到您的开服脚本`run.sh`或其他启动脚本，在`java`之前加入`LD_PRELOAD=./hook_bind.so`，

类似于`LD_PRELOAD=./hook_bind.so java @user_jvm_args.txt @libraries/net/neoforged/neoforge/21.1.133/unix_args.txt "$@"`

> ⚠️注意：
> 如果您在使用面板管理您的服务器，请不要直接将`LD_PRELOAD=./hook_bind.so`加入到启动指令的`java`之前，
> 这会导致您无法启动您的服务器。因为该注入仅适用于使用[shell](https://github.com/bminor/bash)启动`java`的情况，不适用于基于[exec族](https://github.com/bminor/glibc/blob/258126bc0b77d7f9ae7d0b2737ec66e186c1e0ef/posix/unistd.h#L599)的管理面板启动`java`的情况。
> 您可以参阅[在面板中启用SO_REUSEPORT](./README_extend.md#在面板中启用SO_REUSEPORT)使hook适应您的管理面板。

然后像往常一样启动服务器，如果您在日志中看见类似`Hooked bind: PID=1234, FD=5, setsockopt SO_REUSEPORT`的日志则代表修改已生效。

在`config.json`中将`local`值由`null`修改为`":25565"`。

使用`python3 nat1_traversal.pyz`，如果一切顺利，那么您将能使用`config.json`中配置的域名进服。

如果您的dns供应商设置为了`no_dns`那么您可以在NAT1 Traversal日志中找到形如`[    INFO] 获取到映射地址： xx.xx.xx.xx:yyyy`的记录，可复制该地址连接到服务器。

> ⚠️警告：
> 由于此方案解除了单一进程对于一个端口的独占行为，
> 您可能会遇到多个MC服务器同时监听同一端口而**不会抛出**端口已被占用的提示，
> 此时您使用游戏客户端连接服务器时Linux内核将随机将您分配到其中一个服务器中。
> 此功能原本是用于均衡负载，但此时可能会造成多名玩家登录到不同服务器而无法观察到对方的混乱。
> 请您在运行MC服务器之前检查目标端口是否已被使用，避免多个MC服务器共用同一端口的行为。
> 如果出现了多个MC服务器共用同一端口的情况，本项目可能会误认为服务器MOTD在不断更新而不停在日志中输出MOTD。

#### Windows/MacOS/Linux 转发模式
在不可使用Linux 3.9+的`SO_REUSEPORT`时，我们可以让NAT1 Traversal作为中间代理转发我们的MC服务器流量。

此时您在mc服务器控制台将看到所有玩家均从`127.0.0.1`登录，您可以使用端口号和NAT1 Traversal日志判断用户来源ip。

使用NAT1 Traversal作为中间代理转发MC服务器流量时无需对mc服务器做任何修改，唯一需值得注意的是您需要将mc服务器的端口设置为非`25565`的端口（例如`25566`），因为`25565`端口我们需要提供给NAT1 Traversal使用。

在`config.json`中将`local`值由`null`修改为`":25565"`，将`remote`值由`null`修改为`":25566"`。

Windows使用`.\nat1_traversal.exe`

MacOS/Linux使用`python3 nat1_traversal.pyz`

如果一切顺利，那么您将能使用`config.json`中配置的域名进服。

如果您的dns供应商设置为了`no_dns`那么您可以在NAT1 Traversal日志中找到形如`[    INFO] 获取到映射地址： xx.xx.xx.xx:yyyy`的记录，可复制该地址连接到服务器。

> ⚠️提示：
> Windows中`cmd`和`powershell`默认启用的`快速编辑模式`可能会在您使用鼠标框选日志时将本项目挂起，
> 挂起期间程序无法转发或处理任何数据，如遇到挂起情况可使用回车键解除挂起，长期使用建议关闭`快速编辑模式`。

### Minecraft: Bedrock Edition 开服
#### Linux 3.9+ 共端口模式
您需要将`type`设置为`mcbe`而不是默认的`mcje`，其余设置与[MCJE共端口模式](#linux-39-共端口模式)类似。

您需要在启动指令`LD_LIBRARY_PATH=. ./bedrock_server`之前添加`LD_PRELOAD=./hook_bind.so`，变为`LD_PRELOAD=./hook_bind.so LD_LIBRARY_PATH=. ./bedrock_server`。

并且您需要修改`server.properties`，将其中的`enable-lan-visibility=true`改为`enable-lan-visibility=false`，尤其是当您的`server-port=19132`时。

如果您不这样做，在您连接服务器时可能会收到`哇，该服务器非常受欢迎！请稍后再回来查看空间是否开放。`的拒绝提示。

如果您在服务端日志中看见类似`Hooked bind: PID=1234, FD=5, setsockopt SO_REUSEPORT`的日志则代表修改已生效。

由于基岩版不支持`SRV记录`解析，我们需要使用[三方服务端](#使用bedrockconnect代理服务器将玩家重定向到服务器)进行重定向，或者使用[XBOX好友系统广播](#使用broadcaster向xbox好友广播服务器地址)服务器地址。

#### Windows/MacOS/Linux 转发模式
您需要将`type`设置为`mcbe`而不是默认的`mcje`，其余设置与[MCJE转发模式](#windowsmacoslinux-转发模式)的配置方式完全相同。

由于基岩版不支持`SRV记录`解析，我们需要使用[三方服务端](#使用bedrockconnect代理服务器将玩家重定向到服务器)进行重定向，或者使用[XBOX好友系统广播](#使用broadcaster向xbox好友广播服务器地址)服务器地址。

#### 使用BedrockConnect代理服务器将玩家重定向到服务器
您需要在云服务器中下载[带有SRV记录解析的BedrockConnect](https://github.com/Guation/BedrockConnect_with_SRV)，

云服务器要求具有公网UDP:19132端口，对带宽和服务器性能无硬性要求，推荐下载到处于境内的云服务器中。

编辑`server.json`文件，将其中`address`字段修改为您在NAT1 Traversal中设置的DDNS地址，`port`保持为`0`。

`name`字段可以修改为您希望在BedrockConnect菜单中展示的服务器名称，`iconUrl`为您希望在BedrockConnect菜单中展示的服务器图标。

修改完成后使用`java -jar BedrockConnect-1.0-SNAPSHOT.jar`指令运行您的代理服务器。

玩家使用云服务器IP加入代理服务器，点击菜单中您的服务器按钮后，玩家将会被`transfer`指令重定向到您的服务器中，之后玩家将直接与您的服务器通信，数据包不再经过代理服务器。

#### 使用Broadcaster向XBOX好友广播服务器地址
您需要下载[带有SRV记录解析的Broadcaster](https://github.com/Guation/Broadcaster_with_SRV)，

推荐下载到处于境外的云服务器中，这样有利于程序稳定的连接到XBOX网络。

您需要[注册](https://signup.live.com/)一个新的Microsoft账户作为广播账户，请勿直接将您的账户作为广播账户以防止账户意外封禁对您造成损失。

注册完成后前往[Xbox profile](https://www.xbox.com/play/user)为您的Microsoft广播账户注册gametag。

编辑`config.yml`文件，将其中`ip`字段修改为您在NAT1 Traversal中设置的DDNS地址，`port`保持为`0`。

修改完成后使用`java -jar MCXboxBroadcastStandalone.jar`指令运行Broadcaster。

运行后按照日志提示打开[登录](https://www.microsoft.com/link)地址并填入日志中的code，接着按照网页提示进行登录操作。

登录成功后日志中将显示您的Microsoft广播账户的gametag。

玩家需要在游戏中搜索并添加您的Microsoft广播账户为好友，Broadcaster会自动同意好友申请，成功添加好友后玩家可以通过加入好友游戏的按钮加入您的服务器。

### 更多用法
在寻找更多穿透姿势？HTTP(S)网站？RDP远程桌面？[点我查看](./README_extend.md#更多用法)

### 故障排查
#### Windows
在`powershell`中使用`nslookup`进行DNS记录查询，请检查A记录中的应答地址以及SRV记录中的应答端口与程序获取的映射地址是否一致。
```powershell
PS > nslookup.exe -q=a mc.example.com
服务器:  UnKnown
Address:  192.168.1.1

非权威应答:
名称:    mc.example.com
Address:  xx.xx.xx.xx

PS > nslookup.exe -q=srv _minecraft._tcp.mc.example.com
服务器:  UnKnown
Address:  192.168.1.1

非权威应答:
_minecraft._tcp.mc.example.com       SRV service location:
          priority       = 10
          weight         = 0
          port           = yyyy
          svr hostname   = mc.example.com
```

#### Linux
在`shell`中使用`dig`进行DNS记录查询，请检查A记录中的应答地址以及SRV记录中的应答端口与程序获取的映射地址是否一致。
```shell
$ dig +noall +answer mc.example.com A
mc.example.com.	305	IN	A	xx.xx.xx.xx

$ dig +noall +answer _minecraft._tcp.mc.example.com SRV
_minecraft._tcp.mc.example.com. 60 IN SRV	10 0 yyyy mc.example.com.
```

### 构建
#### Linux
```
python3 -m venv venv
source venv/bin/activate
git clone https://github.com/Guation/nat1_traversal.git
cd nat1_traversal
pip install shiv wheel
shiv -e nat1_traversal.nat1_traversal:main -o nat1_traversal.pyz .
```

#### Windows
```
git clone https://github.com/Guation/nat1_traversal.git
cd nat1_traversal
pip install pyinstaller requests dnspython tencentcloud-sdk-python-dnspod alibabacloud_alidns20150109
pyinstaller nat1_traversal.spec
```

### 其他
#### 主仓库
[GitHub](https://github.com/Guation/nat1_traversal)

#### 镜像仓库
[Gitee](https://gitee.com/Guation/nat1_traversal)

#### 视频教程
[[MCJE] 低延迟IPv4直连联机教程，全平台通用。NAT1 Traversal](https://www.bilibili.com/video/BV162TezeEmx/)

[[WEB]无公网在家建站、远程直连NAS教程。NAT1 Traversal](https://www.bilibili.com/video/BV1GeuuzWEgg/)
