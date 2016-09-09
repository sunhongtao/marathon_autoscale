# -*- encoding:utf-8 -*-
#!/usr/bin/env python

"""
Author: "Hunter Sun"
 Date : "2016,08,21,9:59"
"""
import requests
import sys
import os
import pymysql
import time
import math
import json
import threading
from kazoo.client import KazooClient

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

conn = pymysql.connect(
    host=db_host,
    user=db_user,
    passwd=db_pass,
    db=db_name,
    charset='utf8')


class Marathon(object):
    def __init__(self, marathon_host):
        self.host = marathon_host
        self.auth = ('dcosadmin', 'zjdcos01')
        self.uri = ("http://" + marathon_host + ":8080")
        self.max_instances = 5

    def get_all_apps(self):
        response = requests.get(self.uri + '/v2/apps', auth=self.auth).json()
        if response['apps'] == []:
            print ("No Apps found on Marathon")
            sys.exit(1)
        else:
            apps = []
            for i in response['apps']:
                appid = i['id'].strip('/')
                apps.append(appid)
            print ("Found the following App LIST on Marathon =", apps)
            self.apps = apps  # TODO: declare self.apps = [] on top and delete this line, leave the apps.append(appid)
            return apps

    def get_app_details(self, marathon_app):
        response = requests.get(self.uri + '/v2/apps/' + marathon_app, auth=self.auth).json()
        if response['app']['tasks'] == []:
            print ('No task data on Marathon for App !', marathon_app)
        else:
            app_instances = response['app']['instances']
            self.appinstances = app_instances
            print(marathon_app, "has", self.appinstances, "deployed instances")
            app_task_dict = {}
            for i in response['app']['tasks']:
                taskid = i['id']
                hostid = i['host']
                print ('DEBUG - taskId=', taskid + ' running on ' + hostid)
                app_task_dict[str(taskid)] = str(hostid)
            return app_task_dict

    def get_marathon_endpoints_by_zk(self, hosts, name, timeout=1.0):
        """
        :param hosts: one of zookeeper's Server ip address
        :param name: the z-node name of marathon in the zookeeper
        :param timeout: to connect to the zookeeper
        :return:
        """
        zk = KazooClient(
            hosts=hosts,
            timeout=timeout,
            read_only=True
        )
        zk.start()
        try:
            zk_node = name if name else 'marathon'
            zk_node = '/' + zk_node + '/leader/'
            marathon_endpoints = [
                'http://' + zk.get(zk_node + n)[0]
                for n in zk.get_children(zk_node)
                ]
        finally:
            zk.stop()
            zk.close()
        return marathon_endpoints

    def get_zk_host_from_db_by_appid(self, app_id):
        """
        :param app_id: in this container,we can get the docker id.then can get the app-id.then get the zk host.
        :return:
        """
        try:
            conn = pymysql.connect(**config)
            cursor = conn.cursor()
            sql = "select ip from dcos_api_manage where id = (select mid from dcos_app_mapi where app_id = '" + app_id + "')"
            cursor.execute(sql)
            zk_ip = cursor.fetchone()[0]
            zk_hosts = zk_ip.split('/')[2]
            cursor.close()
            conn.close()
            marathon_endpoints = self.get_marathon_endpoints_by_zk(str(zk_hosts), 'marathon')
        except Exception as e:
            print ("ERROR: app_id = %s | ", e)
        return marathon_endpoints

    def scale_app(self, app, autoscale_multiplier):
        target_instances_float = self.appinstances * autoscale_multiplier
        target_instances = math.ceil(target_instances_float)
        if (target_instances > self.max_instances):
            print("Reached the set maximum instances of", self.max_instances)
            target_instances = self.max_instances
        else:
            target_instances = target_instances
        data = {'instances': target_instances}
        json_data = json.dumps(data)
        print("json_data: ", json_data)
        headers = {'Content-type': 'application/json', }
        try:
            response = requests.put(self.uri + '/v2/apps/' + app, json_data, headers=headers, auth=self.auth)
        except:
            response = requests.put(self.uri + '/v2/apps/' + app, json_data, headers=headers)
        print ('Scale_app return status code =', response.status_code)


