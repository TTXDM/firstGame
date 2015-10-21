#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/6/30 13:11


def checkPais(Pais):#检查每个玩家能够用到的牌
    s_list="";
    k_list="";
    for str_i in Pais:
        pai_i=ord(str_i)
        for str_j in Pais:
            pai_j=ord(str_j)
            print chr(pai_i),chr(pai_j), s_list
            if pai_i == pai_j:
                continue
            elif pai_j-pai_i> 2:
                continue
            elif pai_j-pai_i==1:
                s_list= addPaiToList(pai_i-1,s_list)
                s_list= addPaiToList(pai_j+1,s_list)
                #s_list=
            elif pai_i=='r' and pai_i=='u':
                s_list= addPaiToList('s',s_list)
                s_list= addPaiToList('t',s_list)
            elif pai_i=='x' and pai_j=='z':
                s_list= addPaiToList('y',s_list)
            elif pai_j-pai_i==2:
                s_list= addPaiToList(pai_i+1,s_list)
            elif pai_i==pai_j:
                k_list= addPaiToList(pai_i,k_list)
    return [s_list,k_list]

def addPaiToList(pai,list_t=''):#将一个元素添加到列表中，并且保证没有重复
    print u'这是新牌加入前的列表' + list_t
    if not chr(pai) in list_t:
        list_t+=chr(pai)
        print u'这是新牌加入后的列表'+ list_t
    return list_t


checkPais('abcdABCD1234')