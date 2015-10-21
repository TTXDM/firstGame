#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/8/3 15:30  

opt_zua, opt_cup, opt_chi, opt_peng, opt_gang, opt_agng, opt_bu, opt_hu=101,102,103,104,105,106,107,108

class Opt_info():
    def __init__(self, tableid=-1, opt=None, defered_call=None):
        self.tableid=tableid
        self.opt=opt
        self.defered_call=defered_call
    def __eq__(self, other):
        return self.tableid==other.tableid and self.opt==other.opt


arr=[]

arr.append(Opt_info(2,opt_gang,'00000'))
arr.append(Opt_info(1,opt_chi,'aaaaaa'))
arr.append(Opt_info(0,opt_peng,'vvvvv'))

arr.sort(key=lambda a:a.opt)

for i in arr:
    print i.defered_call