#!/usr/bin/env python
#coding=utf-8
import json
import yaml

from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526 import DescribeInstanceMonitorDataRequest


#  ecs实例监控
def Monitor(InstanceId,StartTime,EndTime):
    accessKeyId, accessKeySecret = "", ""
    clt = client.AcsClient(accessKeyId,accessKeySecret,"cn-hangzhou")
    request=DescribeInstanceMonitorDataRequest.DescribeInstanceMonitorDataRequest()
    request.set_InstanceId(InstanceId)
    request.set_StartTime(StartTime)
    request.set_EndTime(EndTime)
    result = clt.do_action_with_exception(request)
    res = json.loads(result)
    #print res
    # for k, v in res.items():
    #     print k, v
    monitors = res['MonitorData']['InstanceMonitorData']
    # print monitors
    for item in monitors:
        for key in item:
            print key,item[key]


if __name__ == '__main__':
    # 实例列表
    list = ['i-']
    StartTime = '2017-11-20T12:00:00Z'
    EndTime = '2017-11-20T12:01:00Z'
    for i in list:
         Monitor(i,StartTime,EndTime)
        #DelUser(i,username)