# -*- encoding:utf-8 -*-
#!/usr/bin/env python

"""
Author: "Hunter Sun"
 Date : "2016,08,24,11:34"
"""

import pymysql
import os
import time,datetime
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
    def __init__(self, marathon_host, app_id):
        self.marathon_host = marathon_host
        self.app_id = app_id
        self.now_instances = 1
        self.scale_in = 0
        self.scale_out = 0
        self.auth = ('dcosadmin', 'zjdcos01')
        self.uri = ("http://" + marathon_host + ":8080")

    def get_scale_rule_from_db(self):
        pass

    def get_app_details(self):
        response = requests.get(self.uri + '/v2/apps/' + self.app_id, auth=self.auth).json()
        if response['app']['tasks'] == []:
            print ('No task data on Marathon for App !', self.app_id)
        else:
            app_instances = response['app']['instances']
            self.appinstances = app_instances
            print(self.app_id, "has", self.appinstances, "deployed instances")
            app_task_dict = {}
            for i in response['app']['tasks']:
                taskid = i['id']
                hostid = i['host']
                print ('DEBUG - taskId=', taskid + ' running on ' + hostid)
                app_task_dict[str(taskid)] = str(hostid)
            return app_task_dict

    def get_task_agentstatistics(self, task, host):
        # Get the performance Metrics for all the tasks for the Marathon App specified
        # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
        # Return to Statistics for the specific task for the marathon_app
        response = requests.get('http://' + host + ':5051/monitor/statistics.json').json()
        # print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',host)
        for i in response:
            executor_id = i['executor_id']
            # print("DEBUG -- Printing each Executor ID ", executor_id)
            if executor_id == task:
                task_stats = i['statistics']
                # print ('****Specific stats for task',executor_id,'=',task_stats)
                return task_stats

    def showstatics(self):
        return self.get_avg_cpu_mem(self.get_app_details())

    def get_avg_cpu_mem(self, app_task_dict):
        app_cpu_values = []
        app_mem_values = []
        for task, host in app_task_dict.items():
            task_stats = self.get_task_agentstatistics(task, host)
            cpus_time = (task_stats['cpus_system_time_secs'] + task_stats['cpus_user_time_secs'])
            print("cpus_system_time_secs:", task_stats['cpus_system_time_secs'])
            print("task_stats['cpus_user_time_secs']:", task_stats['cpus_user_time_secs'])
            print ("Combined Task CPU Kernel and User Time for task", task, "=", cpus_time)
            mem_rss_bytes = int(task_stats['mem_rss_bytes'])
            print ("task", task, "mem_rss_bytes=", mem_rss_bytes)
            mem_limit_bytes = int(task_stats['mem_limit_bytes'])
            print ("task", task, "mem_limit_bytes=", mem_limit_bytes)
            mem_utilization = 100 * (float(mem_rss_bytes) / float(mem_limit_bytes))
            print ("task", task, "mem Utilization=", mem_utilization)
            print()
            app_cpu_values.append(cpus_time)
            app_mem_values.append(mem_utilization)
            print(app_cpu_values)
            print(app_mem_values)
            app_avg_cpu = (sum(app_cpu_values) / len(app_cpu_values))
            print ('Current Average  CPU Time for app', self.app_id, '=', app_avg_cpu)
            app_avg_mem = (sum(app_mem_values) / len(app_mem_values))
            print ('Current Average Mem Utilization for app', self.app_id, '=', app_avg_mem)
            # Evaluate whether an autoscale trigger is called for
            print('\n')
            return app_avg_cpu, app_avg_mem

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
                print("need to scale out!")
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
                res = marathon_obj.scale(app_id, trigger_mode, now.strftime("%Y%m%d%H%M%S"), cpu=cpu, mem=memory, thread=thread)
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
    t1 = threading.Thread(target=dcos_init, args=(marathon_name, app_id, ))
    threads.append(t1)
    t2 = threading.Thread(target=test, args=(mat, ))
    threads.append(t2)
    for i in threads:
        try:
            i.start()
        except Exception as e:
            print(e)
