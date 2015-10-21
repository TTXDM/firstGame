#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/10/13 10:33  

import xmlrpclib

try:
    myrpc = xmlrpclib.ServerProxy("http://127.0.0.1:7080")
    file = open('logging.json', 'rb').read()  # Binary mode open
    myrpc.attachfile("pageName_", "logging.json", file)
except:
    pass