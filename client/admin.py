#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/6/26 17:06  
import weakref,logging,random,struct
from consts import *
from functools import partial
from collections import defaultdict
from twisted.internet import defer,reactor
from twisted.internet.defer import inlineCallbacks
from packet import msg_notify,Parser,Buffer,registe_msg_handler,unregiste_msg_handler

handler={}
def registe_request_handler(cmdId):
    def registe_func(func):
        print u'注册CMD:', cmdId, func
        if handler.has_key(str(cmdId)):
            raise Exception(u'handler重复注册.'+cmdId)
        else:
            handler[str(cmdId)]=func
            return func
        return None
    return registe_func

from twisted.internet import defer

@defer.inlineCallbacks
def request_handler(ro, pack):
    # try:
    if 1:
        cmdId, = struct.unpack(">H",  pack[:2])
        print u'协议ID:', cmdId
        func1=handler.get(str(cmdId), None)
        if callable(func1):
            yield func1(ro, pack[2:])
        else:
            print u'\n@未处理_协议@', cmdId
    # except Exception, e:
    #     print u'\n\n数据包错误:\n', e,'\n'
    #     ro.transport.loseConnection()

############################################################################
############################################################################
############################################################################
############################################################################


def create_GM(usr, pwd):
    from consts import HOST, PORT
    from client import AppProtocol
    from twisted.internet.protocol import ClientCreator
    f = ClientCreator(reactor, AppProtocol, request_handler)
    f.connectTCP(HOST, PORT).addCallback(partial(GM_connected,usr,pwd))

def create_robot(cb):
    from consts import HOST, PORT
    from client import AppProtocol
    from user_manager import request_handler
    from twisted.internet.protocol import ClientCreator
    f = ClientCreator(reactor, AppProtocol, request_handler)
    f.connectTCP(HOST, PORT).addCallback(partial(cb))

class GM():
    def __init__(self,sock=None):
        self.id=0
        self.pwd=0
        self.nick='GM'
        self.mail='gm@game.cn'
        self.sex=1
        self.avata=0
        self.pai=''
        self.ro=sock
        self.roomid=0
        self.tableid=0

gm=GM()
robots={}

def GM_connected(usr, pwd, sock):
    print u"\nGM连接OK!登录...", usr, pwd
    gm.id=usr
    gm.pwd=pwd
    gm.ro=sock
    GM_login()
    @registe_msg_handler(sock,'connectionLost')
    def User_disconnected(*args,**kwargs):
        unregiste_msg_handler(sock,'connectionLost')
        logging.getLogger('user').info('User_disconnected: '+usr)

def GM_register(u):
    res=Buffer()
    res.write_ushort(1024)
    res.write_string(u.id)
    res.write_string(u.pwd)
    res.write_string(u.nick)
    res.write_string(u.mail)
    res.write_short(u.sex)
    res.write_short(u.avata)
    print 'GM_register_request:'
    gm.ro.sendData(res.getValue())

def GM_login():
    res=Buffer()
    res.write_ushort(1025)
    res.write_string(gm.id)
    res.write_string(gm.pwd)
    print 'GM_login_request:', gm.id, gm.pwd
    gm.ro.sendData(res.getValue())

def GM_list_rooms():
    res=Buffer()
    res.write_ushort(1030)
    res.write_short(1)
    res.write_short(1)
    gm.ro.sendData(res.getValue())

def GM_swap_robot(n):
    for i in range(len(n)):
        create_robot(partial(robot_connected,i,n))

def robot_connected(i, arr, sock):
    uid=arr[i]['uid'] #'robot'+str(i)
    pwd=arr[i]['pwd']
    roomid=arr[i].get('roomid',i)
    tableid=arr[i].get('tableid',random.choice(range(4)))
    print u"\n连接OK!登录...", uid, pwd, roomid, tableid
    from user_manager import User
    u=User(sock)
    u.roomid=roomid
    u.tableid=tableid
    u.login(uid,pwd)
    robots[u.id]=u
    robots[sock]=u
    from packet import registe_msg_handler,unregiste_msg_handler
    @registe_msg_handler(sock,'connectionLost')
    def User_disconnected(*args,**kwargs):
        unregiste_msg_handler(sock,'connectionLost')
        logging.getLogger('user').info('User_disconnected: '+u.id)
    @registe_msg_handler(sock, 'lobby_enter')
    def lobby_enter(*args, **kwargs):
        print 'lobby_enter->', args, kwargs
        u=robots[sock]
        if u: u.joinroom(u.roomid,u.tableid)

@registe_request_handler(1025)
@defer.inlineCallbacks
def gm_login(ro, data):
    '''
    GM登录
    :param ro:连接
    :param data:客户端数据包
    :return:
    '''
    print 'GM_login:::::::::::'
    obj=Parser(data)
    sign=obj.read_short()
    if sign==1:
        print u'GM login successed!list room...'
        GM_list_rooms()
    else:
        GM_register(gm)
    yield

@registe_request_handler(1024)
@defer.inlineCallbacks
def gm_register(ro, data):
    '''
    GM注册
    :param ro:连接
    :param data:客户端数据包
    :return:
    '''
    print 'GM_register:::::::::::'
    obj=Parser(data)
    sign=obj.read_short()
    if sign==1:
        print u'register successed!'
        GM_login()
    else:
        print u'register failed!', obj.read_string()
    yield

@registe_request_handler(1030)
@defer.inlineCallbacks
def list_rooms(ro, data):
    '''
    获取大厅房间列表(创建机器人)；
    :param ro:
    :param data:
    :return:
    '''
    print 'list_rooms:::::::::::'
    obj=Parser(data)
    sign=obj.read_short()
    if sign==1:
        print u'lobby enter!'
        dat=obj.read_string()
        arr=[]
        for i in range(10):
            arr.append({'uid':'robot'+str(i),'pwd':'111','roomid':int(i/3),'tableid':i%3})
        GM_swap_robot(arr)
    yield

@registe_request_handler(1052)
@defer.inlineCallbacks
def enter_room(ro, data):
    '''
    玩家加入游戏房间的广播消息；
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    user=obj.read_string()
    nick=obj.read_string()
    print 'player_enter_room:::::::::::', user, nick
    yield

@registe_request_handler(1050)
@defer.inlineCallbacks
def player_ready(ro, data):
    '''
    玩家准备好；
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    tableid=obj.read_ubyte()
    print 'player_ready:::::::::::',  tableid
    yield