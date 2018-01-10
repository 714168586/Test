ActiveMQ安装配置

由于activemq是依赖于java环境的，所以在安装之前，需要先安装jdk，建议安装jdk1.7版本，jdk的具体安装和环境变量配置过程省略

1、下载activemq，下载地址：http://archive.apache.org/dist/activemq，安装版本为apache-activemq-5.15.0-bin.tar.gz 

2、在/ursr/local/目录下新建activemq文件夹，并进入该文件夹，执行如下命令解压文件
cd /ursr/local
mkdir activemq
tar xzvf apache-activemq-5.15.0-bin.tar.gz

3、启动ActiveMQ
cd /ursr/local/activemq/apache-activemq-5.15.0/bin
./activemq start

4 测试是否成功安装

activeMQ默认配置下启动会启动8161和61616两个端口，其中8161是mq自带的管理后台的端口，61616是mq服务默认端口

通过http://ip地址:8161/admin/ 打开MQ自带的web控制台（可以在控制台测试消息的创建和消费）默认用户名密码为admin、admin


RabbitMQ安装配置

安装依赖文件：
yum install gcc glibc-devel make ncurses-devel openssl-devel xmlto

1.Erlang安装配置
下载安装包，地址http://www.erlang.org/downloads，这里选择的是otp_src_18.3.tar.gz
解压文件：tar xzvf otp_src_18.3.tar.gz
cd otp_src_18.3
配置安装路径编译代码： ./configure --prefix=/opt/erlang
编译： make && make install
安装完成后进入/opt/erlang查看执行结果
cd /opt/erlang/
erl
当出现以下信息时表示安装完成。然后输入’halt().’退出即可
Erlang/OTP 18 [erts-7.3] [source] [64-bit] [smp:8:8] [async-threads:10] [hipe] [kernel-poll:false]

Eshell V7.3  (abort with ^G)
1>

配置Erlang环境变量,vim /etc/profile文件，增加下面的环境变量:
export PATH=$PATH:/opt/erlang/bin
source  /etc/profile  使配置生效

2.下载安装RabbitMq
wget http://www.rabbitmq.com/releases/rabbitmq-server/v3.6.1/rabbitmq-server-generic-unix-3.6.1.tar.xz

解压文件
xz -d rabbitmq-server-generic-unix-3.6.1.tar.xz
tar xvf rabbitmq-server-generic-unix-3.6.1.tar　　-C /opt
解压后进入文件夹/opt发现多了个文件夹rabbitmq-server-generic-unix-3.6.1 ，重命名为rabbitmq以便记忆

然后在配置rabbitmq环境变量,vim /etc/profile文件，增加下面的环境变量:
export PATH=$PATH:/opt/rabbitmq/sbin

source  /etc/profile 使配置生效

3.RabbitMQ服务启动关闭
cd sbin/
./rabbitmq-server -detached     （detached参数表示后台启动服务）

查看服务状态：
 ./rabbitmqctl status
 
4. 配置网页插件

首先创建目录，否则可能报错：

mkdir /etc/rabbitmq


然后启用插件：

./rabbitmq-plugins enable rabbitmq_management

配置linux 端口 15672 网页管理  5672 AMQP端口
然后访问http://localhost:15672即可 

默认用户guest 密码guest

5. 远程访问配置

默认网页是不允许访问的，需要增加一个用户修改一下权限，代码如下：

添加用户:rabbitmqctl add_user admin admin

添加权限:rabbitmqctl set_permissions -p "/" admin ".*" ".*" ".*"

修改用户角色rabbitmqctl set_user_tags admin administrator

然后就可以远程访问了，然后可直接配置用户权限等信息。

6.自定义rabbitmq端口
主要参考官方文档：http://www.rabbitmq.com/configure.html

一般情况下，RabbitMQ的默认配置就足够了。如果希望特殊设置的话，有两个途径：
一个是环境变量的配置文件 rabbitmq-env.conf ；
一个是配置信息的配置文件 rabbitmq.config；
注意，这两个文件默认是没有的，如果需要必须自己创建

rabbitmq-env.conf
这个文件的位置是确定和不能改变的，位于：/etc/rabbitmq目录下（这个目录需要自己创建）。
文件的内容包括了RabbitMQ的一些环境变量，常用的有：
#RABBITMQ_NODE_PORT=    //端口号
#HOSTNAME=
RABBITMQ_NODENAME=mq
RABBITMQ_CONFIG_FILE=        //配置文件的路径
RABBITMQ_MNESIA_BASE=/rabbitmq/data        //需要使用的MNESIA数据库的路径
RABBITMQ_LOG_BASE=/rabbitmq/log        //log的路径
RABBITMQ_PLUGINS_DIR=/rabbitmq/plugins    //插件的路径

具体的列表见：http://www.rabbitmq.com/configure.html#define-environment-variables


rabbitmq.config
这是一个标准的erlang配置文件。它必须符合erlang配置文件的标准。
它既有默认的目录，也可以在rabbitmq-env.conf文件中配置。

文件的内容详见：http://www.rabbitmq.com/configure.html#config-items

参考链接：http://www.linuxidc.com/Linux/2016-03/129557.htm
          http://blog.csdn.net/historyasamirror/article/details/6827870




