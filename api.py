# -*- encoding:utf-8 -*-
#!/usr/bin/env python

"""
author: "Hunter Sun"
 date : "2016,09,08,16:54"
"""

import scale


from bottle import *  # 导入bottle相关的包


@route('/autoscale/api/v1/show/:marathon1/:app', methods=['GET', 'POST'])  # url接口，注意参数书写格式，前面有个冒号表示是参
def show(marathon1, app):
    info = scale.DB()
    a = info.show_db(marathon_name=marathon1, app_id=app)
    return 'hello world. ' + marathon1 + ' ' + app + '\n ' + str(a)


@route('/autoscale/api/v1/insert/:marathon1/:app', methods=['GET', 'POST'])  # url接口，注意参数书写格式，前面有个冒号表示是参
def insert(marathon1, app):
    pass


@route('/autoscale/api/v1/update/:marathon1/:app', methods=['GET', 'POST'])  # url接口，注意参数书写格式，前面有个冒号表示是参
def update(marathon1, app):
    pass


@route('/autoscale/api/v1/delete/:marathon1/:app', methods=['GET', 'POST'])  # url接口，注意参数书写格式，前面有个冒号表示是参
def delete(marathon1, app):
    pass

run(host='0.0.0.0', port=8080)
