[TOC]
### 环境：
    72.127.2.50	master	 db01    
    72.127.2.51     slave 	 db02
    72.127.2.52	slave 	 db03
    72.127.2.119     vip            
### 主从环境搭建：
    主库:
    
    grant replication slave on *.* to 'repl'@'72.127.2.%' identified by '123456';
    grant all privileges on *.* to 'huha'@'%' identified by '123456';
    
    从库：
    
    change master to master_host='72.127.2.50',master_user='repl',master_password='123456',master_port=3306,MASTER_AUTO_POSITION = 1;
    start slave;
    show slave status\G;

### 三台服务器做免秘钥：
    略

### mha安装：
#### 安装依赖（epel扩展源）
    # yum install perl-DBD-MySQL
    # yum install perl-Config-Tiny
    # yum install perl-Log-Dispatch
    # yum install perl-Parallel-ForkManage

#### 所有机器安装node:
    yum install mha4mysql-node-0.56-0.el6.noarch.rpm

#### db03 安装manager:
    yum install mha4mysql-manager-0.56-0.el6.noarch.rpm
#### manager创建目录：
    mkdir -p /etc/masterha/
    mkdir -p /var/log/masterha/app1

#### 配置文件如下：
```
[root@db03 masterha]# cat app1.conf 
[server default]
#MySQL的用户和密码
user=huha
password=123456

#系统ssh用户
ssh_user=root

#复制用户
repl_user=repl
repl_password= 123456


#监控
ping_interval=1
#shutdown_script=""

#切换调用的脚本
master_ip_failover_script= /etc/masterha/master_ip_failover.pl    # 设置自动failover时候的切换脚本
master_ip_online_change_script= /etc/masterha/master_ip_online_change # 设置手动切换时候的切换脚本

log_level=debug

#mha manager工作目录
manager_workdir = /var/log/masterha/app1
manager_log = /var/log/masterha/app1/app1.log
remote_workdir = /var/log/masterha/app1

[server1]
hostname=db01
master_binlog_dir = /data/mysql/mysql_3306/logs
candidate_master = 1
check_repl_delay = 0     #用防止master故障时，切换时slave有延迟，卡在那里切不过来。

[server2]
hostname=db02
master_binlog_dir=/data/mysql/mysql_3306/logs
candidate_master=1
check_repl_delay=0

[server3]
hostname=db03
master_binlog_dir=/data/mysql/mysql_3306/logs
candidate_master=1
check_repl_delay=0
```
#### 切换脚本如下：
```
[root@db03 masterha]# cat  master_ip_failover.pl     
#!/usr/bin/env perl

use strict;
use warnings FATAL => 'all';

use Getopt::Long;

my (
    $command,          $ssh_user,        $orig_master_host, $orig_master_ip,
    $orig_master_port, $new_master_host, $new_master_ip,    $new_master_port
);

my $vip = '72.127.2.119/24';
my $key = '1';
my $ssh_start_vip = "/sbin/ip addr add $vip dev eth0";
my $ssh_stop_vip = "/sbin/ip addr del $vip dev eth0";

GetOptions(
    'command=s'          => \$command,
    'ssh_user=s'         => \$ssh_user,
    'orig_master_host=s' => \$orig_master_host,
    'orig_master_ip=s'   => \$orig_master_ip,
    'orig_master_port=i' => \$orig_master_port,
    'new_master_host=s'  => \$new_master_host,
    'new_master_ip=s'    => \$new_master_ip,
    'new_master_port=i'  => \$new_master_port,
);

exit &main();

sub main {

    print "\n\nIN SCRIPT TEST====$ssh_stop_vip==$ssh_start_vip===\n\n";

    if ( $command eq "stop" || $command eq "stopssh" ) {

        my $exit_code = 1;
        eval {
            print "Disabling the VIP on old master: $orig_master_host \n";
            &stop_vip();
            $exit_code = 0;
        };
        if ($@) {
            warn "Got Error: $@\n";
            exit $exit_code;
        }
        exit $exit_code;
    }
    elsif ( $command eq "start" ) {

        my $exit_code = 10;
        eval {
            print "Enabling the VIP - $vip on the new master - $new_master_host \n";
            &start_vip();
            $exit_code = 0;
        };
        if ($@) {
            warn $@;
            exit $exit_code;
        }
        exit $exit_code;
    }
    elsif ( $command eq "status" ) {
        print "Checking the Status of the script.. OK \n";
        exit 0;
    }
    else {
        &usage();
        exit 1;
    }
}

sub start_vip() {
    `ssh $ssh_user\@$new_master_host \" $ssh_start_vip \"`;
}
sub stop_vip() {
     return 0  unless  ($ssh_user);
    `ssh $ssh_user\@$orig_master_host \" $ssh_stop_vip \"`;
}

