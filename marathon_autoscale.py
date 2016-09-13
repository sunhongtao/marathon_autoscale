# -*- encoding:utf-8 -*-
# !/usr/bin/env python

"""
Author: "Hunter Sun"
 Date : "2016,08,24,11:34"
"""

import pymysql
import os
import time, datetime
import json
import math
import requests
import threading

db_user = os.environ.get('DB_USER', 'root')
db_pass = os.environ.get('DB_PASS', 'root123')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', 3306)
db_name = os.environ.get('DB_NAME', 'machine')

config = {
    'user': db_user,
    'password': db_pass,
    'host': db_host,
    'port': db_port,
    'database': db_name,
    'charset': 'utf8'}


class Marathonautoscale(object):
    def __init__(self):
        self.now_instances = 1
        self.scale_in = 0
        self.scale_out = 0
        self.auth = ('dcosadmin', 'zjdcos01')
        self.scale_rule = self.get_scale_rule_from_db()

    def get_scale_rule_from_db(self):
        conn = pymysql.connect(**config)
        cur = conn.cursor()
        try:
            cur.execute("select * from app_scale_rule")
            rows = cur.fetchall()
            for row in rows:
                temp = {
                    'marathon_name': row[0],
                    'app_id': row[1],
                    'max_scale_num': row[2],
                    'per_auto_scale': row[3],
                    'memory': row[4],
                    'cpu': row[5],
                    'thread': row[6],
                    'switch': row[7],
                    'cold-time': row[8],
                    'collect-period': row[9],
                    'continue-period': row[10]
                }
                print("DEBUG------------temp---------:%s  %s " % (temp,temp['switch']))
                if temp['switch']:
                    print("Hellllllllllllllllllllll")
                    scale_rule[temp['marathon_name']][temp['app_id']] = temp
                    print("scaleu -----------------%s" % scale_rule)
                    print("scale cp %s" % scale_rule[temp['marathon_name']][temp['app_id']]['switch'])
                    if scale_rule[scale_rule[temp['marathon_name']][temp['app_id']]['cpu']]:
                        try:
                            cur.execute("select * from quota_info where app_id = %s AND rule_type=%s",
                                        (scale_rule[temp['app_id']], "cpu"))
                            rows = cur.fetchall()
                            for row in rows:
                                print("DEBUG====dcosinit======{},{}".format(row[0], row[1]))
                                scale_rule[temp['marathon_name']]['cpu_max_threshold'] = row[3]
                                scale_rule[temp['marathon_name']]['cpu_min_threshold'] = row[4]
                        except Exception as e:
                            print(e)
                    if scale_rule[temp['marathon_name']['app_id']['memory']]:
                        try:
                            cur.execute("select * from quota_info where app_id = %s AND rule_type=%s",
                                        (scale_rule[temp['marathon_name']][temp['app_id']], "memory"))
                            rows = cur.fetchall()
                            for row in rows:
                                print("DEBUG====dcosinit======{},{}".format(row[0], row[1]))
                                scale_rule[temp['marathon_name']]['mem_max_threshold'] = row[3]
                                scale_rule[temp['marathon_name']]['mem_min_threshold'] = row[4]
                        except Exception as e:
                            print(e)
                    print("the scale rule: %s " % scale_rule)
                else:
                    print("This app's scale switch is off!")
        except Exception as e:
            print(e)
        cur.close()
        conn.close()
        timer()
        return scale_rule

    def scale_app(self, app, autoscale_multiplier):
        max_instances = scale_rule[app]['max_scale_num']
        target_instances_float = self.appinstances * autoscale_multiplier
        target_instances = math.ceil(target_instances_float)
        if (target_instances > max_instances):
            print("Reached the set maximum instances of", max_instances)
            target_instances = max_instances
        else:
            target_instances = target_instances
        data = {'instances': target_instances}
        json_data = json.dumps(data)
        print("json_data: ", json_data)
        headers = {'Content-type': 'application/json'}
        try:
            response = requests.put(self.uri + '/v2/apps/' + app, json_data, headers=headers, auth=self.auth)
        except:
            response = requests.put(self.uri + '/v2/apps/' + app, json_data, headers=headers)
        print ('Scale_app return status code =', response.status_code)

    def scale(self, app_id, trigger_mode, scale_time, cpu=None, mem=None, thread=None):
        print("DEBUG------------scale--------scale_rule:%s" % scale_rule)
        per_auto_scale = scale_rule[app_id]['per_auto_scale']
        max_scale_num = scale_rule[app_id]['max_scale_num']
        now_quota_value = {'cpu': 1, 'mem': 1}
        if trigger_mode == 'or':
            for k, v in now_quota_value.items():  # 遍历CPU memory
                print("k=%s, v=%s" % (k, v))
                index_max_info = k + '_max_threshold'  # cpu, memory的最大阈值
                index_min_info = k + '_min_threshold'  # cpu, memory的最小阈值
                if v > scale_rule[app_id][index_max_info]:
                    self.scale_out = 1
                elif v < scale_rule[app_id][index_min_info]:
                    self.scale_in = -1
            print("scale out =%s, scale in=%s" % (self.scale_out, self.scale_in))
            if self.scale_out == 1:  # 当碰到scale_out=1 scale_in=-1时，会优先考虑扩容
                print("Need to scale out!")
                return 2
            elif self.scale_in == -1:
                print("Need to scale in!")
                return 1
            else:
                return 0
        if trigger_mode == 'and':
            for k, v in now_quota_value.items():
                index_max_info = k + '_max_threshold'
                index_min_info = k + '_min_threshold'
                if v > scale_rule[app_id][index_max_info]:
                    self.scale_out += 1
                if v < scale_rule[app_id][index_min_info]:
                    self.scale_out -= 1
            if self.scale_out == len(now_quota_value):
                print("need to scale out!")
                return 2
            elif self.scale_in + len(now_quota_value):
                print("need to scale in!")
                return 1
            else:
                return 0

