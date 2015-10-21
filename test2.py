#!/usr/bin/env python
# coding:utf-8
#Author:  Administrator
#Created: 2015/9/23 14:26

str1='abc,ghi,,123,555,6'
str2=sorted('abcghi1235556')

print str2==sorted(str1.replace(',',''))