# 磁盘清空相关命令

```{code-block} shell
:linenos:
:caption: 查看linux系统中的磁盘并格式化成ext4
# 推荐，直观，看 TYPE=disk 的就是裸盘，MOUNTPOINT为空=未挂载
lsblk
# 详细信息
sudo fdisk -l
# 查看文件系统UUID（后面永久挂载要用）
blkid
```

由于这块磁盘本来是windows的磁盘，需要重建GPT分区表并新建单分区
```{code-block} shell
:linenos:
:caption: 重建GPT分区表并新建单分区
# 新建GPT标签（覆盖原有所有分区）
sudo parted /dev/nvme1n1 mklabel gpt
# 整块盘建一个主分区
sudo parted /dev/nvme1n1 mkpart primary 0% 100%
# 通知内核刷新分区表
sudo partprobe /dev/nvme1n1
```

```{code-block} shell
:linenos:
:caption: 格式化
sudo mkfs.ext4 /dev/nvme1n1p1
# 执行下列命令，获取uuid
blkid /dev/nvme1n1p1
```

```{code-block} shell
:linenos:
:caption: 创建挂载目录并开机自动挂载

# 创建挂载目录
sudo mkdir -p /mnt/ssd
# 备份fstab（已经备份过也没关系，再备一次更稳妥）
sudo cp /etc/fstab /etc/fstab.bak
# 编辑fstab
sudo nano /etc/fstab
# 并加入下列命令
UUID=07a12a9b-3b98-4f8f-882a-856653217b08    /mnt/ssd    ext4    defaults    0 0

# 赋权给huai用户，不用sudo读写
sudo chown huai:huai /mnt/ssd



```











