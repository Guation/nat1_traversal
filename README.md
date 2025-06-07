# NAT1 Traversal

### 什么是NAT1 Traversal

#### 项目背景

随着互联网发展对于IPv4地址的需求量逐步增大，IPv4地址的总量是固定的，ISP(Internet Service Provider)出于盈利目而更倾向于将公网IPv4地址用于商用宽带而非家用宽带。

为了减少在家用宽带的IPv4地址投入量，ISP采用了NAT(Network Address Translation)技术使多名家用宽带用户共用同一个公网IPv4地址，这么做的副作用就是家用宽带的用户尝试对外提供的互联网服务时变得不可寻址。

ISP最常使用的NAT方案为NAPT(Network Address Port Translation)，而在进行网络端口地址转换的过程中，对于端口的映射方案和对外部来源的处理策略又衍生出了四个常见的NAT等级：

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
##### Windows（无python3环境）
1. 从Releases下载`NAT1_Traversal_nt.zip`
2. 右键压缩包选择“解压到NAT1_Traversal_nt”
3. 在`NAT1_Traversal_nt`目录中按住`shift`并在空白处按右键，点击“在此处打开Powershell窗口”
4. 执行`.\nat1_traversal.exe -t`

##### Windows（有python3环境）
1. 从Releases下载`NAT1_Traversal.tgz`或`NAT1_Traversal.zip`
2. 右键压缩包选择“解压到NAT1_Traversal”
3. 在`NAT1_Traversal`目录中按住`shift`并在空白处按右键，点击“在此处打开Powershell窗口”
4. 执行`python nat1_traversal.py -t`

##### Linux/MacOS
1. 从Releases下载`NAT1_Traversal.tgz`
2. 打开命令行并`cd`到下载目录
3. 使用`tar -xzvf NAT1_Traversal.tgz -C NAT1_Traversal ; cd NAT1_Traversal`
3. 执行`python3 nat1_traversal.py -t`

##### 结果分析
- 如果结果显示为`SYMMETRIC`则代表您无法使用本项目的核心功能。

- 如果结果显示`RESTRICTED CONE`或`PORT RESTRICTED CONE`则代表您必须登录到光猫/路由器中进行“(PORT) RESTRICTED CONE 改 FULL CONE”的步骤。

- 如果结果显示`FULL CONE`则代表您可以直接使用本项目的核心功能而无需对网络进行配置。

- 如果结果显示`OPEN INTERNET`则代表您已经拥有公网IP地址，无需使用本项目。

#### \(PORT\) RESTRICTED CONE 改 FULL CONE
##### 配置端口映射规则

您可以在光猫/路由器背面的铭牌中找到设备默认的管理地址和默认的管理员账户及密码。

部分路由器会要求您在首次登录时更改管理员密码，请以实际情况为准。

登录后在选项卡寻找类似“端口映射”、“端口转发”、“虚拟服务器”之类的字眼，并在选项卡中添加一条TCP规则，其中内外端口均填入25565（其他端口也可以，本例中使用25565），局域网IP填写MC服务器所在的主机IP。

如果您使用光猫+路由器的组合且光猫和路由器均处于路由模式而非桥接模式，则您需要在光猫和路由器中分别添加一条映射规则，在光猫中将端口映射的局域网IP指向路由器IP，而在路由器中将端口映射的局域网IP指向MC服务区所在的主机IP。

##### 再次检测NAT类型

此时需要在前一次的指令后指定测试端口`-l :25565`，由于我们只对25565进行了映射，如果不指定端口那么测试结果依旧是`PORT RESTRICTED CONE`

Windows使用`.\NAT1_Traversal.exe -t -l :25565`

MacOS/Linux使用`python3 NAT1_Traversal.py -t -l :25565`

此时如果测试结果为`FULL CONE`则代表您已完成配置，可进行开服。

#### 修改 config.json 文件中的dns配置信息
对于不同dns供应商，我们都提供了形如`config.供应商名.json`的配置模板以供参考，您可以使用`-c /path/to/your_config.json`的方法指定您的配置路径，也可以默认使用当前目录下的`config.json`。
##### 字段解释
- dns: dns供应商名称，目前支持`cloudflare`和`dynv6`，以及一个不使用dns的`nodns`

- id: 您登录dns管理界面的登录邮箱或者用户名，有些供应商无需提供此字段，此时值应为`null`

- token: 这是dns供应商给您的令牌

- domain: 您托管在dns供应商处的主域名，例如`example.com`

- sub_domain: 您想要绑定的子域名，此字段不包含主域名。例如您希望使用`mc.example.com`进服，那么您应该填入`mc`

##### id和token的获取方法

- [cloudflare](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)

- [dynv6](https://dynv6.com/keys)


#### 开服
##### Linux 3.9+
利用[Linux内核在3.9](https://lwn.net/Articles/542629/)引入的`SO_REUSEPORT`特性可以使多个应用程序监听同一端口，也就是意味着我们可以在MC服务器正在运行的同时使用和MC服务器相同的端口去申请并维持一个`TCP`内外端口的映射关系。

由于MC服务器本身未配置`SO_REUSEPORT`，我们需要使用Linux的`LD_PRELOAD`机制对JAVA的`bind`函数进行hook操作，使其在监听端口时激活`SO_REUSEPORT`特性。

在`hook_bind`文件夹中使用`make`指令生成`hook_bind.so`，复制该文件到您的服务器根目录中。

找到您的开服脚本`run.sh`或其他启动脚本，在`java`之前加入`LD_PRELOAD=./hook_bind.so`，

类似于`LD_PRELOAD=./hook_bind.so java @user_jvm_args.txt @libraries/net/neoforged/neoforge/21.1.133/unix_args.txt "$@"`

然后像往常一样启动服务器，如果您在日志中看见类似`Hooked bind: PID=1234, FD=5, setsockopt SO_REUSEPORT`的日志则代表修改已生效。

使用`python3 nat1_traversal.py -l :25565`，如果一切顺利，那么您将能使用`config.json`中配置的域名进服。

##### Windows/MacOS/Linux
在不可使用Linux 3.9+的`SO_REUSEPORT`时，我们可以让NAT1 Traversal作为中间代理转发我们的MC服务器流量。

此时您在mc服务器控制台将看到所有玩家均从`127.0.0.1`登录，您可以使用端口号和NAT1 Traversal日志判断用户来源ip。

使用NAT1 Traversal作为中间代理转发MC服务器流量时无需对mc服务器做任何修改，唯一需值得注意的是您需要将mc服务器的端口设置为非`25565`的端口（例如`25566`），因为`25565`端口我们需要提供给NAT1 Traversal使用。

Windows使用`.\nat1_traversal.exe -l :25565 -r :25566`

MacOS/Linux使用`python3 nat1_traversal.py -l :25565 -r :25566`

如果一切顺利，那么您将能使用`config.json`中配置的域名进服。
