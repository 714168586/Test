[TOC]

## Mysql5.7 的安装

二进制：方便提bug
源码不推荐：
学习环境推荐源码，
生产不推荐源码，是后期数据库升级，失败后，需要回滚新版本，再安装老版本。

小版本升级，可以去link，unlink目录，例如：



### 1.1 软件解压和安装

root执行
```
解压到/opt/mysql/mysql-5.7.16-xxx
ln -s /opt/mysql/mysql-5.7.16-linux-glibc2.5-x86_64 /usr/local/mysql
使用软链是为了以后的升级方便
```

### 1.2 新建用户、目录
```
groupadd mysql
useradd  -g mysql -d /user/local/mysql -s /sbin/nologin -M -n mysql

-s 是禁用shell

mkdir /data/mysql/项目名-端口号
mkdir -p /data/mysql/mysql3306/{data,logs,tmp}
chown -R mysql:mysql /data/mysql/mysql3306/
chown -R mysql:mysql /usr/local/mysql/

错误： chown -R mysql:mysql /
修复方法：从其他机器的权限列表拷贝过来，然后应用到本机
getfacl -r 

注意：权限乱掉后 不能重启主机
```

### 1.3 安装

5.7 以上使用下面的方式初始化：
```
配置文件使用my.cnf.9

bin/mysqld --defaults-file=配置文件路径  --initialize 
-- 这里的bin目录是mysql tar包的解压目录。
-- 初始化日志：/data/mysql/mysql3306/data/error.log

如何不想要初始化密码：
/mysql/bin/mysqld --initiaize-insecure

grep password /data/mysql/mysql3306/data/error.log
2016-12-25T14:17:13.126583Z 1 [Note] A temporary password is generated for root@localhost: HKGAptLDc8&3
```
5.6初始化方式：
```
/usr/local/mysql/scripts/mysql_install_db 
5.7以下初始化不会带默认密码
```


### 1.4 启动登录

**标准方式**
```
service mysqld start
/etc/init.d/mysqld start
mysqld来自：
cp /usr/local/mysql/support-files/mysql.server /etc/init.d/mysqld

```
**启动多实例的方式**
```
/usr/local/mysql/bin/mysqld_safe --defaults-file=
/usr/local/mysql/bin/mysqld --defaults-file=
/usr/local/mysql/bin/mysqld_multi start 3307

```
```
echo "export PATH=$PATH:/usr/local/mysql/bin">>/etc/profile
cp support-files/mysql.server /etc/init.d/mysql
/etc/init.d/mysql start


--登录
mysql -S /tmp/mysql3306.sock -uroot -pHKGAptLDc8&3
修改默认root密码：
alter user user() identified by '123456';
user() 表示该会话的连接用户
current_user() 当前操作用户

select host,user,authentication_string from mysql.user;
+-----------+-----------+-------------------------------------------+
| host      | user      | authentication_string                    |
+-----------+-----------+-------------------------------------------+
| localhost | root      | *6BB4837EB74329105EE4568DDA7DC67ED2CA2AD9 |
| localhost | mysql.sys | *THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE |
+-----------+-----------+-------------------------------------------+

支持远程登录的账号

create user 'test'@'%' identified by 'test';
grant all privileges on *.* to  'test'@'%' ;

```


### 1.5 启动mysql
```
mysql 开机自启动
cp support-files/mysql.server /etc/init.d/mysql
chkconfig --add mysql

/usr/local/mysql/bin/mysqld_safe --defaults-file=/etc/my.cnf &
```

### 1.6 多实例启动
```
mkdir -p /data/mysql/mysql3307/{data,logs,tmp}

cp /etc/my.cnf /data/mysql/mysql3307/my3307.cnf
cp /data/mysql/mysql3306/data/ib_* /data/mysql/mysql3307/data --如果不拷贝这个文件，可以使用重新初始化3307
chown -R mysql:mysql /data/mysql/mysql3307/
sed -i 's/3306/3307/g' /data/mysql/mysql3307/my3307.cnf

重新初始化：
mysqld  --defaults-file=/data/mysql/mysql3307/my3307.cnf --initialize
-- defaults-file和 initlize的顺序不能错。否则初始化会卡住不动。



-- 启动多实例
/usr/local/mysql/bin/mysqld --defaults-file=/data/mysql/mysql3307/my3307.cnf &

-- 登录多实例
mysql -S /tmp/mysql3307.sock -uroot -p123456

-- 关闭多实例
mysqladmin -S /tmp/mysql3307.sock shutdown -p

-- 冷备份
cp -rf  /data/mysql/mysql3307 /data/mysql/mysql3307_bak
```
备注：
```
Mysql 5.6 以前(包括5.6)需要账号的安全加固
delete from mysql.user where user != 'root' or host != 'localhost';
flush privileges;
alter user user() identified by '密码';
drop database test;
truncate mysql.db;
flush privileges;
```
### 1.7 多实例关闭

```
/opt/mysql/mysql-5.7.16-linux-glibc2.5-x86_64/bin/mysqladmin -uroot -p123456 -P 3307 -S /tmp/mysql3307.sock shutdown
```
