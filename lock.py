# -*- encoding:utf-8 -*-
#!/usr/bin/env python

"""
Author: "Hunter Sun"
 Date : "2016,09,09,15:39"
"""

import threading
import time

lock = threading.Lock()

def show(i):
    lock.acquire()
    for k in range(20):
        print("In the thread: {}\n".format(i))
        print("In the lock{}".format(k))
    time.sleep(5)
    lock.release()

index = 0
def fil(marathonname,appid):
    global index
    if index != 1:
        f = open("1.txt",'r')
        index = 0
    else:
        print("Someone is handle!")



if __name__ == '__main__':
    threads = []

    for i in range(4):
        t = threading.Thread(target=show, name="Thread %d" % i, args=(i,))
        t.start()
        # time.sleep(2)
