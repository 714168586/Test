### 这里搭建的是avtivemq  高可用+负载均衡   
### 需要用到两个集群  
#### 环境准备：
    72.127.2.140    cluster01   高可用   activemq-01 activemq-02 activemq-03    zookeeper
    72.127.2.158    cluster02   高可用   activemq-04 activemq-05 activemq-06    zookeeper
      
    140 /etc/hosts
    72.127.2.140 zk01 zk02 zk03


### zookeeper集群：
    zookeeper-01  zookeeper-02  zookeeper-03

### 配置文件都如下 （如果是同一台机器  端口号需要修改）这里是演示一台
    [root@zk01 conf]# vim zoo.cfg 
    # The number of milliseconds of each tick
    tickTime=2000
    # The number of ticks that the initial 
    # synchronization phase can take
    initLimit=10
    # The number of ticks that can pass between 
    # sending a request and getting an acknowledgement
    syncLimit=5
    # the directory where the snapshot is stored.
    # do not use /tmp for storage, /tmp here is just 
    # example sakes.
    dataDir=/data/zookeeper/master/zookeeper/data/
    dataLogDir=/data/zookeeper/master/zookeeper/logs
    # the port at which the clients will connect
    clientPort=2181
    # the maximum number of client connections.
    # increase this if you need to handle more clients
    #maxClientCnxns=60
    #
    # Be sure to read the maintenance section of the 
    # administrator guide before turning on autopurge.
    #
    # http://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_maintenance
    #
    # The number of snapshots to retain in dataDir
    #autopurge.snapRetainCount=3
    # Purge task interval in hours
    # Set to "0" to disable auto purge feature
    #autopurge.purgeInterval=1
    server.1=72.127.2.140:2888:38888
    server.2=72.127.2.140:2889:38889
    server.3=72.127.2.140:2890:38890

#### 创建目录：
    mkdir -p /data/zookeeper/master/zookeeper/data/
    cd  /data/zookeeper/master/zookeeper/data/
    echo "1" > myid（myid不能一样）
    mkdir -p dataLogDir=/data/zookeeper/master/zookeeper/logs

#### 启动：
     ./zkServer.sh start 
    
    ps -ef| grep zook   检查集群是否启动成功   没成功则看错误日志，根据日志排查问题

### activemq基于zookeeper高可用搭建：
#### 这里是其中一个集群的配置

#### 首先是修改配置文件activemq.xml 

##### activemq01   
      <networkConnectors>
        <networkConnector uri="static:(tcp://72.127.2.158:61616,tcp://72.127.2.158:61617,tcp://72.127.2.158:61618)" duplex="true"/>
        </networkConnectors>
       
        <persistenceAdapter>
         <replicatedLevelDB
              directory="${activemq.data}/leveldb"
              replicas="3"
              bind="tcp://0.0.0.0:0"
              zkAddress="zk01:2181,zk02:2182,zk03:2183"
              hostname="zk01"
              sync="local_disk"
              zkPath="/activemq/leveldb-stores"
              />
        </persistenceAdapter>
        
端口号：

        <transportConnectors>
            <!-- DOS protection, limit concurrent connections to 1000 and frame size to 100MB -->
            <transportConnector name="openwire" uri="tcp://0.0.0.0:61616?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="amqp" uri="amqp://0.0.0.0:5672?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="stomp" uri="stomp://0.0.0.0:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="mqtt" uri="mqtt://0.0.0.0:1883?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="ws" uri="ws://0.0.0.0:61614?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
        </transportConnectors>

jetty.xml

     <property name="port" value="8161"/>
   
#### activemq02 
    <networkConnectors>
        <networkConnector uri="static:(tcp://72.127.2.158:61616,tcp://72.127.2.158:61617,tcp://72.127.2.158:61618)" duplex="true"/>
        </networkConnectors>
        <persistenceAdapter>
            <replicatedLevelDB
                  directory="${activemq.data}/leveldb"
                  replicas="3"
                  bind="tcp://0.0.0.0:0"
                  zkAddress="72.127.2.140:2181,72.127.2.140:2182,72.127.2.140:2183"
                  sync="local_disk"
                  hostname="zk02"
                  zkPath="/activemq/leveldb-stores"
                  />
        </persistenceAdapter>
        
端口号：  

         <transportConnectors>
            <!-- DOS protection, limit concurrent connections to 1000 and frame size to 100MB -->
            <transportConnector name="openwire" uri="tcp://0.0.0.0:61617?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="amqp" uri="amqp://0.0.0.0:5672?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="stomp" uri="stomp://0.0.0.0:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="mqtt" uri="mqtt://0.0.0.0:1883?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="ws" uri="ws://0.0.0.0:61614?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
        </transportConnectors>
        
        
jetty.xml

     <property name="port" value="8162"/>
     
#### activemq03

     <networkConnectors>
        <networkConnector uri="static:(tcp://72.127.2.158:61616,tcp://72.127.2.158:61617,tcp://72.127.2.158:61618)" duplex="true"/>
        </networkConnectors>
      
        <persistenceAdapter>
            <replicatedLevelDB
              directory="${activemq.data}/leveldb"
              replicas="3"
              bind="tcp://0.0.0.0:0"
              zkAddress="72.127.2.140:2181,72.127.2.140:2182,72.127.2.140:2183"
              sync="local_disk"
              hostname="zk03"
              zkPath="/activemq/leveldb-stores"
              />
        </persistenceAdapter>


端口号：

     <transportConnectors>
            <!-- DOS protection, limit concurrent connections to 1000 and frame size to 100MB -->
            <transportConnector name="openwire" uri="tcp://0.0.0.0:61618?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="amqp" uri="amqp://0.0.0.0:5672?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="stomp" uri="stomp://0.0.0.0:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="mqtt" uri="mqtt://0.0.0.0:1883?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="ws" uri="ws://0.0.0.0:61614?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
        </transportConnectors>

jetty.xml：

    <property name="port" value="8163"/>



### 集群启动：
    avtivemq01:
        ./activemq start
    avtivemq02:
        ./activemq start
    avtivemq03:
        ./activemq start


同理另一个集群也是一样的方式配置启动 即可实现高可用负载均衡