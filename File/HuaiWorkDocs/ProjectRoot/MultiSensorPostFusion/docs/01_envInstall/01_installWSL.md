# Install WSL
安装WSL的命令直接问豆包等相关AI助手
## WSL安装Ubuntu20.04
### WSL安装Ubuntu20.04 method1
打开windows终端,win + x，复制粘贴以下指令并执行
```{code-block} shell
:linenos:
:caption: WSL install Ubuntu2004 method2

wsl --install -d Ubuntu-20.04 --web-download
```

### WSL安装Ubuntu20.04 method2
如果方法1不生效的话，请把网址丢到浏览器：[https://aka.ms/wslubuntu2004](https://aka.ms/wslubuntu2004) 然后就会下载CanonicalGroupLimited.UbuntuonWindows_2004.2021.825.0.AppxBundle

进到下载的路径
```{code-block} shell
:linenos:
:caption: WSL install Ubuntu2004 Method2

Add-AppxPackage .\CanonicalGroupLimited.UbuntuonWindows_2004.2021.825.0.AppxBundle
```

完毕后打开开始菜单，搜索ubuntu 手动打开一次，会弹出黑色弹窗，然后要求你设置用户名跟密码

## 迁移wsl相关内容到非系统盘
从安装到的c盘给挪到d盘去
### 查看发行版并打印信息


```{code-block} shell
:linenos:
:caption: move ubuntu into Ddisk

# 查看发行版并打印信息
wsl -l -v
PS C:\Users\XCMG> wsl -l -v
  NAME      STATE           VERSION
* Ubuntu    Stopped         2

# 然后关闭
wsl --shutdown

# 然后在D盘建文件D:\WSL\Ubuntu2004同时迁移
wsl --export Ubuntu D:\WSL\Ubuntu2004\ubuntu_backup.tar

# 注销原先的
wsl --unregister Ubuntu
# 重新迁入
wsl --import Ubuntu D:\WSL\Ubuntu D:\WSL\Ubuntu2004\ubuntu_backup.tar --version 2
```


