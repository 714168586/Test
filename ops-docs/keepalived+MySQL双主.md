## 基于  MySQL 5.7  keepalived  的双主搭建
   
### 环境：


hostname | ip
---|---
 db01 | 72.127.2.50	
 db02 |  72.127.2.51
 vip  | 72.127.2.199

    双主搭建省略....

### 安装Keepalived：
    
    rpm -ivh http://mirrors.ustc.edu.cn/fedora/epel/6/x86_64/epel-release-6-8.noarch.rpm
    yum install keepalived
    #yum install MySQL-python


### 配置keepalived.conf
    vi /etc/keepalived/keepalived.conf
    
    global_defs {    
         notification_email {    
             sushengbin@51tuodao.com  
         }    
         notification_email_from sushengbin@51tuodao.com    
         smtp_server 127.0.0.1    
         smtp_connect_timeout 30    
         router_id MySQL-ha    
    }    
       
    vrrp_instance VI_1 {    
         state BACKUP   #两台配置此处均是BACKUP    
         interface eth0    
         virtual_router_id 51   #分组，主备相同  
         priority 100   #优先级，另一台改为90    
         advert_int 1    
         nopreempt  #不抢占，只在优先级高的机器上设置即可，优先级低的机器不设置    
         authentication {    
             auth_type PASS    
             auth_pass 1111    
         }    
         virtual_ipaddress {    
            72.127.2.119 
         }    
    }    
       
    virtual_server 72.127.2.119 3306 {    
         delay_loop 2   #每个2秒检查一次real_server状态    
         lb_algo wrr   #LVS算法    
         lb_kind DR    #LVS模式    
         persistence_timeout 60   #会话保持时间    
         protocol TCP    
         real_server 72.127.2.50 3306 {    
             weight 3    
             notify_down /etc/keepalived/mysql.sh #检测到服务down后执行的脚本    
             TCP_CHECK {    
                 connect_timeout 10    #连接超时时间    
                 nb_get_retry 3       #重连次数    
                 delay_before_retry 3   #重连间隔时间    
                 connect_port 3306   #健康检查端口  
             }  
         }    
    }


db02服务器配置keepalived.conf跟master一样，只需要把Realserver IP修改成real_server 72.127.2.51 ；优先级从100改成90即可。

### 两台服务器都配置检测脚本：
    cat  /etc/keepalived/mysql.sh
    #!/bin/sh    
    /etc/init.d/keepalived  stop

    然后分别重启两台数据库上keepalived服务即可。最后测试停止master Mysql服务，是否会自动切换到Backup上。



## keepalived的脑裂问题
### 解决思路如下：
    每个keepalived的节点都执行一个定时任务的脚本，定时去ping网关，累计失败次数超过阀值次数，则关闭自身的keepalived服务。这样就不会出现脑裂的情况。
    脚本如下：
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    import os
    import sys
    
    ip = sys.argv[1]
    c=0
    for i in range(1,4,1):
        return1=os.popen('ping %s -w 1' %ip).read()
        if  '100% packet loss' in return1  :
            c += 1
    if c>2:
        os.popen('service keepalived stop')
    
    
    
    定时任务如下：
    Shell>crontab –e
    * * * * * /root/ping.py 72.127.2.1
