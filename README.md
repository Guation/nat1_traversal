# NAT1 Traversal

***

### 什么是NAT1 Traversal

#### 项目背景

随着互联网发展对于IPv4地址的需求量逐步增大，IPv4地址的总量是固定的，ISP(Internet Service Provider)出于盈利目的更倾向于将公网IPv4地址用于商用宽带而非家用宽带。

为了减少在家用宽带的IPv4地址投入量，ISP采用了NAT(Network Address Translation)技术使多名家用宽带用户共用同一个公网IPv4地址，这么做的副作用就是家用宽带的用户尝试对外提供的互联网服务时变得不可寻址。

ISP最常使用的NAT方案为NAPT(Network Address Port Translation)，而在进行网络端口地址转换的过程中，对于端口的对应方案和对输入数据来源的处理策略又衍生出了四个常见的NAT等级：

- **FULL CONE**（全锥，NAT1）
- RESTRICTED CONE（IP限制锥，NAT2）
- PORT RESTRICTED CONE（端口限制锥，NAT3）
- **SYMMETRIC**（对称型，NAT4）

其中对于ISP而言最常使用的策略为`FULL CONE`和`SYMMETRIC`。

- `FULL CONE`是一种宽松的解决方案，对于同一内部端口发起的请求始终对应到同一外部端口，直至该映射一段时间内不再使用时才会被释放。也就是说如果能将映射通道一直标记为使用状态，那么映射将始终不会关闭，我们可以轻松的获取到内外端口的映射关系，`电信`通常采用这种方案。

- `SYMMETRIC`是一种严格的解决方案，对于同一个内部端口向不同的外部端口建立连接时将新建一个端口到端口的对应关系，由于每次向不同地址发起的连接都将更换新的来源地址，使得该方案的映射关系变得不可预测，`移动`通常采用这种方案。

#### 项目目的

借助特定的公共STUN服务器，在`FULL CONE`中申请并维持一个`TCP`内外端口的映射关系，实现在家用宽带上对外提供互联网服务。

#### 特化功能

在`Linux`平台为`Minecraft: Java Edition`提供像租赁云服务器的一样的开服体验。

#### 方案对比

|  | NAT1 Traversal | 租赁云服务器 | 内网穿透|
|:--|:--:|:--:|:--:|
|使用域名连接到服务器|✅|✅|✅|
|使用IP连接到服务器|⚠️ISP会定期更新IP 无法长期使用同一IP|✅|❓取决于供应商|
|控制台读取玩家IP|⚠️仅限Linux开服|✅|❌全为中转IP|
|非控制台读取玩家IP|⚠️转发日志记录|⚠️已从控制台读取|❓取决于供应商|
|配置难度|中等|简单|简单|
|自身网络限制|FULL CONE|无|无|
|费用|免费|昂贵|中等|
|稳定性|取决于自身网络|稳定|取决于自身网络和中转网络|
|上行速率/流量限制|无|有|有|

### 使用方法

#### 命令行参数

```shell
$ python3 nat1_traversal.py -h
[    INFO] 
nat1_traversal.py [-h] [-l] [-r] [-c] [-d] [-v] [-q]
-h  --help                                显示本帮助
-l  --local [[local ip]:[local port]]     本地监听地址，省略ip时默认为0.0.0.0，省略port时默认为25565
-r  --remote [[remote ip]:[remote port]]  转发目的地址，省略ip时默认为127.0.0.1，省略port时默认为25565
-c  --config <config.json>                DDNS配置文件
-d  --debug                               Debug模式
-v  --version                             显示版本
-t  --nat-type-test                       NAT类型测试（仅参考）
-q  --query [[server ip]:[server port]]   Minecraft: Java Edition服务器MOTD查询，省略ip时默认为127.0.0.1，省略port时默认为25565
```

#### NAT类型检测
##### Windows
1. 从Releases下载`NAT1_Traversal.exe`
2. 在下载目录按住`shift`并在空白处按右键，点击“在此处打开Powershell窗口”
3. 执行`.\NAT1_Traversal.exe -t`

##### Linux/MacOS/Windows
1. 从Releases下载`NAT1_Traversal.pyz`
2. 打开命令行并`cd`到下载目录
3. 执行`python3 ./NAT1_Traversal.pyz -t`

##### 结果分析
如果结果显示为`SYMMETRIC`则代表您无法继续使用项目的核心功能。

如果结果显示`PORT RESTRICTED CONE`则代表您必须登录到光猫/路由器中配置“虚拟服务器”(端口映射)规则

如果结果显示`FULL CONE`则代表您可以直接使用项目的核心功能而无需对网络进行配置。

如果结果显示`OPEN INTERNET`则代表您已经拥有公网IP地址，无需使用本软件。
