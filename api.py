# -*- encoding:utf-8 -*-
#!/usr/bin/env python

"""
author: "Hunter Sun"
 date : "2016,09,08,16:54"
"""

import marathon_autoscale

from bottle import *  # 导入bottle相关的包


@route('/helloworld/:marathon1/:app', methods=['GET', 'POST'])  # url接口，注意参数书写格式，前面有个冒号表示是参
def update(marathon1,app):
    marathon_autoscale.main(marathon1, app_id=app)
    return 'hello world. ' + marathon1 + ' ' + app

run(host='0.0.0.0', port=8080)