sub usage {
    print
    "Usage: master_ip_failover --command=start|stop|stopssh|status --orig_master_host=host --orig_master_ip=ip --orig_master_port=port --new_master_host=host --new_master_ip=ip --new_master_port=port\n";
}
```


### 验证SSH

    [root@db03 shell]# masterha_check_ssh --conf=/etc/masterha/app1.conf  
    Wed Nov  1 18:04:11 2017 - [warning] Global configuration file /etc/masterha_default.cnf not found. Skipping.
    Wed Nov  1 18:04:11 2017 - [info] Reading application default configuration from /etc/masterha/app1.conf..
    Wed Nov  1 18:04:11 2017 - [info] Reading server configuration from /etc/masterha/app1.conf..
    Wed Nov  1 18:04:11 2017 - [info] Starting SSH connection tests..
    Wed Nov  1 18:04:14 2017 - [debug] 
    Wed Nov  1 18:04:11 2017 - [debug]  Connecting via SSH from root@db01(72.127.2.50:22) to root@db02(72.127.2.51:22)..
    Wed Nov  1 18:04:13 2017 - [debug]   ok.
    Wed Nov  1 18:04:13 2017 - [debug]  Connecting via SSH from root@db01(72.127.2.50:22) to root@db03(72.127.2.52:22)..
    Wed Nov  1 18:04:14 2017 - [debug]   ok.
    Wed Nov  1 18:04:14 2017 - [debug] 
    Wed Nov  1 18:04:12 2017 - [debug]  Connecting via SSH from root@db03(72.127.2.52:22) to root@db01(72.127.2.50:22)..
    Wed Nov  1 18:04:14 2017 - [debug]   ok.
    Wed Nov  1 18:04:14 2017 - [debug]  Connecting via SSH from root@db03(72.127.2.52:22) to root@db02(72.127.2.51:22)..
    Wed Nov  1 18:04:14 2017 - [debug]   ok.
    Wed Nov  1 18:04:14 2017 - [debug] 
    Wed Nov  1 18:04:12 2017 - [debug]  Connecting via SSH from root@db02(72.127.2.51:22) to root@db01(72.127.2.50:22)..
    Wed Nov  1 18:04:14 2017 - [debug]   ok.
    Wed Nov  1 18:04:14 2017 - [debug]  Connecting via SSH from root@db02(72.127.2.51:22) to root@db03(72.127.2.52:22)..
    Wed Nov  1 18:04:14 2017 - [debug]   ok.
    Wed Nov  1 18:04:14 2017 - [info] All SSH connection tests passed successfully.
### 检查整个复制环境状况
    [root@db03 masterha]#  masterha_check_repl --conf=/etc/masterha/app1.conf 
    Thu Nov  2 09:20:14 2017 - [warning] Global configuration file /etc/masterha_default.cnf not found. Skipping.
    Thu Nov  2 09:20:14 2017 - [info] Reading application default configuration from /etc/masterha/app1.conf..
    Thu Nov  2 09:20:14 2017 - [info] Reading server configuration from /etc/masterha/app1.conf..
    Thu Nov  2 09:20:14 2017 - [info] MHA::MasterMonitor version 0.56.
    Thu Nov  2 09:20:14 2017 - [debug] Connecting to servers..
    Thu Nov  2 09:20:14 2017 - [debug]  Connected to: db01(72.127.2.50:3306), user=huha
    Thu Nov  2 09:20:14 2017 - [debug]  Number of slave worker threads on host db01(72.127.2.50:3306): 0
    Thu Nov  2 09:20:14 2017 - [debug]  Connected to: db02(72.127.2.51:3306), user=huha
    Thu Nov  2 09:20:14 2017 - [debug]  Number of slave worker threads on host db02(72.127.2.51:3306): 0
    Thu Nov  2 09:20:14 2017 - [debug]  Connected to: db03(72.127.2.52:3306), user=huha
    Thu Nov  2 09:20:14 2017 - [debug]  Number of slave worker threads on host db03(72.127.2.52:3306): 0
    Thu Nov  2 09:20:14 2017 - [debug]  Comparing MySQL versions..
    Thu Nov  2 09:20:14 2017 - [debug]   Comparing MySQL versions done.
    Thu Nov  2 09:20:14 2017 - [debug] Connecting to servers done.
    Thu Nov  2 09:20:14 2017 - [info] GTID failover mode = 1
    Thu Nov  2 09:20:14 2017 - [info] Dead Servers:
    Thu Nov  2 09:20:14 2017 - [info] Alive Servers:
    Thu Nov  2 09:20:14 2017 - [info]   db01(72.127.2.50:3306)
    Thu Nov  2 09:20:14 2017 - [info]   db02(72.127.2.51:3306)
    Thu Nov  2 09:20:14 2017 - [info]   db03(72.127.2.52:3306)
    Thu Nov  2 09:20:14 2017 - [info] Alive Slaves:
    Thu Nov  2 09:20:14 2017 - [info]   db02(72.127.2.51:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
    Thu Nov  2 09:20:14 2017 - [info]     GTID ON
    Thu Nov  2 09:20:14 2017 - [debug]    Relay log info repository: FILE
    Thu Nov  2 09:20:14 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
    Thu Nov  2 09:20:14 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
    Thu Nov  2 09:20:14 2017 - [info]   db03(72.127.2.52:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
    Thu Nov  2 09:20:14 2017 - [info]     GTID ON
    Thu Nov  2 09:20:14 2017 - [debug]    Relay log info repository: FILE
    Thu Nov  2 09:20:14 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
    Thu Nov  2 09:20:14 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
    Thu Nov  2 09:20:14 2017 - [info] Current Alive Master: db01(72.127.2.50:3306)
    Thu Nov  2 09:20:14 2017 - [info] Checking slave configurations..
    Thu Nov  2 09:20:14 2017 - [info]  read_only=1 is not set on slave db02(72.127.2.51:3306).
    Thu Nov  2 09:20:14 2017 - [info]  read_only=1 is not set on slave db03(72.127.2.52:3306).
    Thu Nov  2 09:20:14 2017 - [info] Checking replication filtering settings..
    Thu Nov  2 09:20:14 2017 - [info]  binlog_do_db= , binlog_ignore_db= 
    Thu Nov  2 09:20:14 2017 - [info]  Replication filtering check ok.
    Thu Nov  2 09:20:14 2017 - [info] GTID (with auto-pos) is supported. Skipping all SSH and Node package checking.
    Thu Nov  2 09:20:14 2017 - [info] Checking SSH publickey authentication settings on the current master..
    Thu Nov  2 09:20:14 2017 - [debug] SSH connection test to db01, option -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o BatchMode=yes -o ConnectTimeout=5, timeout 5
    Thu Nov  2 09:20:15 2017 - [info] HealthCheck: SSH to db01 is reachable.
    Thu Nov  2 09:20:15 2017 - [info] 
    db01(72.127.2.50:3306) (current master)
     +--db02(72.127.2.51:3306)
     +--db03(72.127.2.52:3306)
    
    Thu Nov  2 09:20:15 2017 - [info] Checking replication health on db02..
    Thu Nov  2 09:20:15 2017 - [info]  ok.
    Thu Nov  2 09:20:15 2017 - [info] Checking replication health on db03..
    Thu Nov  2 09:20:15 2017 - [info]  ok.
    Thu Nov  2 09:20:15 2017 - [info] Checking master_ip_failover_script status:
    Thu Nov  2 09:20:15 2017 - [info]   /etc/masterha/master_ip_failover.pl --command=status --ssh_user=root --orig_master_host=db01 --orig_master_ip=72.127.2.50 --orig_master_port=3306 
    
    
    IN SCRIPT TEST====/sbin/ip addr del 72.127.2.119/24 dev eth0==/sbin/ip addr add 72.127.2.119/24 dev eth0===
    
    Checking the Status of the script.. OK 
    Thu Nov  2 09:20:15 2017 - [info]  OK.
    Thu Nov  2 09:20:15 2017 - [warning] shutdown_script is not defined.
    Thu Nov  2 09:20:15 2017 - [debug]  Disconnected from db01(72.127.2.50:3306)
    Thu Nov  2 09:20:15 2017 - [debug]  Disconnected from db02(72.127.2.51:3306)
    Thu Nov  2 09:20:15 2017 - [debug]  Disconnected from db03(72.127.2.52:3306)
    Thu Nov  2 09:20:15 2017 - [info] Got exit code 0 (Not master dead).
    
    MySQL Replication Health is OK.




### 开启MHA Manager监控
    masterha_manager --conf=/etc/masterha/app1.conf &  

### 通过脚本的方式管理虚拟ip（开启manager之前添加）
        注意：master 需要手动添加虚拟ip
        ip addr add 72.127.2.119/24 dev eth0


为了防止脑裂发生，推荐生产环境采用脚本的方式来管理虚拟ip，而不是使用keepalived来完成。
    到这基本搭建完成   还可以添加个报警脚本  

### 验证
#### 一.自动Failover（必须先启动MHA Manager，否则无法自动切换，当然手动切换不需要开启MHA Manager监控）

```
[root@db03 app1]# cat app1.log 
Wed Nov  1 17:14:41 2017 - [info] MHA::MasterMonitor version 0.56.
Wed Nov  1 17:14:41 2017 - [debug] Connecting to servers..
Wed Nov  1 17:14:41 2017 - [debug]  Connected to: db01(72.127.2.50:3306), user=huha
Wed Nov  1 17:14:41 2017 - [debug]  Number of slave worker threads on host db01(72.127.2.50:3306): 0
Wed Nov  1 17:14:41 2017 - [debug]  Connected to: db02(72.127.2.51:3306), user=huha
Wed Nov  1 17:14:41 2017 - [debug]  Number of slave worker threads on host db02(72.127.2.51:3306): 0
Wed Nov  1 17:14:41 2017 - [debug]  Connected to: db03(72.127.2.52:3306), user=huha
Wed Nov  1 17:14:41 2017 - [debug]  Number of slave worker threads on host db03(72.127.2.52:3306): 0
Wed Nov  1 17:14:41 2017 - [debug]  Comparing MySQL versions..
Wed Nov  1 17:14:41 2017 - [debug]   Comparing MySQL versions done.
Wed Nov  1 17:14:41 2017 - [debug] Connecting to servers done.
Wed Nov  1 17:14:41 2017 - [info] GTID failover mode = 1
Wed Nov  1 17:14:41 2017 - [info] Dead Servers:
Wed Nov  1 17:14:41 2017 - [info] Alive Servers:
Wed Nov  1 17:14:41 2017 - [info]   db01(72.127.2.50:3306)
Wed Nov  1 17:14:41 2017 - [info]   db02(72.127.2.51:3306)
Wed Nov  1 17:14:41 2017 - [info]   db03(72.127.2.52:3306)
Wed Nov  1 17:14:41 2017 - [info] Alive Slaves:
Wed Nov  1 17:14:41 2017 - [info]   db02(72.127.2.51:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:14:41 2017 - [info]     GTID ON
Wed Nov  1 17:14:41 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:14:41 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:14:41 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:14:41 2017 - [info]   db03(72.127.2.52:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:14:41 2017 - [info]     GTID ON
Wed Nov  1 17:14:41 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:14:41 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:14:41 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:14:41 2017 - [info] Current Alive Master: db01(72.127.2.50:3306)
Wed Nov  1 17:14:41 2017 - [info] Checking slave configurations..
Wed Nov  1 17:14:41 2017 - [info]  read_only=1 is not set on slave db02(72.127.2.51:3306).
Wed Nov  1 17:14:41 2017 - [info]  read_only=1 is not set on slave db03(72.127.2.52:3306).
Wed Nov  1 17:14:41 2017 - [info] Checking replication filtering settings..
Wed Nov  1 17:14:41 2017 - [info]  binlog_do_db= , binlog_ignore_db= 
Wed Nov  1 17:14:41 2017 - [info]  Replication filtering check ok.
Wed Nov  1 17:14:41 2017 - [info] GTID (with auto-pos) is supported. Skipping all SSH and Node package checking.
Wed Nov  1 17:14:41 2017 - [info] Checking SSH publickey authentication settings on the current master..
Wed Nov  1 17:14:41 2017 - [debug] SSH connection test to db01, option -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o BatchMode=yes -o ConnectTimeout=5, timeout 5
Wed Nov  1 17:14:42 2017 - [info] HealthCheck: SSH to db01 is reachable.
Wed Nov  1 17:14:42 2017 - [info] 
db01(72.127.2.50:3306) (current master)
 +--db02(72.127.2.51:3306)
 +--db03(72.127.2.52:3306)

Wed Nov  1 17:14:42 2017 - [info] Checking master_ip_failover_script status:
Wed Nov  1 17:14:42 2017 - [info]   /etc/masterha/master_ip_failover.pl --command=status --ssh_user=root --orig_master_host=db01 --orig_master_ip=72.127.2.50 --orig_master_port=3306 


IN SCRIPT TEST====/sbin/ip addr del 72.127.2.119/24 dev eth0==/sbin/ip addr add 72.127.2.119/24 dev eth0===

Checking the Status of the script.. OK 
Wed Nov  1 17:14:42 2017 - [info]  OK.
Wed Nov  1 17:14:42 2017 - [warning] shutdown_script is not defined.
Wed Nov  1 17:14:42 2017 - [debug]  Disconnected from db01(72.127.2.50:3306)
Wed Nov  1 17:14:42 2017 - [debug]  Disconnected from db02(72.127.2.51:3306)
Wed Nov  1 17:14:42 2017 - [debug]  Disconnected from db03(72.127.2.52:3306)
Wed Nov  1 17:14:42 2017 - [debug] SSH check command: exit 0
Wed Nov  1 17:14:42 2017 - [info] Set master ping interval 1 seconds.
Wed Nov  1 17:14:42 2017 - [warning] secondary_check_script is not defined. It is highly recommended setting it to check master reachability from two or more routes.
Wed Nov  1 17:14:42 2017 - [info] Starting ping health check on db01(72.127.2.50:3306)..
Wed Nov  1 17:14:42 2017 - [debug] Connected on master.
Wed Nov  1 17:14:42 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:14:42 2017 - [debug] Trying to get advisory lock..
Wed Nov  1 17:14:42 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:19 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:19 2017 - [info] Executing SSH check script: exit 0
Wed Nov  1 17:17:19 2017 - [debug] SSH connection test to db01, option -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o BatchMode=yes -o ConnectTimeout=5, timeout 5
Wed Nov  1 17:17:20 2017 - [debug] Connected on master.
Wed Nov  1 17:17:20 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:20 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:21 2017 - [warning] Got timeout on SSH Check child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:42 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:43 2017 - [info] Executing SSH check script: exit 0
Wed Nov  1 17:17:43 2017 - [debug] SSH connection test to db01, option -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o BatchMode=yes -o ConnectTimeout=5, timeout 5
Wed Nov  1 17:17:43 2017 - [debug] Connected on master.
Wed Nov  1 17:17:43 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:43 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:44 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:44 2017 - [debug] Connected on master.
Wed Nov  1 17:17:44 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:44 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:45 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:45 2017 - [debug] Connected on master.
Wed Nov  1 17:17:45 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:45 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:46 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:46 2017 - [debug] Connected on master.
Wed Nov  1 17:17:46 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:46 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:47 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:47 2017 - [debug] Connected on master.
Wed Nov  1 17:17:47 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:47 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:48 2017 - [warning] HealthCheck: Got timeout on checking SSH connection to db01! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 342.
Wed Nov  1 17:17:48 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:48 2017 - [debug] Connected on master.
Wed Nov  1 17:17:48 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:48 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:17:49 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:17:49 2017 - [debug] Connected on master.
Wed Nov  1 17:17:49 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:17:49 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:19:12 2017 - [warning] Got timeout on MySQL Ping(SELECT) child process and killed it! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 431.
Wed Nov  1 17:19:13 2017 - [info] Executing SSH check script: exit 0
Wed Nov  1 17:19:13 2017 - [debug] SSH connection test to db01, option -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o BatchMode=yes -o ConnectTimeout=5, timeout 5
Wed Nov  1 17:19:14 2017 - [warning] Got error on MySQL connect: 2003 (Can't connect to MySQL server on '72.127.2.50' (4))
Wed Nov  1 17:19:14 2017 - [warning] Connection failed 2 time(s)..
Wed Nov  1 17:19:17 2017 - [debug] Connected on master.
Wed Nov  1 17:19:17 2017 - [debug] Set short wait_timeout on master: 2 seconds
Wed Nov  1 17:19:17 2017 - [info] Ping(SELECT) succeeded, waiting until MySQL doesn't respond..
Wed Nov  1 17:19:18 2017 - [warning] HealthCheck: Got timeout on checking SSH connection to db01! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 342.
Wed Nov  1 17:19:58 2017 - [warning] Got error on MySQL select ping: 2006 (MySQL server has gone away)
Wed Nov  1 17:19:58 2017 - [info] Executing SSH check script: exit 0
Wed Nov  1 17:19:58 2017 - [debug] SSH connection test to db01, option -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o BatchMode=yes -o ConnectTimeout=5, timeout 5
Wed Nov  1 17:19:59 2017 - [warning] Got error on MySQL connect: 2013 (Lost connection to MySQL server at 'reading initial communication packet', system error: 111)
Wed Nov  1 17:19:59 2017 - [warning] Connection failed 2 time(s)..
Wed Nov  1 17:20:00 2017 - [warning] Got error on MySQL connect: 2013 (Lost connection to MySQL server at 'reading initial communication packet', system error: 111)
Wed Nov  1 17:20:00 2017 - [warning] Connection failed 3 time(s)..
Wed Nov  1 17:20:01 2017 - [warning] Got error on MySQL connect: 2013 (Lost connection to MySQL server at 'reading initial communication packet', system error: 111)
Wed Nov  1 17:20:01 2017 - [warning] Connection failed 4 time(s)..
Wed Nov  1 17:20:03 2017 - [warning] HealthCheck: Got timeout on checking SSH connection to db01! at /usr/share/perl5/vendor_perl/MHA/HealthCheck.pm line 342.
Wed Nov  1 17:20:03 2017 - [warning] Master is not reachable from health checker!
Wed Nov  1 17:20:03 2017 - [warning] Master db01(72.127.2.50:3306) is not reachable!
Wed Nov  1 17:20:03 2017 - [warning] SSH is NOT reachable.
Wed Nov  1 17:20:03 2017 - [info] Connecting to a master server failed. Reading configuration file /etc/masterha_default.cnf and /etc/masterha/app1.conf again, and trying to connect to all servers to check server status..
Wed Nov  1 17:20:03 2017 - [warning] Global configuration file /etc/masterha_default.cnf not found. Skipping.
Wed Nov  1 17:20:04 2017 - [info] Reading application default configuration from /etc/masterha/app1.conf..
Wed Nov  1 17:20:04 2017 - [info] Reading server configuration from /etc/masterha/app1.conf..
Wed Nov  1 17:20:04 2017 - [debug] Skipping connecting to dead master db01(72.127.2.50:3306).
Wed Nov  1 17:20:04 2017 - [debug] Connecting to servers..
Wed Nov  1 17:20:09 2017 - [debug]  Connected to: db02(72.127.2.51:3306), user=huha
Wed Nov  1 17:20:09 2017 - [debug]  Number of slave worker threads on host db02(72.127.2.51:3306): 0
Wed Nov  1 17:20:09 2017 - [debug]  Connected to: db03(72.127.2.52:3306), user=huha
Wed Nov  1 17:20:09 2017 - [debug]  Number of slave worker threads on host db03(72.127.2.52:3306): 0
Wed Nov  1 17:20:09 2017 - [debug]  Comparing MySQL versions..
Wed Nov  1 17:20:09 2017 - [debug]   Comparing MySQL versions done.
Wed Nov  1 17:20:09 2017 - [debug] Connecting to servers done.
Wed Nov  1 17:20:09 2017 - [info] GTID failover mode = 1
Wed Nov  1 17:20:09 2017 - [info] Dead Servers:
Wed Nov  1 17:20:09 2017 - [info]   db01(72.127.2.50:3306)
Wed Nov  1 17:20:09 2017 - [info] Alive Servers:
Wed Nov  1 17:20:09 2017 - [info]   db02(72.127.2.51:3306)
Wed Nov  1 17:20:09 2017 - [info]   db03(72.127.2.52:3306)
Wed Nov  1 17:20:09 2017 - [info] Alive Slaves:
Wed Nov  1 17:20:09 2017 - [info]   db02(72.127.2.51:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:09 2017 - [info]     GTID ON
Wed Nov  1 17:20:09 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:09 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:09 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:09 2017 - [info]   db03(72.127.2.52:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:09 2017 - [info]     GTID ON
Wed Nov  1 17:20:09 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:09 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:09 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:09 2017 - [info] Checking slave configurations..
Wed Nov  1 17:20:09 2017 - [info]  read_only=1 is not set on slave db02(72.127.2.51:3306).
Wed Nov  1 17:20:09 2017 - [info]  read_only=1 is not set on slave db03(72.127.2.52:3306).
Wed Nov  1 17:20:09 2017 - [info] Checking replication filtering settings..
Wed Nov  1 17:20:09 2017 - [info]  Replication filtering check ok.
Wed Nov  1 17:20:09 2017 - [info] Master is down!
Wed Nov  1 17:20:09 2017 - [info] Terminating monitoring script.
Wed Nov  1 17:20:09 2017 - [info] Got exit code 20 (Master dead).
Wed Nov  1 17:20:09 2017 - [info] MHA::MasterFailover version 0.56.
Wed Nov  1 17:20:09 2017 - [info] Starting master failover.
Wed Nov  1 17:20:09 2017 - [info] 
Wed Nov  1 17:20:09 2017 - [info] * Phase 1: Configuration Check Phase..
Wed Nov  1 17:20:09 2017 - [info] 
Wed Nov  1 17:20:11 2017 - [debug] Skipping connecting to dead master db01.
Wed Nov  1 17:20:11 2017 - [debug] Connecting to servers..
Wed Nov  1 17:20:12 2017 - [debug]  Connected to: db02(72.127.2.51:3306), user=huha
Wed Nov  1 17:20:12 2017 - [debug]  Number of slave worker threads on host db02(72.127.2.51:3306): 0
Wed Nov  1 17:20:12 2017 - [debug]  Connected to: db03(72.127.2.52:3306), user=huha
Wed Nov  1 17:20:12 2017 - [debug]  Number of slave worker threads on host db03(72.127.2.52:3306): 0
Wed Nov  1 17:20:12 2017 - [debug]  Comparing MySQL versions..
Wed Nov  1 17:20:12 2017 - [debug]   Comparing MySQL versions done.
Wed Nov  1 17:20:12 2017 - [debug] Connecting to servers done.
Wed Nov  1 17:20:12 2017 - [info] GTID failover mode = 1
Wed Nov  1 17:20:12 2017 - [info] Dead Servers:
Wed Nov  1 17:20:12 2017 - [info]   db01(72.127.2.50:3306)
Wed Nov  1 17:20:12 2017 - [info] Checking master reachability via MySQL(double check)...
Wed Nov  1 17:20:12 2017 - [info]  ok.
Wed Nov  1 17:20:12 2017 - [info] Alive Servers:
Wed Nov  1 17:20:12 2017 - [info]   db02(72.127.2.51:3306)
Wed Nov  1 17:20:12 2017 - [info]   db03(72.127.2.52:3306)
Wed Nov  1 17:20:12 2017 - [info] Alive Slaves:
Wed Nov  1 17:20:12 2017 - [info]   db02(72.127.2.51:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:12 2017 - [info]     GTID ON
Wed Nov  1 17:20:12 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:12 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:12 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:12 2017 - [info]   db03(72.127.2.52:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:12 2017 - [info]     GTID ON
Wed Nov  1 17:20:12 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:12 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:12 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:12 2017 - [info] Starting GTID based failover.
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] ** Phase 1: Configuration Check Phase completed.
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] * Phase 2: Dead Master Shutdown Phase..
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] Forcing shutdown so that applications never connect to the current master..
Wed Nov  1 17:20:12 2017 - [debug]  Stopping IO thread on db02(72.127.2.51:3306)..
Wed Nov  1 17:20:12 2017 - [info] Executing master IP deactivation script:
Wed Nov  1 17:20:12 2017 - [info]   /etc/masterha/master_ip_failover.pl --orig_master_host=db01 --orig_master_ip=72.127.2.50 --orig_master_port=3306 --command=stop 
Wed Nov  1 17:20:12 2017 - [debug]  Stopping IO thread on db03(72.127.2.52:3306)..
Wed Nov  1 17:20:12 2017 - [debug]  Stop IO thread on db03(72.127.2.52:3306) done.


IN SCRIPT TEST====/sbin/ip addr del 72.127.2.119/24 dev eth0==/sbin/ip addr add 72.127.2.119/24 dev eth0===

Disabling the VIP on old master: db01 
Wed Nov  1 17:20:12 2017 - [info]  done.
Wed Nov  1 17:20:12 2017 - [warning] shutdown_script is not set. Skipping explicit shutting down of the dead master.
Wed Nov  1 17:20:12 2017 - [debug]  Stop IO thread on db02(72.127.2.51:3306) done.
Wed Nov  1 17:20:12 2017 - [info] * Phase 2: Dead Master Shutdown Phase completed.
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] * Phase 3: Master Recovery Phase..
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] * Phase 3.1: Getting Latest Slaves Phase..
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [debug] Fetching current slave status..
Wed Nov  1 17:20:12 2017 - [debug]  Fetching current slave status done.
Wed Nov  1 17:20:12 2017 - [info] The latest binary log file/position on all slaves is mysql-bin.000002:209165788
Wed Nov  1 17:20:12 2017 - [info] Retrieved Gtid Set: 24ce300b-98ed-11e7-8156-000c29809308:1-12155
Wed Nov  1 17:20:12 2017 - [info] Latest slaves (Slaves that received relay log files to the latest):
Wed Nov  1 17:20:12 2017 - [info]   db03(72.127.2.52:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:12 2017 - [info]     GTID ON
Wed Nov  1 17:20:12 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:12 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:12 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:12 2017 - [info] The oldest binary log file/position on all slaves is mysql-bin.000002:130801566
Wed Nov  1 17:20:12 2017 - [info] Retrieved Gtid Set: 24ce300b-98ed-11e7-8156-000c29809308:1-1218
Wed Nov  1 17:20:12 2017 - [info] Oldest slaves:
Wed Nov  1 17:20:12 2017 - [info]   db02(72.127.2.51:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:12 2017 - [info]     GTID ON
Wed Nov  1 17:20:12 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:12 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:12 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] * Phase 3.3: Determining New Master Phase..
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] Searching new master from slaves..
Wed Nov  1 17:20:12 2017 - [info]  Candidate masters from the configuration file:
Wed Nov  1 17:20:12 2017 - [info]   db02(72.127.2.51:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:12 2017 - [info]     GTID ON
Wed Nov  1 17:20:12 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:12 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:12 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:12 2017 - [info]   db03(72.127.2.52:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Wed Nov  1 17:20:12 2017 - [info]     GTID ON
Wed Nov  1 17:20:12 2017 - [debug]    Relay log info repository: FILE
Wed Nov  1 17:20:12 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Wed Nov  1 17:20:12 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Wed Nov  1 17:20:12 2017 - [info]  Non-candidate masters:
Wed Nov  1 17:20:12 2017 - [info]  Searching from candidate_master slaves which have received the latest relay log events..
Wed Nov  1 17:20:12 2017 - [info] New master is db03(72.127.2.52:3306)
Wed Nov  1 17:20:12 2017 - [info] Starting master failover..
Wed Nov  1 17:20:12 2017 - [info] 
From:
db01(72.127.2.50:3306) (current master)
 +--db02(72.127.2.51:3306)
 +--db03(72.127.2.52:3306)

To:
db03(72.127.2.52:3306) (new master)
 +--db02(72.127.2.51:3306)
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info] * Phase 3.3: New Master Recovery Phase..
Wed Nov  1 17:20:12 2017 - [info] 
Wed Nov  1 17:20:12 2017 - [info]  Waiting all logs to be applied.. 
Wed Nov  1 17:20:13 2017 - [info]   done.
Wed Nov  1 17:20:13 2017 - [debug]  Stopping slave IO/SQL thread on db03(72.127.2.52:3306)..
Wed Nov  1 17:20:13 2017 - [debug]   done.
Wed Nov  1 17:20:13 2017 - [info] Getting new master's binlog name and position..
Wed Nov  1 17:20:13 2017 - [info]  mysql-bin.000002:132070670
Wed Nov  1 17:20:13 2017 - [info]  All other slaves should start replication from here. Statement should be: CHANGE MASTER TO MASTER_HOST='db03 or 72.127.2.52', MASTER_PORT=3306, MASTER_AUTO_POSITION=1, MASTER_USER='repl', MASTER_PASSWORD='xxx';
Wed Nov  1 17:20:13 2017 - [info] Master Recovery succeeded. File:Pos:Exec_Gtid_Set: mysql-bin.000002, 132070670, 24ce300b-98ed-11e7-8156-000c29809308:1-12155
Wed Nov  1 17:20:13 2017 - [info] Executing master IP activate script:
Wed Nov  1 17:20:13 2017 - [info]   /etc/masterha/master_ip_failover.pl --command=start --ssh_user=root --orig_master_host=db01 --orig_master_ip=72.127.2.50 --orig_master_port=3306 --new_master_host=db03 --new_master_ip=72.127.2.52 --new_master_port=3306 --new_master_user='huha' --new_master_password='123456'  
Unknown option: new_master_user
Unknown option: new_master_password


IN SCRIPT TEST====/sbin/ip addr del 72.127.2.119/24 dev eth0==/sbin/ip addr add 72.127.2.119/24 dev eth0===

Enabling the VIP - 72.127.2.119/24 on the new master - db03 
Wed Nov  1 17:20:14 2017 - [info]  OK.
Wed Nov  1 17:20:14 2017 - [info] ** Finished master recovery successfully.
Wed Nov  1 17:20:14 2017 - [info] * Phase 3: Master Recovery Phase completed.
Wed Nov  1 17:20:14 2017 - [info] 
Wed Nov  1 17:20:14 2017 - [info] * Phase 4: Slaves Recovery Phase..
Wed Nov  1 17:20:14 2017 - [info] 
Wed Nov  1 17:20:14 2017 - [info] 
Wed Nov  1 17:20:14 2017 - [info] * Phase 4.1: Starting Slaves in parallel..
Wed Nov  1 17:20:14 2017 - [info] 
Wed Nov  1 17:20:14 2017 - [info] -- Slave recovery on host db02(72.127.2.51:3306) started, pid: 4504. Check tmp log /var/log/masterha/app1/db02_3306_20171101172009.log if it takes time..
Wed Nov  1 17:21:10 2017 - [info] 
Wed Nov  1 17:21:10 2017 - [info] Log messages from db02 ...
Wed Nov  1 17:21:11 2017 - [info] 
Wed Nov  1 17:20:14 2017 - [info]  Resetting slave db02(72.127.2.51:3306) and starting replication from the new master db03(72.127.2.52:3306)..
Wed Nov  1 17:20:14 2017 - [debug]  Stopping slave IO/SQL thread on db02(72.127.2.51:3306)..
Wed Nov  1 17:20:14 2017 - [debug]   done.
Wed Nov  1 17:20:14 2017 - [info]  Executed CHANGE MASTER.
Wed Nov  1 17:20:14 2017 - [debug]  Starting slave IO/SQL thread on db02(72.127.2.51:3306)..
Wed Nov  1 17:20:15 2017 - [debug]   done.
Wed Nov  1 17:20:15 2017 - [info]  Slave started.
Wed Nov  1 17:21:10 2017 - [info]  gtid_wait(24ce300b-98ed-11e7-8156-000c29809308:1-12155) completed on db02(72.127.2.51:3306). Executed 10854 events.
Wed Nov  1 17:21:11 2017 - [info] End of log messages from db02.
Wed Nov  1 17:21:11 2017 - [info] -- Slave on host db02(72.127.2.51:3306) started.
Wed Nov  1 17:21:11 2017 - [info] All new slave servers recovered successfully.
Wed Nov  1 17:21:11 2017 - [info] 
Wed Nov  1 17:21:11 2017 - [info] * Phase 5: New master cleanup phase..
Wed Nov  1 17:21:11 2017 - [info] 
Wed Nov  1 17:21:11 2017 - [info] Resetting slave info on the new master..
Wed Nov  1 17:21:11 2017 - [debug]  Clearing slave info..
Wed Nov  1 17:21:11 2017 - [debug]  Stopping slave IO/SQL thread on db03(72.127.2.52:3306)..
Wed Nov  1 17:21:11 2017 - [debug]   done.
Wed Nov  1 17:21:12 2017 - [debug]  SHOW SLAVE STATUS shows new master does not replicate from anywhere. OK.
Wed Nov  1 17:21:12 2017 - [info]  db03: Resetting slave info succeeded.
Wed Nov  1 17:21:12 2017 - [info] Master failover to db03(72.127.2.52:3306) completed successfully.
Wed Nov  1 17:21:12 2017 - [debug]  Disconnected from db02(72.127.2.51:3306)
Wed Nov  1 17:21:12 2017 - [debug]  Disconnected from db03(72.127.2.52:3306)
Wed Nov  1 17:21:12 2017 - [info] 

----- Failover Report -----

app1: MySQL Master failover db01(72.127.2.50:3306) to db03(72.127.2.52:3306) succeeded

Master db01(72.127.2.50:3306) is down!

Check MHA Manager logs at db03:/var/log/masterha/app1/app1.log for details.

Started automated(non-interactive) failover.
Invalidated master IP address on db01(72.127.2.50:3306)
Selected db03(72.127.2.52:3306) as a new master.
db03(72.127.2.52:3306): OK: Applying all logs succeeded.
db03(72.127.2.52:3306): OK: Activated master IP address.
db02(72.127.2.51:3306): OK: Slave started, replicating from db03(72.127.2.52:3306)
db03(72.127.2.52:3306): Resetting slave info succeeded.
Master failover to db03(72.127.2.52:3306) completed successfully.
```
#####  从上面的输出可以看出整个MHA的切换过程，共包括以下的步骤：

    1.配置文件检查阶段，这个阶段会检查整个集群配置文件配置
    
    2.宕机的master处理，这个阶段包括虚拟ip摘除操作）
    
    3.复制dead maste和最新slave相差的relay log，并保存到MHA Manger具体的目录下
    
    4.识别含有最新更新的slave
    
    5.应用从master保存的二进制日志事件（binlog events）
    
    6.提升一个slave为新的master进行复制
    
    7.使其他的slave连接新的master进行复制  
#### 在线切换(master_ip_online_change)
##### 首先，停掉MHA监控
==注意：--new_master_host=db02  必须和配置文件保持一致，写ip的话会不识别==
##### 手动在线切换
```
[root@db03 masterha]#  masterha_master_switch --conf=/etc/masterha/app1.conf --master_state=alive --new_master_host=db02 --orig_master_is_new_slave --running_updates_limit=10000 --interactive=0
Thu Nov  2 10:14:51 2017 - [info] MHA::MasterRotate version 0.56.
Thu Nov  2 10:14:51 2017 - [info] Starting online master switch..
Thu Nov  2 10:14:51 2017 - [info] 
Thu Nov  2 10:14:51 2017 - [info] * Phase 1: Configuration Check Phase..
Thu Nov  2 10:14:51 2017 - [info] 
Thu Nov  2 10:14:51 2017 - [warning] Global configuration file /etc/masterha_default.cnf not found. Skipping.
Thu Nov  2 10:14:51 2017 - [info] Reading application default configuration from /etc/masterha/app1.conf..
Thu Nov  2 10:14:51 2017 - [info] Reading server configuration from /etc/masterha/app1.conf..
Thu Nov  2 10:14:51 2017 - [debug] Connecting to servers..
Thu Nov  2 10:14:51 2017 - [debug]  Connected to: db01(72.127.2.50:3306), user=huha
Thu Nov  2 10:14:51 2017 - [debug]  Number of slave worker threads on host db01(72.127.2.50:3306): 0
Thu Nov  2 10:14:51 2017 - [debug]  Connected to: db02(72.127.2.51:3306), user=huha
Thu Nov  2 10:14:51 2017 - [debug]  Number of slave worker threads on host db02(72.127.2.51:3306): 0
Thu Nov  2 10:14:51 2017 - [debug]  Connected to: db03(72.127.2.52:3306), user=huha
Thu Nov  2 10:14:51 2017 - [debug]  Number of slave worker threads on host db03(72.127.2.52:3306): 0
Thu Nov  2 10:14:51 2017 - [debug]  Comparing MySQL versions..
Thu Nov  2 10:14:51 2017 - [debug]   Comparing MySQL versions done.
Thu Nov  2 10:14:51 2017 - [debug] Connecting to servers done.
Thu Nov  2 10:14:51 2017 - [info] GTID failover mode = 1
Thu Nov  2 10:14:51 2017 - [info] Current Alive Master: db01(72.127.2.50:3306)
Thu Nov  2 10:14:51 2017 - [info] Alive Slaves:
Thu Nov  2 10:14:51 2017 - [info]   db02(72.127.2.51:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Thu Nov  2 10:14:51 2017 - [info]     GTID ON
Thu Nov  2 10:14:51 2017 - [debug]    Relay log info repository: FILE
Thu Nov  2 10:14:51 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Thu Nov  2 10:14:51 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Thu Nov  2 10:14:51 2017 - [info]   db03(72.127.2.52:3306)  Version=5.7.19-log (oldest major version between slaves) log-bin:enabled
Thu Nov  2 10:14:51 2017 - [info]     GTID ON
Thu Nov  2 10:14:51 2017 - [debug]    Relay log info repository: FILE
Thu Nov  2 10:14:51 2017 - [info]     Replicating from 72.127.2.50(72.127.2.50:3306)
Thu Nov  2 10:14:51 2017 - [info]     Primary candidate for the new Master (candidate_master is set)
Thu Nov  2 10:14:51 2017 - [info] Executing FLUSH NO_WRITE_TO_BINLOG TABLES. This may take long time..
Thu Nov  2 10:14:51 2017 - [info]  ok.
Thu Nov  2 10:14:51 2017 - [info] Checking MHA is not monitoring or doing failover..
Thu Nov  2 10:14:51 2017 - [info] Checking replication health on db02..
Thu Nov  2 10:14:51 2017 - [info]  ok.
Thu Nov  2 10:14:51 2017 - [info] Checking replication health on db03..
Thu Nov  2 10:14:51 2017 - [info]  ok.
Thu Nov  2 10:14:51 2017 - [info] db02 can be new master.
Thu Nov  2 10:14:51 2017 - [info] 
From:
db01(72.127.2.50:3306) (current master)
 +--db02(72.127.2.51:3306)
 +--db03(72.127.2.52:3306)

To:
db02(72.127.2.51:3306) (new master)
 +--db03(72.127.2.52:3306)
 +--db01(72.127.2.50:3306)
Thu Nov  2 10:14:51 2017 - [info] Checking whether db02(72.127.2.51:3306) is ok for the new master..
Thu Nov  2 10:14:51 2017 - [info]  ok.
Thu Nov  2 10:14:51 2017 - [info] db01(72.127.2.50:3306): SHOW SLAVE STATUS returned empty result. To check replication filtering rules, temporarily executing CHANGE MASTER to a dummy host.
Thu Nov  2 10:14:51 2017 - [info] db01(72.127.2.50:3306): Resetting slave pointing to the dummy host.
Thu Nov  2 10:14:51 2017 - [info] ** Phase 1: Configuration Check Phase completed.
Thu Nov  2 10:14:51 2017 - [info] 
Thu Nov  2 10:14:51 2017 - [debug]  Disconnected from db01(72.127.2.50:3306)
Thu Nov  2 10:14:51 2017 - [info] * Phase 2: Rejecting updates Phase..
Thu Nov  2 10:14:51 2017 - [info] 
Thu Nov  2 10:14:51 2017 - [info] Executing master ip online change script to disable write on the current master:
Thu Nov  2 10:14:51 2017 - [info]   /etc/masterha/master_ip_online_change --command=stop --orig_master_host=db01 --orig_master_ip=72.127.2.50 --orig_master_port=3306 --orig_master_user='huha' --orig_master_password='123456' --new_master_host=db02 --new_master_ip=72.127.2.51 --new_master_port=3306 --new_master_user='huha' --new_master_password='123456' --orig_master_ssh_user=root --new_master_ssh_user=root   --orig_master_is_new_slave
Unknown option: orig_master_password
Unknown option: new_master_password
Unknown option: orig_master_ssh_user
Unknown option: new_master_ssh_user
Unknown option: orig_master_is_new_slave
Thu Nov  2 10:14:51 2017 264706 Set read_only on the new master.. ok.
Thu Nov  2 10:14:51 2017 268418 Waiting all running 2 threads are disconnected.. (max 1500 milliseconds)
{'Time' => '3839','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '6','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db03:25479'}
{'Time' => '3767','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '7','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db02:36900'}
Thu Nov  2 10:14:51 2017 778610 Waiting all running 2 threads are disconnected.. (max 1000 milliseconds)
{'Time' => '3840','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '6','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db03:25479'}
{'Time' => '3768','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '7','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db02:36900'}
Thu Nov  2 10:14:52 2017 286080 Waiting all running 2 threads are disconnected.. (max 500 milliseconds)
{'Time' => '3840','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '6','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db03:25479'}
{'Time' => '3768','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '7','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db02:36900'}
Thu Nov  2 10:14:52 2017 794432 Set read_only=1 on the orig master.. ok.
Thu Nov  2 10:14:52 2017 797219 Waiting all running 2 queries are disconnected.. (max 500 milliseconds)
{'Time' => '3841','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '6','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db03:25479'}
{'Time' => '3769','Command' => 'Binlog Dump GTID','db' => undef,'Id' => '7','Info' => undef,'User' => 'repl','State' => 'Master has sent all binlog to slave; waiting for more updates','Host' => 'db02:36900'}
Disabling the VIP on old master: db01 
Thu Nov  2 10:14:53 2017 596027 Killing all application threads..
Thu Nov  2 10:14:53 2017 607901 done.
Thu Nov  2 10:14:53 2017 - [info]  ok.
Thu Nov  2 10:14:53 2017 - [info] Locking all tables on the orig master to reject updates from everybody (including root):
Thu Nov  2 10:14:53 2017 - [info] Executing FLUSH TABLES WITH READ LOCK..
Thu Nov  2 10:14:53 2017 - [info]  ok.
Thu Nov  2 10:14:53 2017 - [info] Orig master binlog:pos is mysql-bin.000003:616.
Thu Nov  2 10:14:53 2017 - [debug] Fetching current slave status..
Thu Nov  2 10:14:53 2017 - [debug]  Fetching current slave status done.
Thu Nov  2 10:14:53 2017 - [info]  Waiting to execute all relay logs on db02(72.127.2.51:3306)..
Thu Nov  2 10:14:53 2017 - [info]  master_pos_wait(mysql-bin.000003:616) completed on db02(72.127.2.51:3306). Executed 0 events.
Thu Nov  2 10:14:53 2017 - [info]   done.
Thu Nov  2 10:14:53 2017 - [debug]  Stopping SQL thread on db02(72.127.2.51:3306)..
Thu Nov  2 10:14:53 2017 - [debug]   done.
Thu Nov  2 10:14:53 2017 - [info] Getting new master's binlog name and position..
Thu Nov  2 10:14:53 2017 - [info]  mysql-bin.000003:690
Thu Nov  2 10:14:53 2017 - [info]  All other slaves should start replication from here. Statement should be: CHANGE MASTER TO MASTER_HOST='db02 or 72.127.2.51', MASTER_PORT=3306, MASTER_AUTO_POSITION=1, MASTER_USER='repl', MASTER_PASSWORD='xxx';
Thu Nov  2 10:14:53 2017 - [info] Executing master ip online change script to allow write on the new master:
Thu Nov  2 10:14:53 2017 - [info]   /etc/masterha/master_ip_online_change --command=start --orig_master_host=db01 --orig_master_ip=72.127.2.50 --orig_master_port=3306 --orig_master_user='huha' --orig_master_password='123456' --new_master_host=db02 --new_master_ip=72.127.2.51 --new_master_port=3306 --new_master_user='huha' --new_master_password='123456' --orig_master_ssh_user=root --new_master_ssh_user=root   --orig_master_is_new_slave
Unknown option: orig_master_password
Unknown option: new_master_password
Unknown option: orig_master_ssh_user
Unknown option: new_master_ssh_user
Unknown option: orig_master_is_new_slave
Thu Nov  2 10:14:53 2017 726975 Set read_only=0 on the new master.
Enabling the VIP - 72.127.2.119/24 on the new master - db02 
Thu Nov  2 10:14:54 2017 - [info]  ok.
Thu Nov  2 10:14:54 2017 - [info] 
Thu Nov  2 10:14:54 2017 - [info] * Switching slaves in parallel..
Thu Nov  2 10:14:54 2017 - [info] 
Thu Nov  2 10:14:54 2017 - [info] -- Slave switch on host db03(72.127.2.52:3306) started, pid: 1584
Thu Nov  2 10:14:54 2017 - [info] 
Thu Nov  2 10:14:55 2017 - [info] Log messages from db03 ...
Thu Nov  2 10:14:55 2017 - [info] 
Thu Nov  2 10:14:54 2017 - [info]  Waiting to execute all relay logs on db03(72.127.2.52:3306)..
Thu Nov  2 10:14:54 2017 - [info]  master_pos_wait(mysql-bin.000003:616) completed on db03(72.127.2.52:3306). Executed 0 events.
Thu Nov  2 10:14:54 2017 - [info]   done.
Thu Nov  2 10:14:54 2017 - [debug]  Stopping SQL thread on db03(72.127.2.52:3306)..
Thu Nov  2 10:14:54 2017 - [debug]   done.
Thu Nov  2 10:14:54 2017 - [info]  Resetting slave db03(72.127.2.52:3306) and starting replication from the new master db02(72.127.2.51:3306)..
Thu Nov  2 10:14:54 2017 - [debug]  Stopping slave IO/SQL thread on db03(72.127.2.52:3306)..
Thu Nov  2 10:14:54 2017 - [debug]   done.
Thu Nov  2 10:14:54 2017 - [info]  Executed CHANGE MASTER.
Thu Nov  2 10:14:54 2017 - [debug]  Starting slave IO/SQL thread on db03(72.127.2.52:3306)..
Thu Nov  2 10:14:55 2017 - [debug]   done.
Thu Nov  2 10:14:55 2017 - [info]  Slave started.
Thu Nov  2 10:14:55 2017 - [info] End of log messages from db03 ...
Thu Nov  2 10:14:55 2017 - [info] 
Thu Nov  2 10:14:55 2017 - [info] -- Slave switch on host db03(72.127.2.52:3306) succeeded.
Thu Nov  2 10:14:55 2017 - [info] Unlocking all tables on the orig master:
Thu Nov  2 10:14:55 2017 - [info] Executing UNLOCK TABLES..
Thu Nov  2 10:14:55 2017 - [info]  ok.
Thu Nov  2 10:14:55 2017 - [info] Starting orig master as a new slave..
Thu Nov  2 10:14:55 2017 - [info]  Resetting slave db01(72.127.2.50:3306) and starting replication from the new master db02(72.127.2.51:3306)..
Thu Nov  2 10:14:55 2017 - [info]  Executed CHANGE MASTER.
Thu Nov  2 10:14:55 2017 - [debug]  Starting slave IO/SQL thread on db01(72.127.2.50:3306)..
Thu Nov  2 10:14:56 2017 - [error][/usr/share/perl5/vendor_perl/MHA/Server.pm, ln770] SQL Thread could not be started on db01(72.127.2.50:3306)! Check slave status.
Thu Nov  2 10:14:56 2017 - [error][/usr/share/perl5/vendor_perl/MHA/Server.pm, ln774]  Last Error= 1007, Last Error=Error 'Can't create database 'test_01'; database exists' on query. Default database: 'test_01'. Query: 'create database test_01'
Thu Nov  2 10:14:56 2017 - [error][/usr/share/perl5/vendor_perl/MHA/Server.pm, ln862] Starting slave IO/SQL thread on db01(72.127.2.50:3306) failed!
Thu Nov  2 10:14:56 2017 - [error][/usr/share/perl5/vendor_perl/MHA/MasterRotate.pm, ln573]  Failed!
Thu Nov  2 10:14:56 2017 - [error][/usr/share/perl5/vendor_perl/MHA/MasterRotate.pm, ln602] Switching master to db02(72.127.2.51:3306) done, but switching slaves partially failed.
Thu Nov  2 10:14:56 2017 - [debug]  Disconnected from db01(72.127.2.50:3306)
Thu Nov  2 10:14:56 2017 - [debug]  Disconnected from db02(72.127.2.51:3306)
Thu Nov  2 10:14:56 2017 - [debug]  Disconnected from db03(72.127.2.52:3306)
```
##### 在线切换原理步骤
    MHA在线切换的大概过程：
    1.检测复制设置和确定当前主服务器
    2.确定新的主服务器
    3.阻塞写入到当前主服务器
    4.等待所有从服务器赶上复制
    5.授予写入到新的主服务器
    6.重新设置从服务器 
    
    注意，在线切换的时候应用架构需要考虑以下两个问题：
    
    1.自动识别master和slave的问题（master的机器可能会切换），如果采用了vip的方式，基本可以解决这个问题。
    
    2.负载均衡的问题（可以定义大概的读写比例，每台机器可承担的负载比例，当有机器离开集群时，需要考虑这个问题）
    
    为了保证数据完全一致性，在最快的时间内完成切换，MHA的在线切换必须满足以下条件才会切换成功，否则会切换失败。
    
    1.所有slave的IO线程都在运行
    
    2.所有slave的SQL线程都在运行
    
    3.所有的show slave status的输出中Seconds_Behind_Master参数小于或者等于running_updates_limit秒，如果在切换过程中不指定running_updates_limit,那么默认情况下running_updates_limit为1秒。
    
    4.在master端，通过show processlist输出，没有一个更新花费的时间大于running_updates_limit秒。
    
### 参考：
    http://www.cnblogs.com/gomysql/p/3675429.html