def get_task_agentstatistics(task, host):
    # Get the performance Metrics for all the tasks for the Marathon App specified
    # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
    # Return to Statistics for the specific task for the marathon_app
    response = requests.get('http://'+host + ':5051/monitor/statistics.json').json()
    # print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',host)
    for i in response:
        executor_id = i['executor_id']
        # print("DEBUG -- Printing each Executor ID ", executor_id)
        if executor_id == task:
            task_stats = i['statistics']
            # print ('****Specific stats for task',executor_id,'=',task_stats)
            return task_stats


def get_avg_cpu_mem(marathon_app, app_task_dict):
    app_cpu_values = []
    app_mem_values = []
    for task, host in app_task_dict.items():
        task_stats = get_task_agentstatistics(task, host)
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
        print ('Current Average  CPU Time for app', marathon_app, '=', app_avg_cpu)
        app_avg_mem = (sum(app_mem_values) / len(app_mem_values))
        print ('Current Average Mem Utilization for app', marathon_app, '=', app_avg_mem)
        # Evaluate whether an autoscale trigger is called for
        print('\n')
        return app_avg_cpu, app_avg_mem


def timer():
    print("Successfully completed a cycle, sleeping for 10 seconds ...")
    time.sleep(10)
    return


# ############Init scale rule##################
def dcos_init():
    while True:
        global scale_rule
        scale_rule = []
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        cursor.execute("select * from scale_rule")
        rows = cursor.fetchall()
        for row in rows:
            temp = {
                'RULE_TYPE': row[0],
                'APP_ID': row[1],
                'RULE_NUM': row[2],
                'REP_TIME': row[3],
                'SCALE_OUT': row[4],
                'SCALE_IN': row[5],
                'SCALE_INIT': row[6],
                'SCALE_MAX': row[7],
                'SCALE_INC': row[8],
                'OBL_VALUE': row[9],
                'THRESHOLD': row[10]
            }
            scale_rule.append(temp)
        cursor.close()
        conn.close()
        for info in scale_rule:
            print ("SR: %s = %s, %s = %s" % ('APP_ID', info['APP_ID'], 'SCALE_MAX', info['SCALE_MAX']))
        timer()
    return


def marathon_init():
    marathon = Marathon(marathon_host='20.26.25.148')
    marathon_apps = marathon.get_all_apps()
    print("DEBUG-----------------apps:", marathon_apps)
    marathon_app = input("Please input the app name:")
    # marathon_app = os.environ.get("MARATHON_APP_ID")
    trigger_mode = "or"
    max_cpu_time = 0.1
    max_mem_percent = 0.1
    autoscale_multiplier = 2
    for i in marathon_apps:
        if i == marathon_app:
            print("OK")
    if marathon_app in marathon_apps:
        print ("Found your Marathon App=", marathon_app)
    else:
        print ("Could not find your App =", marathon_app)
        sys.exit(1)
    # Return a dictionary comprised of the target app taskId and hostId.
    while True:
        app_task_dict = marathon.get_app_details(marathon_app)
        print("Marathon  App 'tasks' for", marathon_app, "are=", app_task_dict)
        app_avg_mem, app_avg_cpu = get_avg_cpu_mem(marathon_app, app_task_dict)
        print("DEBUG-----------------OK--------------------")
        if trigger_mode == "and":
            if (app_avg_cpu > max_cpu_time) and (app_avg_mem > max_mem_percent):
                print ("Autoscale triggered based on 'both' Mem & CPU exceeding threshold")
                marathon.scale_app(marathon_app, autoscale_multiplier)
            else:
                print ("Both values were not greater than autoscale targets")
        elif (trigger_mode == "or"):

            if (app_avg_cpu > max_cpu_time) or (app_avg_mem > max_mem_percent):
                print ("Autoscale triggered based Mem 'or' CPU exceeding threshold")
                marathon.scale_app(marathon_app, autoscale_multiplier)
            else:
                print ("Neither Mem 'or' CPU values exceeding threshold")
        timer()

if __name__ == '__main__':
    threads = []
    marathon_init()


    # try:
    #     dcos_init = threading.Thread(target=dcos_init)
    #     marathon_init = threading.Thread(target=marathon_init)
    #     threads.append(dcos_init)
    #     threads.append(marathon_init)
    #     for thread in threads:
    #         thread.setDaemon(True)
    #         thread.start()
    # except Exception as e:
    #     print(e)