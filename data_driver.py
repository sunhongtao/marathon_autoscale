#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#       Filename: data_driver.py
#
#         Author: xwisen 1031649164@qq.com
#    Description: ---
#         Create: 2016-08-26 08:52:11
#  Last Modified: 2016-08-26 08:52:11
# ***********************************************

import os
import sys
import httplib2
import json
from influxdb import InfluxDBClient

# prometheus config
promethus_ip_addr = os.environ.get("PROMETHEUS_IP_ADDR", "10.254.10.18")
promethus_port = os.environ.get("PROMETHEUS_PORT", "9091")
promethus_group = os.environ.get("PROMETHEUS_GROUP", "slave")
promethus_job = os.environ.get("PROMETHEUS_JOB", "dcos")

# influxdb config
influxdb_ip_addr = os.environ.get("INFLUXDB_IP_ADDR", "20.26.25.148")
influxdb_port = os.environ.get("INFLUXDB_PORT", "8086")
influxdb_user = os.environ.get("INFLUXDB_USER", "root")
influxdb_password = os.environ.get("INFLUXDB_PASSWORD", "root")
influxdb_db_name = os.environ.get("INFLUXDB_DB_NAME", "dcos")

error_status = {"succeed": 0, "mem_error": 1, "cpu_error": 2, "other_error": 3}


# influxdb_info = {
# "ip_addr": influxdb_ip_addr,
# "port": influxdb_port,
# "user": influxdb_user,
# "password": influxdb_password,
# "db_name": influxdb_db_name
# }

def data_driver(driver_type, marathon_info, app_id):
    """data_driver return specified application information
    application information is a dict, include:
        marathon_info
        app_id
        app_av_cpu
        app_av_mem
    """
    err_info = {"marathon_info": marathon_info, "app_id": app_id,
                "error": "driver not support!"
                }

    if driver_type == "influxdb":
        return influxdb_driver(marathon_info, app_id)
    elif driver_type == "prometheus":
        return prometheus_driver(marathon_info, app_id)
    else:
        print(driver_type, "driver_type is not support, only influxdb and prometheus support!")
        return err_info


def influxdb_driver(marathon_info, app_id):
    c = InfluxDBClient(influxdb_ip_addr, influxdb_port,
                       influxdb_user, influxdb_password,
                       influxdb_db_name)
    c.query("select * from container limit 3")


