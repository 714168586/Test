### 脚本没有优化CPU 只能手动关闭CPU节能模式 设定最大性能模式
### 脚本中主要功能如下：
    1、关闭NUMA
    2、修改IO调度
    3、关闭iptables和selinux
    4、优化内核文件  

```
[root@39 ~]# cat test.sh 
#!/bin/bash


main_menu(){
echo "----------------------------------"
echo "please enter your choise:"
echo "(0) centos6"
echo "(1) centos7"
echo "(2) Exit Menu"
echo "----------------------------------"
read input

case $input in
    0)
    echo "centos6"
    sleep 1
    centos6
    sys
    echo -e "\033[44;37m sysctl.conf limits.conf 初始化完成 \033[0m "
    ;;

    1)
    echo centos7
    sleep 1
        centos7
        sys
        echo -e "\033[44;37m sysctl.conf limits.conf 初始化完成 \033[0m "
        ;;
    2)
        exit
        ;;
        *)
        echo "输入不能为空，请重新输入："
        main_menu
        ;;
esac
   
}

        centos6(){
        cp /etc/grub.conf{,.bak}
        echo -e "\033[44;37m 关闭NUMA \033[0m "
        sed -i '/kernel/ s/$/ numa=off/'  /etc/grub.conf
        echo -e "\033[44;37m 修改IO调度 \033[0m "
        echo deadline > /sys/block/sda/queue/scheduler 
        sed -i '/kernel/ s/$/ elevator=deadline/'  /etc/grub.conf 
        echo -e "\033[44;37m 关闭iptables和selinux \033[0m "
        service iptables stop
        chkconfig iptables off
        # close selinux
        setenforce 0 &&
        sed -i 's/SELINUX=enforcing/SELINUX=disabled/g'/etc/selinux/config
}

        centos7(){
        cp /etc/grub2.cfg{,.bak}
        echo -e "\033[44;37m 关闭NUMA \033[0m "
        sed -i '/kernel/ s/$/ numa=off/'  /etc/grub2.cfg
         echo -e "\033[44;37m 修改IO调度 \033[0m "
        echo deadline > /sys/block/sda/queue/scheduler 
        sed -i '/kernel/ s/$/ elevator=deadline/'  /etc/grub2.cfg 
        echo -e "\033[44;37m 关闭iptables和selinux \033[0m "
        systemctl stop firewalld.service 
        systemctl disable firewalld.service 
        # close selinux
        setenforce 0 &&
        sed -i 's/SELINUX=enforcing/SELINUX=disabled/g'/etc/sysconfig/selinux
}

function sys(){
        cat << EOF >  /etc/sysctl.conf 
net.ipv4.ip_forward = 0
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.default.accept_source_route = 0
kernel.sysrq = 0
kernel.core_uses_pid = 1
net.ipv4.tcp_syncookies = 1
net.bridge.bridge-nf-call-ip6tables = 0
net.bridge.bridge-nf-call-iptables = 0
net.bridge.bridge-nf-call-arptables = 0
kernel.msgmnb = 65536
kernel.msgmax = 65536
kernel.shmmax = 68719476736
kernel.shmall = 4294967296
fs.file-max = 65535
net.ipv4.tcp_max_tw_buckets = 50000
net.ipv4.ip_local_port_range = 1024    65000
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_tw_reuse = 1
net.core.somaxconn = 262144
net.core.netdev_max_backlog = 4096
net.ipv4.tcp_max_orphans = 262144
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_timestamps = 0
net.ipv4.tcp_synack_retries = 3
net.ipv4.tcp_syn_retries = 3
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 120
vm.swappiness=5
vm.dirty_background_ratio = 10
vm.dirty_background_bytes = 0
vm.dirty_ratio = 20
vm.dirty_bytes = 0
vm.dirty_writeback_centisecs = 500
vm.dirty_expire_centisecs = 3000
vm.min_free_kbytes=409600
vm.vfs_cache_pressure=200
EOF

cat << EOF >   /etc/security/limits.conf
* soft nofile 65535 
* hard nofile 65535 
* soft nproc 65535 
* hard nproc 65535
EOF

}
main_menu
```