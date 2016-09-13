# # -*- encoding:utf-8 -*-
# #!/usr/bin/env python
#
# """
# Author: "Hunter Sun"
#  Date : "2016,08,21,10:53"
# """
# import os
# import pymysql
#
# db_user = os.environ.get('DB_USER', 'root')
# db_pass = os.environ.get('DB_PASS', 'root123')
# db_host = os.environ.get('DB_HOST', 'localhost')
# db_port = os.environ.get('DB_PORT', 3306)
# db_name = os.environ.get('DB_NAME', 'machine')
#
# config = {
#     'user':db_user,
#     'password':db_pass,
#     'host':db_host,
#     'port':db_port,
#     'database':db_name,
#     'charset':'utf8'}
#
# def one():
#     conn = pymysql.connect(**config)
#     cur = conn.cursor()
#     sql_info = "select * from douban limit 1"
#     cur.execute(sql_info)
#     for k in cur.fetchall():
#         print(k)
#     cur.close()
#     conn.close()
# # one()
#
# # import requests
# # def get_task_agentstatistics(task, host):
# #     # Get the performance Metrics for all the tasks for the Marathon App specified
# #     # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
# #     # Return to Statistics for the specific task for the marathon_app
# #     response = requests.get('http://'+host + ':5051/monitor/statistics.json').json()
# #     # print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',host)
# #     for i in response:
# #         executor_id = i['executor_id']
# #         # print("DEBUG -- Printing each Executor ID ", executor_id)
# #         if executor_id == task:
# #             task_stats = i['statistics']
# #             # print ('****Specific stats for task',executor_id,'=',task_stats)
# #             return task_stats
# #
# # task = "http.check.684d0eee-676f-11e6-9663-b64e1e88076d"
# # host = "20.26.25.149"
# # task_stats = get_task_agentstatistics(task, host)
# # print(task_stats)
# #
# # print(task_stats["mem_limit_bytes"])
# # print(task_stats["timestamp"])
#
# # '''
# # test the mysql connection
# # '''
# # conn = pymysql.connect(**config)
# # cur = conn.cursor()
# # app_id = "http.check"
# # marathon_name = "20.26.25.148"
# # try:
# #     cur.execute("select * from app_scale_rule where marathon_name = %s and app_id = %s",
# #                 (str(marathon_name), str(app_id)))
# #     rows = cur.fetchall()
# #     print(rows)
# #     for row in rows:
# #         print(row[8])
# # except Exception as e:
# #     print(e)
# db_user = os.environ.get('DB_USER', 'root')
# db_pass = os.environ.get('DB_PASS', 'root123')
# db_host = os.environ.get('DB_HOST', 'localhost')
# db_port = os.environ.get('DB_PORT', 3306)
# db_name = os.environ.get('DB_NAME', 'machine')
# config = {
#     'user': db_user,
#     'password': db_pass,
#     'host': db_host,
#     'port': db_port,
#     'database': db_name,
#     'charset': 'utf8'}
#
#
# from marathon_autoscale import *
# app_id = 'health.check'
# a = ['cpu', 'memory']
# now_quota_value = {'cpu': 1, 'memory': 1 }
# print(scale_rule)
# trigger = 'or'
# scale_in = 0
# scale_out = 0
# per_auto_scale = 1
# # per_auto_scale = scale_rule[app_id]['per_auto_scale']
#
# scale_rule = {}
#
#
# def timer():
#     print("Successfully completed a cycle, sleeping for 5 seconds ...")
#     time.sleep(100)
#     return
#
#
# def dcos_init(marathon_name, appid):
#     while True:
#         global scale_rule
#         conn = pymysql.connect(**config)
#         cur = conn.cursor()
#         try:
#             cur.execute("select * from app_scale_rule where marathon_name = %s and app_id = %s",
#                         (str(marathon_name), str(appid)))
#             rows = cur.fetchall()
#             for row in rows:
#                 temp = {
#                     'marathon_name': row[0],
#                     'appid': row[1],
#                     'trigger_mode': row[2],
#                     'max_scale_num': row[3],
#                     'per_auto_scale': row[4],
#                     'memory': row[5],
#                     'cpu': row[6],
#                     'thread': row[7],
#                     'switch': row[8]
#                 }
#                 if temp['switch']:
#                     scale_rule[row[1]] = temp
#                 else:
#                     pass
#         except Exception as e:
#             print(e)
#         # print("scale-rule app_id's CPU %s" % scale_rule[appid]['cpu'])
#         if scale_rule[appid]['cpu']:
#             try:
#                 cur.execute("select * from quota_info where app_id = %s AND rule_type=%s",(str(appid),"cpu"))
#                 rows = cur.fetchall()
#                 for row in rows:
#                     print("DEBUG====dcosinit======{},{}".format(row[0], row[1]))
#                     scale_rule[appid]['cpu_max_threshold'] = row[3]
#                     scale_rule[appid]['cpu_min_threshold'] = row[4]
#             except Exception as e:
#                 print (e)
#         elif scale_rule[appid]['memory']:
#             try:
#                 cur.execute("select * from quota_info where app_id = %s AND rule_type=%s", (str(appid), "memory"))
#                 rows = cur.fetchall()
#                 for row in rows:
#                     print("DEBUG====dcosinit======{},{}".format(row[0], row[1]))
#                     scale_rule[appid]['mem_max_threshold'] = row[3]
#                     scale_rule[appid]['mem_min_threshold'] = row[4]
#             except Exception as e:
#                 print (e)
#         cur.close()
#         conn.close()
#         timer()
#
#
# dcos_init('20.26.25.148', 'health.check')
#
# if trigger == 'or':
#     for k,v in now_quota_value.items():  # 遍历CPU memory
#         index_max_info = k + '_max_threshold'  # cpu,memory的最大阈值
#         index_min_info = k + '_min_threshold'  # cpu,memory的最小阈值
#         if v > scale_rule[0][index_max_info]:
#             scale_out = 1
#         elif v < scale_rule[0][index_min_info]:
#             scale_in = -1
#     if scale_out == 1:
#         print("Need to scale out!")
#     elif scale_in == -1:
#         print("need to scale in!")
#
# if trigger == 'and':
#     for k, v in now_quota_value.items():
#         index_max_info = k + '_max_threshold'
#         index_min_info = k + '_min_threshold'
#         if v > scale_rule[0][index_max_info]:
#             scale_out += 1
#         if v < scale_rule[0][index_min_info]:
#             scale_out -= 1
#     if scale_out == len(now_quota_value):
#         print("need to scale out!")
#     elif scale_in + len(now_quota_value):
#         print("need to scale out!")

