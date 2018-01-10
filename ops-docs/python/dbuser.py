#!/usr/bin/env python
#coding=utf-8
import json
import yaml

from aliyunsdkcore import client
from aliyunsdkrds.request.v20140815 import CreateAccountRequest,GrantAccountPrivilegeRequest,DeleteAccountRequest,DescribeAccountsRequest

# 添加用户
def AddUser(DBInstanceId,username,passwd):
    accessKeyId, accessKeySecret = "", ""
    clt = client.AcsClient(accessKeyId,accessKeySecret,"cn-hangzhou")
    request=CreateAccountRequest.CreateAccountRequest()
    request.set_DBInstanceId(DBInstanceId)
    request.set_AccountName(username)
    request.set_AccountPassword(passwd)
    result = clt.do_action_with_exception(request)
    print result

def add(name,info):
    passwd = info['passwd']
    for ID in info['DB']:
        instanceid=ID['ID']
        print '==========creatuser with AddUser========='
        print name, passwd, instanceid
        AddUser(instanceid,name,passwd)

# 授权
def Grant(DBInstanceId,dbname,username,privilege):
    accessKeyId, accessKeySecret = "LTAIMplK007fM3iy", "Yy6SoWHIlNXrDg9JsGRNiXD2omX4yc"
    clt = client.AcsClient(accessKeyId,accessKeySecret,"cn-hangzhou")
    request=GrantAccountPrivilegeRequest.GrantAccountPrivilegeRequest()
    request.set_DBName(dbname)
    request.set_DBInstanceId(DBInstanceId)
    request.set_AccountName(username)
    request.set_AccountPrivilege(privilege)
    result = clt.do_action(request)
    print result

# 账号权限，ReadOnly 只读，ReadWrite读写
def grant(name,info):
    passwd = info['passwd']
    for ID in info['DB']:
        instanceid = ID['ID']
        for db in ID['DBNAME']:
            print '==========grand with grant right========='
            print name, passwd, instanceid, db
            Grant(instanceid,db,name,'ReadOnly')

# 查看用户
def ListUser(DBInstanceId):
    accessKeyId, accessKeySecret = "", ""
    clt = client.AcsClient(accessKeyId, accessKeySecret, "cn-hangzhou")
    request = DescribeAccountsRequest.DescribeAccountsRequest()
    request.set_accept_format('json')
    request.set_DBInstanceId(DBInstanceId)
    result = clt.do_action(request)
    res = json.loads(result)
    users = res['Accounts']['DBInstanceAccount']
    for user in users:
        username = user['AccountName']
        print username

# 删除用户
def DelUser(DBInstanceId,username):
    accessKeyId, accessKeySecret = "", ""
    clt = client.AcsClient(accessKeyId,accessKeySecret,"cn-hangzhou")
    request=DeleteAccountRequest.DeleteAccountRequest()
    request.set_DBInstanceId(DBInstanceId)
    request.set_AccountName(username)
    result = clt.do_action(request)
    print result

if __name__ == '__main__':

    # 实例上面的数据库
    list = ['rds72y31682d1mq79tmy']
    username = 'fengshang'
    for i in list:
         ListUser(i)
        #DelUser(i,username)


    # 添加用户
    # s = yaml.load(file('db.yaml'))
    # for name,info in s.items():
    #     # 添加用户
    #     add(name,info)
    #     # 授权
    #     grant(name, info)

