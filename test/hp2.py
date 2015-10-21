#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/7/15 18:09  

#encoding:utf-8
import random, re, itertools
#风牌-箭牌-字牌[万条筒]
_wan = list('123456789')#万牌的集合;
_tiao = list('ABCDEFGHI')#条子的集合;
_tong = list('abcdefghi')#筒子的集合;
_feng = list('stuvwxy')#风牌和箭牌的集合;
_pais = _wan + _tiao + _tong + _feng
_allPai = _pais * 4#所有牌的集合
_pai = random.sample(_allPai, 14 + 13 + 13 + 13)#随机发牌

sp1 = ''.join(_pai[:14])
sp2 = ''.join(_pai[14:27])
sp3 = ''.join(_pai[27:40])
sp4 = ''.join(_pai[40:])

print '->随机发牌：庄0:', sp1
print '\t->闲1：', sp2
print '\t->闲2：', sp3
print '\t->闲3：', sp4

def isSeven(_pai14):
    '''
            是否是七对；
    '''
    res=re.compile(r'(?:(\w)\1{1}){7}').match(_pai14)
    return res and True or False

def sunzi(arr):
    '''
              找出序列中所有可能的顺子;
    '''
    try:
        arr = map(int, arr)
        for p in arr:
            if  p + 1 in arr and p + 2 in arr:
                yield [p, p + 1, p + 2]
    except:
        raise StopIteration

def parse(arr):
    kk=[[],[],[],[]]
    for s in arr:
        if str(s).isdigit():
            kk[0].append(int(s))
        elif not str(s).isalpha():
            continue
        elif str(s).isupper():
            kk[1].append(ord(s)-ord('A')+1)
        elif str(s).islower() and ord(s)<ord('j'):
            kk[2].append(ord(s)-ord('a')+1)
        else:
            kk[3].append(str(s))
    map(list.sort, kk)
    return kk

# vv=parse(sp1)
# print '__', vv

_sort = [re.findall(_r, sp1) for _r in [r'\d', r'[A-I]', r'[a-i]', r'[stuvwxy]']]
map(list.sort, _sort)
print _sort

# MM= re.compile(r'(?:(\w)\1{1}){7}').match('AAAABBBCCCDDDEE')
# print MM and 1 or 0