# NAT1 Traversal

## 在面板中启用SO_REUSEPORT
您可以在以下方案中二选一进行设置。推荐使用[修改JAVA指令](#修改java指令)的操作方案，这样您无需为每个服务器重新创建启动脚本，只需要简单修改启动指令即可。

### 创建启动脚本
您可以将启动指令移动到一个`shell`脚本，并将`LD_PRELOAD=./hook_bind.so`放置到指令的最前方。

假设您原本在面板中的启动指令为：
```shell
java -Xmx2G -jar fabric-server-mc.1.21.8-loader.0.16.14-launcher.1.0.3.jar nogui
```

您需要将其修改为如下样式并填入到一个`shell`脚本，例如`run.sh`中，并为该脚本添加可执行权限`chmod +x run.sh`。
```shell
#!/bin/bash
LD_PRELOAD=./hook_bind.so java -Xmx2G -jar fabric-server-mc.1.21.8-loader.0.16.14-launcher.1.0.3.jar nogui
```

为了不在每个游戏文件夹内都放置`hook_bind.so`您也可以将其放置到一个固定位置，并将`LD_PRELOAD`值设置为绝对路径，例如：

```shell
#!/bin/bash
LD_PRELOAD=/usr/local/auto_minecraft_server/hook_bind.so java -Xmx2G -jar fabric-server-mc.1.21.8-loader.0.16.14-launcher.1.0.3.jar nogui
```

然后将您的面板启动指令修改为`sh run.sh`。

此时您可以正常使用面板启动服务器。

### 修改JAVA指令
您可以创建`/usr/local/bin/java-bind`文件填入如下内容，并为该文件添加可执行权限（`chmod +x /usr/local/bin/java21-bind`）。
```shell
#!/bin/bash
export LD_PRELOAD=/usr/local/auto_minecraft_server/hook_bind.so
exec java $@
```

然后在面板的启动指令中将`java`替换为`java-bind`即可。

## 更多用法

### WEB网站
#### Linux 3.9+ 共端口模式
对于数量庞大的WEB程序，在Linux 3.9+中实现共端口模式变得非常复杂。

多数WEB程序为了能让一个二进制文件在各种Linux发行版中运行而不用为每个发行版编译一个二进制文件，通常会采用静态链接的编译方式，

静态链接的使用导致WEB程序并不会去尝试从动态运行库中搜索函数，此时我们无法让WEB程序使用我们篡改的`bind`函数。

如果您的WEB程序采用了静态链接，您可以尝试修改源代码解除静态链接或者在`bind`之前为socket设置`SO_REUSEPORT`标志。

或者您应该采用更加通用的转发模式，当然这会对并发性能产生一些影响。

您需要将`type`设置为`web`而不是默认的`mcje`，其余设置与[MCJE共端口模式](../README.md#linux-39-共端口模式)的配置方式完全相同。

您现在可以使用`域名:端口`的方式访问您的WEB应用，但是随着映射IP地址的更新，端口号也会一起发生变化，

所以为了追踪端口的变化，您还需要根据[HTTP Redirect](https://github.com/Guation/http_redirect)项目的指引配置重定向，以固化域名访问入口。

#### Windows/MacOS/Linux 转发模式
您需要将`type`设置为`web`而不是默认的`mcje`，其余设置与[MCJE转发模式](../README.md#windowsmacoslinux-转发模式)的配置方式完全相同。

您现在可以使用`域名:端口`的方式访问您的WEB应用，但是随着映射IP地址的更新，端口号也会一起发生变化，

所以为了追踪端口的变化，您还需要根据[HTTP Redirect](https://github.com/Guation/http_redirect)项目的指引配置重定向，以固化域名访问入口。

### 通用TCP应用
#### Linux 3.9+ 共端口模式
与[WEB网站共端口模式](#linux-39-共端口模式)情况类似，hook很有可能无法生效，如果未生效您需要自行修改目标应用源代码以支持`SO_REUSEPORT`标志。

或者您应该采用更加通用的转发模式。

您需要将`type`设置为`tcp`而不是默认的`mcje`，其余设置与[MCJE共端口模式](../README.md#linux-39-共端口模式)的配置方式完全相同。

#### Windows/MacOS/Linux 转发模式
您需要将`type`设置为`tcp`而不是默认的`mcje`，其余设置与[MCJE转发模式](../README.md#windowsmacoslinux-转发模式)的配置方式完全相同。

### RDP远程桌面
#### Windows/MacOS/Linux 转发模式
RDP无法采用共端口模式，将`type`设置为`tcp`，将`dns`设置为`no_dns`。

Windows RDP默认使用端口为`3389`，因此我们需要配置`remote`为`Windows主机IP:3389`。

### 通用UDP应用
#### Windows/MacOS/Linux 转发模式
由于UDP无连接特性，通用UDP应用没有有效的通用方案确认映射隧道是否可用，因此无法采用共端口模式，将`type`设置为`udp`，将`dns`设置为`no_dns`。
