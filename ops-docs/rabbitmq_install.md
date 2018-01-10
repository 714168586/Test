### 持久化
RabbitMQ支持消息的持久化，也就是数据写在磁盘上，为了数据安全考虑，我个人觉得大多数开发人员都会选择持久化。

消息队列持久化包括3个部分：

1、exchange持久化，在声明时指定durable => true

2、queue持久化，在声明时指定durable => true

3、消息持久化，在投递时指定delivery_mode=> 2（1是非持久化）

如果exchange和queue都是持久化的，那么它们之间的binding也是持久化的。如果exchange和queue两者之间有一个持久化，一个非持久化，就不允许建立绑定。

注意：一旦创建了队列和交换机，就不能修改其标志了。例如，如果创建了一个non-durable的队列，然后想把它改变成durable的，唯一的办法就是删除这个队列然后重现创建。

集群
rabbitMQ可以通过三种方法来部署分布式集群系统，分别是：cluster,federation,shovel

一般用cluster

节点类型

持久化:

  1.写入磁盘
 
  2.写入内存


### 安装(基于centos7.2)
rpm -Uvh https://mirrors.tuna.tsinghua.edu.cn/epel/7/x86_64/e/epel-release-7-10.noarch.rpm

yum install erlang

安装过程中会有提示，一路输入“y”即可。
完成后安装RabbitMQ：
先下载rpm：

wget http://www.rabbitmq.com/releases/rabbitmq-server/v3.6.6/rabbitmq-server-3.6.6-1.el7.noarch.rpm

下载完成后安装：

yum install rabbitmq-server-3.6.6-1.el7.noarch.rpm 

完成后启动服务：

service rabbitmq-server start

可以查看服务状态：

service rabbitmq-server status


### 开启管理UI：

rabbitmq-plugins enable rabbitmq_management

rabbitmq默认配置文件：

 /usr/lib/rabbitmq/lib/rabbitmq_server-3.6.1/sbin/rabbitmq-defaults

http://72.127.2.22:15672/


集群：

http://72.127.2.21:15672/#/acticemq  
http://72.127.2.22:8161/admin/


报错：

节点名字和实际名字不一样 
 vi /etc/rabbitmq/rabbitmq-env.conf 
NODENAME=rabbit@localhost


集群：

rabbitmqctl stop_app
 rabbitmqctl join_cluster rabbit@rabbit1  
 rabbitmqctl start_app
 rabbitmqctl cluster_status

join_cluster --ram  内存形式   默认是disk形式

拆分集群：

在要剔除的节点上执行

rabbitmqctl stop_app

rabbitmqctl reset

rabbitmqctl start_app


### 常用命令：
```

查看所有队列信息

# rabbitmqctl list_queues

关闭应用

# rabbitmqctl stop_app

启动应用，和上述关闭命令配合使用，达到清空队列的目的

# rabbitmqctl start_app

清除所有队列

# rabbitmqctl reset

更多用法及参数，可以执行如下命令查看

# rabbitmqctl

（1）首先关闭rabbitmq: rabbitmqctl stop_app

（2）还原： rabbitmqctl reset

（3）启动： rabbitmqctl start_app

（4）添加用户： rabbitmqctl add_user root root

（5）设置权限：rabbitmqctl set_permissions -p / root ".*" ".*" ".*"

（6）查看用户： rabbitmqctl list_users


RabbitMQ用户管理

添加用户（用户名root，密码admin）

[root@node139 ~]# rabbitmqctl add_user admin admin

设置用户角色（设置admin用户为管理员角色）

[root@node139 ~]# rabbitmqctl set_user_tags admin administrator

Setting tags for user "admin" to [administrator] ...

设置用户权限（设置admin用户配置、写、读的权限）

[root@node139 ~]# rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"

Setting permissions for user "admin" in vhost "/" ...

删除用户（删除guest用户）

[root@node139 ~]# rabbitmqctl delete_user gues