scale_rule = {}


def timer():
    """
    :this time is collect period.get from the db.
    """
    print("Successfully completed a cycle, sleeping for 5 seconds ...")
    time.sleep(5)
    return


def dcos_init(marathon_name, appid):
    while True:
        global scale_rule
        conn = pymysql.connect(**config)
        cur = conn.cursor()
        try:
            cur.execute("select * from app_scale_rule where marathon_name = %s and app_id = %s",
                        (str(marathon_name), str(appid)))
            rows = cur.fetchall()
            for row in rows:
                temp = {
                    'marathon_name': row[0],
                    'appid': row[1],
                    'trigger_mode': row[2],
                    'max_scale_num': row[3],
                    'per_auto_scale': row[4],
                    'memory': row[5],
                    'cpu': row[6],
                    'thread': row[7],
                    'switch': row[8]
                }
                print("DEBUG-------------temp---------:%s" % temp)
                if temp['switch']:
                    scale_rule[row[1]] = temp
                    if scale_rule[appid]['cpu']:
                        try:
                            cur.execute("select * from quota_info where app_id = %s AND rule_type=%s",
                                        (str(appid), "cpu"))
                            rows = cur.fetchall()
                            for row in rows:
                                print("DEBUG====dcosinit======{},{}".format(row[0], row[1]))
                                scale_rule[appid]['cpu_max_threshold'] = row[3]
                                scale_rule[appid]['cpu_min_threshold'] = row[4]
                        except Exception as e:
                            print (e)
                    if scale_rule[appid]['memory']:
                        try:
                            cur.execute("select * from quota_info where app_id = %s AND rule_type=%s",
                                        (str(appid), "memory"))
                            rows = cur.fetchall()
                            for row in rows:
                                print("DEBUG====dcosinit======{},{}".format(row[0], row[1]))
                                scale_rule[appid]['mem_max_threshold'] = row[3]
                                scale_rule[appid]['mem_min_threshold'] = row[4]
                        except Exception as e:
                            print(e)
                else:
                    print("This app's scale switch is off!")
        except Exception as e:
            print(e)
        cur.close()
        conn.close()
        timer()

def timer():
    """
    :this time is collect period.get from the db.
    """
    print("Successfully completed a cycle, sleeping for 5 seconds ...")
    time.sleep(5)
    return

def test(marathon_obj):
    app_id = marathon_obj.app_id
    while True:
        if len(scale_rule):
            now = datetime.datetime.now()
            cpu = scale_rule[app_id]['cpu']
            memory = scale_rule[app_id]['memory']
            thread = scale_rule[app_id]['thread']
            trigger_mode = scale_rule[app_id]["trigger_mode"]
            print("DEBUG----------test---------cpu: {}".format(cpu))
            print("DEBUG----------test---------memory: {}".format(memory))
            print("DEBUG----------test---------thread: {}".format(thread))
            try:
                res = marathon_obj.scale(app_id, trigger_mode, now.strftime("%Y%m%d%H%M%S"), cpu=cpu, mem=memory,
                                         thread=thread)
                if res == 0:
                    print (app_id, "No scale!")
                elif res == 1:
                    print (app_id, "Scale in!")
                elif res == 2:
                    print(app_id, "Scale out!")
            except Exception as e:
                print ("ERROR: app_ID = %s | " % app_id, e)
            timer()
        else:
            pass


def main(marathon_name, app_id):
    # app_id = "http.check"
    # marathon_name = "20.26.25.148"
    threads = []
    mat = Marathonautoscale(marathon_name, app_id)
    t1 = threading.Thread(target=dcos_init, args=(marathon_name, app_id,))
    threads.append(t1)
    t2 = threading.Thread(target=test, args=(mat,))
    threads.append(t2)
    for i in threads:
        try:
            i.start()
        except Exception as e:
            print(e)


