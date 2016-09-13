# -*- encoding:utf-8 -*-
# !/usr/bin/env python

"""
Author: "Hunter Sun"
 Date : "2016,09,12,16:17"
"""
import time
import threading


def xx(rule):
    if not rule.has_key('time'):
        start_time = time.time()
        rule['time'] = start_time
    print("before===time %s" % rule['time'])
    for i in range(10000000):
        i += 1
    rule['time'] = time.time()
    print("after====time %s" % rule['time'])


def test():
    rule = {1: 2, 66: 77}
    for i in range(5):
        xx(rule)
        print("*" * 10)


def dcos_init():
    while True:
        print("DEBUG======dcos_init=====")
        time.sleep(5)


def test1():
    print("DEBUG======test=====")
    threads1 = []
    i = 0
    global  scale_time
    scale_time = {}
    for i in range(2):
        t = threading.Thread(target=scale, args=(i,))
        threads1.append(t)
    for i in threads1:
        try:
            i.start()
        except Exception as e:
            print(e)
    time.sleep(4)


def scale(num):
    if num not in scale_time:
        scale_time[num] = time.time()
    while True:
        print("DEBUG======scale======%s" % num)
        print("DEBUG======scale======%s" % scale_time[num])
        if num > 0:
            scale_time[num] = time.time()
            time.sleep(2)
        time.sleep(5)


def main():
    threads = []
    t1 = threading.Thread(target=dcos_init)
    threads.append(t1)
    t2 = threading.Thread(target=test1)
    threads.append(t2)
    for i in threads:
        try:
            i.start()
        except Exception as e:
            print(e)


# main()

# rule = []
rule = [
    {"marathonid"}
]

b = 1
c = 2
if b == 1:
    d = 1
    print("in b==1 :", d+1)
if c == 2:
    d = 2
    print("in c==2", d+1)