import time
import math

now_info = {'cpu': 1, 'memory': 1, 'thread': 5}
now_instance = 2
scale_rule = [{'cold_time': u'60', 'memory_max_threshold': '2.0', 'memory': 1, 'app_id': u'http.check',
               'tag': u'True', 'cpu_min_threshold': '0.6', 'thread': 0, 'per_auto_scale': 1,
               'cpu_max_threshold': '0.8', 'collect_period': 5, 'marathon_name': u'20.26.25.148',
               'switch': 1, 'continue_period': 3, 'min_scale_num': 1, 'max_scale_num': 3, 'memory_min_threshold': '0.6',
               'cpu': 1}]


def getinfo():
    now_info = {'cpu': 1, 'memory': 1, 'app_task_num': 1}
    now_quota_info = {}
    now_quota_info['cpu'] = now_info['cpu']
    now_quota_info['memory'] = now_info['memory']
    now_instances = now_info['app_task_num']
    return now_quota_info, now_instances


def scale_app_out():
    pass


count = 0
start_time = time.time()
scale_out = 0
scale_in = 0
for rule in scale_rule:  # 遍历各个应用的规则  app1  app2
    now_quota_info, now_tasks_number = getinfo()
    for k, v in now_quota_info.items():     # 遍历各个规则  app1: {cpu  memory}
        index_max_info = k + '_max_threshold'
        index_min_info = k + '_min_threshold'

        if v > rule[index_max_info]:
            scale_out += 1
        if v < rule[index_min_info]:
            scale_out -= 1
    if scale_out == len(now_quota_info):
        print("need to scale out!")
    elif scale_in + len(now_quota_info):
        print("need to scale out!")
    else:
        print("Don't need to scale")

    end_time = time.time()
    if count == rule['continue_period'] and int(math.ceil(end_time - start_time)) > rule['cold_time']:
        scale_app_out()
        pass
    else:
        count += 1
        pass

    time.sleep(rule['collect_period'])