def prometheus_driver(marathon_info, app_id):
    # marathon_info like :
    # 10.254.9.57 or www.marathon.com

    # return_info = {"marathon_info": marathon_info, "app_id": app_id,"status":error_status["other_error"],"error": "driver not support!"}

    marathon_url = "http://" + marathon_info + ":8080"
    conn = httplib2.Http()
    headers = {"Content-type": "application/json"}
    response, content = conn.request(marathon_url + "/v2/apps/" + app_id, "GET", headers=headers)
    if response.status != 200:
        return_info = {"marathon_info": marathon_info, "app_id": app_id, "status": error_status["other_error"],
                       "error": "marathon response code" + str(response.status) + "found!"}
    else:
        task_ids = []
        app = json.loads(content)
        headers = {"Content-type": "application/json"}
        prometheus_url = "http://" + promethus_ip_addr + ":" + promethus_port + "/api/v1/query?"
        cpu_avg = 0
        mem_avg = 0
        for task in app["app"]["tasks"]:
            conn = httplib2.Http()
            # cpu average info
            s = "irate(container_cpu_system_seconds_total{group=\"" + promethus_group + "\",job=\"" + promethus_job + "\",mesos_task_id=\"" + \
                task["id"] + "\"}[1m])"
            req_url = prometheus_url + "query=" + s
            print ("req_url is : ", req_url)
            response, content = conn.request(req_url, "GET", headers=headers)
            if response.status != 200:
                print (response.status)
                return_info = {"marathon_info": marathon_info, "app_id": app_id, "status": error_status["cpu_error"],
                               "error": "prometheus system cpu response code" + str(response.status) + "found!"}
            else:
                resq = json.loads(content)
                for r in resq["data"]["result"]:
                    if len(r["metric"]["id"]) == 72:
                        sys_cpu_rate = float(r["value"][1])
                        print ("sys_cpu_rate is :", sys_cpu_rate)

            u = "irate(container_cpu_user_seconds_total{group=\"" + promethus_group + "\",job=\"" + promethus_job + "\",mesos_task_id=\"" + \
                task["id"] + "\"}[1m])"
            req_url = prometheus_url + "query=" + u
            print ("req_url is : ", req_url)
            response, content = conn.request(req_url, "GET", headers=headers)
            if response.status != 200:
                print (response.status)
                return_info = {"marathon_info": marathon_info, "app_id": app_id, "status": error_status["cpu_error"],
                               "error": "prometheus user cpu response code" + str(response.status) + "found!"}
            else:
                resq = json.loads(content)
                for r in resq["data"]["result"]:
                    if len(r["metric"]["id"]) == 72:
                        user_cpu_rate = float(r["value"][1])
                        print ("user_cpu_rate is: ", user_cpu_rate)
            print ("first cpu_avg is: ", cpu_avg)
            if cpu_avg == 0:
                cpu_avg = float(sys_cpu_rate + user_cpu_rate)
            else:
                cpu_avg = float((cpu_avg + sys_cpu_rate + user_cpu_rate) / 2)

                # average mem info
            l = "sum(container_spec_memory_limit_bytes{group=\"" + promethus_group + "\",job=\"" + promethus_job + "\",mesos_task_id=\"" + \
                task["id"] + "\"})"
            req_url = prometheus_url + "query=" + l
            print ("req_url is : ", req_url)
            response, content = conn.request(req_url, "GET", headers=headers)
            if response.status != 200:
                print (response.status)
                return_info = {"marathon_info": marathon_info, "app_id": app_id, "status": error_status["mem_error"],
                               "error": "prometheus limits mem response code" + str(response.status) + "found!"}
            else:
                resq = json.loads(content)
                for r in resq["data"]["result"]:
                    sum_limit_mem_bytes = float(r["value"][1])
                    print ("sum limit mem bytes is: ", sum_limit_mem_bytes)
            m = "sum(container_memory_usage_bytes{group=\"" + promethus_group + "\",job=\"" + promethus_job + "\",mesos_task_id=\"" + \
                task["id"] + "\"})"
            req_url = prometheus_url + "query=" + m
            print ("req_url is : ", req_url)
            response, content = conn.request(req_url, "GET", headers=headers)
            if response.status != 200:
                print (response.status)
                return_info = {"marathon_info": marathon_info, "app_id": app_id, "status": error_status["mem_error"],
                               "error": "prometheus mem response code" + str(response.status) + "found!"}
            else:
                resq = json.loads(content)
                for r in resq["data"]["result"]:
                    sum_mem_bytes = float(r["value"][1])
                    print ("sum mem bytes is: ", sum_mem_bytes)
                if mem_avg == 0:
                    mem_avg = float(sum_mem_bytes / sum_limit_mem_bytes)
                    print (mem_avg)
                else:
                    mem_avg = float((mem_avg + (sum_mem_bytes / sum_limit_mem_bytes)) / 2)
                    print (mem_avg)
            task_ids.append(task["id"])
        print ("tasks is:", task_ids)
        cpu_avg = round(cpu_avg * 100, 2)
        print ("cpu average is: ", cpu_avg)
        mem_avg = round(mem_avg * 100, 2)
        print ("mem average is: ", mem_avg)
        return_info = {"marathon_info": marathon_info, "app_id": app_id, "status": error_status["succeed"],
                       "cpu": cpu_avg, "mem": mem_avg}
    return return_info


def main():
    marathon_url = "http://10.254.9.57:8080"
    conn = httplib2.Http()
    # conn.add_credentials("dcosadmin", "zjdcos01")
    header = {"Content-type": "application/json"}
    print(marathon_url + "/v2/apps/")
    resp, content = conn.request(
        marathon_url + "/v2/apps/", "GET", headers=header)
    print("resp type is: ", type(resp), "content type is: ", type(content))
    if resp.status == 200:
        apps = json.loads(content)
        print("apps type is: ", type(apps))
        if apps["apps"] == []:
            print("no apps")
            sys.exit(1)
        apps_name = []
        for app in apps["apps"]:
            app_name = app["id"].strip("/")
            apps_name.append(app_name)
        print("marathon have apps: ", apps_name)
    else:
        print("status code is not 200 !")

    print("app have tasks", data_driver("prometheus", "10.254.9.57", "nginx"))


if __name__ == "__main__":
    main()
