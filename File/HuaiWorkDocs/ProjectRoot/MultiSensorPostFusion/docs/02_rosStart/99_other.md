# 其他内容
## linux 中文输入法
这个安装起来比较麻烦 参考AI 一步步走
bash ~/restart-fcitx.sh
直接使用fcitx -r 会导致浏览器挂掉

```{code-block} shell
:linenos:
:caption: install fcitx
cat > ~/restart-fcitx.sh <<'EOF'
#!/bin/bash
# 杀掉旧fcitx
pkill fcitx
# 杀掉conda里跑出来的dbus-daemon（元凶）
pkill -f '/miniconda3/bin/dbus-daemon'
# 临时把conda bin从PATH删掉，优先调用系统命令
export PATH=$(echo $PATH | sed 's|/mnt/Ddisk/soft/miniconda3/bin:||')
# 启动fcitx，用桌面自带dbus，不会自己新建dbus
fcitx -d
EOF
chmod +x ~/restart-fcitx.sh
# 不会调用conda 的dbus，我也不懂反正就这样把 哈哈
```

## linux 截图命令

```{code-block} shell
:linenos:
:caption: gnome-screenshot -a
# 截图完后会存在~/Pictures当中 
gnome-screenshot -a
```

## 启动VScode
启动VScode时候可以关闭终端
```{code-block} shell
:linenos:
:caption: VScode start
setsid code
# 这里的code是我自己启动VScode的简写
```

## sphinx添加note自定义配色 

```{code-block} css
:linenos:
:caption: add-color
/* purple：基于note，i图标 */
.admonition.purple {
  border-left: 0.2rem solid #9333ea !important;
  background-color: #f5edff !important;
}
.admonition.purple > .admonition-title {
  background-color: #9333ea !important;
  color: #ffffff !important;
}

然后在对应正文中添加以下使得自定义颜色生效
:::{admonition} 紫色自定义框
:class: purple
自定义紫色提示内容
:::

```