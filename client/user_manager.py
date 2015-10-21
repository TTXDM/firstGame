#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/6/26 17:06  
from consts import *
import weakref,logging,random,struct
from functools import partial
from collections import defaultdict
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from packet import msg_notify
from packet import Parser,Buffer
from packet import registe_msg_handler,unregiste_msg_handler

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
@registe_request_handler(1024)
@defer.inlineCallbacks
def user_register(ro, data):
    '''
    玩家注册
    :param ro:连接
    :param data:客户端数据包
    :return:
    '''
    print 'user_register:::::::::::'
    obj=Parser(data)
    sign=obj.read_short()
    if sign==1:
        print u'register successed!'
        yield msg_notify(ro,'register_success')
    else:
        print u'register failed!', obj.read_string()
    yield

@registe_request_handler(1025)
@defer.inlineCallbacks
def auth_login(ro, data):
    '''
    用户登录
    :param ro:连接
    :param data:客户端数据包
    :return:
    '''
    print 'auth_login:::::::::::'
    obj=Parser(data)
    sign=obj.read_short()
    if sign==1:
        print u'login successed!'
        avatar=obj.read_ushort()
        yield msg_notify(ro,'login_success',avatar)
    else:
        yield msg_notify(ro,'login_failed')
        print u'login failed!', obj.read_string()
    yield

@registe_request_handler(1030)
@defer.inlineCallbacks
def list_rooms(ro, data):
    '''
    获取大厅房间列表；
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
        print dat
        yield msg_notify(ro,'lobby_enter')
    yield

@registe_request_handler(1032)
@defer.inlineCallbacks
def enter_room(ro, data):
    '''
    加入游戏房间；
    :param ro:
    :param data:
    :return:
    '''
    print 'enter_room:::::::::::'
    obj=Parser(data)
    sign=obj.read_short()
    if sign==1:
        roomid=obj.read_ushort()
        tableid=obj.read_ubyte()
        print u'room enter!', roomid,  tableid
        yield msg_notify(ro,'room_enter',roomid,tableid)
    else:
        print u'room enter failed!', obj.read_string()
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

@registe_request_handler(1051)
@defer.inlineCallbacks
def game_start(ro, data):
    '''
    麻将开局；
    :param ro:
    :param data:
    :return:
    '''
    print 'game_start:::::::::::'
    obj=Parser(data)
    zuang=obj.read_ubyte()
    pai=obj.read_string()
    sai=[]
    for i in range(6):
        sai.append(obj.read_ubyte())
    jin1=chr(obj.read_ubyte())
    jin2=chr(obj.read_ubyte())
    jin=[]
    for i in range(4):
        jin.append(obj.read_string())
    print u'庄:',zuang
    print u'牌:',pai
    print u'骰子:',sai
    print u'上精:',jin1
    print u'下精:',jin2
    print u'下精分布:',jin
    yield msg_notify(ro,'game_start',zuang,pai,sai,jin1,jin2,jin)

@registe_request_handler(1054)
@defer.inlineCallbacks
def zua_pai(ro, data):
    '''
    抓牌；
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    pai=chr(obj.read_ubyte())
    tableid=obj.read_ubyte()
    print 'zua_pai:::::::::::', tableid, PAI_NAME(pai)
    yield msg_notify(ro,'zua_pai',tableid,pai)

@registe_request_handler(1059)
@defer.inlineCallbacks
def player_drop(ro, data):
    '''
    玩家出牌广播；
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    tableid=obj.read_ubyte()
    pai=chr(obj.read_ubyte())
    print 'player_drop:::::::::::', tableid, PAI_NAME(pai)
    yield msg_notify(ro,'player_drop',tableid,pai)

@registe_request_handler(1089)
@defer.inlineCallbacks
def hu_pai(ro, data):
    '''
    胡牌
    :return:
    '''
    print u"hu_pai:"
    obj=Parser(data)
    tableid=obj.read_ubyte()
    str1=obj.read_string()
    pai=obj.read_ubyte()
    int1=obj.read_short()
    int2=obj.read_short()
    int3=obj.read_short()
    int4=obj.read_short()
    flag=obj.read_string()
    yield msg_notify(ro,'hu_pai',tableid,pai)


##############################################################################################
class User():
    def __init__(self,sock):
        self.id=''
        self.nick='robot'
        self.mail=''
        self.sex=0
        self.avata=0
        self.pai=''
        self.pwd='111'
        self.ro=sock
        self.roomid=0
        self.tableid=0
        @registe_msg_handler(self.ro, 'login_success')
        def login_success(avata, *args, **kwargs):
            print 'login_success->', args, kwargs, avata
            self.avata=avata
            logging.getLogger('user').info('login_success.')
            self.lobby()
        @registe_msg_handler(self.ro, 'login_failed')
        def login_failed(*args, **kwargs):
            print 'login_failed->', args, kwargs
            logging.getLogger('user').info('login_failed.')
            self.register()
        @registe_msg_handler(self.ro, 'register_success')
        def register_success(*args, **kwargs):
            print 'register_success->', args, kwargs
            logging.getLogger('user').info('register_success.')
            self.login(self.id,self.pwd)
        @registe_msg_handler(self.ro, 'lobby_enter')
        def lobby_enter(*args, **kwargs):
            print 'lobby_enter->', args, kwargs
            logging.getLogger('user').info('lobby_enter.')
            # self.joinroom()
        @registe_msg_handler(self.ro, 'room_enter')
        def room_enter(roomid, tableid, *args, **kwargs):
            self.roomid=roomid
            self.tableid=tableid
            print '================================================================================'
            print 'room[%s]<%s>room_enter->room[%s]<%s>' % (self.roomid, self.tableid, roomid, tableid)
            logging.getLogger('user').info('room_enter. roomid:%s, tableid:%s'%(roomid, tableid))
            self.standby()
        @registe_msg_handler(self.ro, 'game_start')
        def game_start(*args):
            zuang,pai,sai,jin1,jin2,jin=args
            print 'game_start->', args
            logging.getLogger('user').info('game_start.')
            self.pai=pai
            import time
            print time.clock()
            self.tt=time.clock()
            if zuang==self.tableid:
                reactor.callLater(20, partial(self.drop))
        @registe_msg_handler(self.ro, 'player_drop')
        def player_drop(*args):
            import time
            print u'====延时：', self.tt-time.clock()
            self.tt=time.clock()
            tableid,pai=args
            print 'player_drop->', tableid, pai
            logging.getLogger('user').info('player_drop.')
            if tableid-self.tableid in [-1,3]:
                self.zua()
            else:
                self.paipass()
        @registe_msg_handler(self.ro, 'zua_pai')
        def zua_pai(*args):
            tableid,pai=args
            print 'zua_pai->', tableid, pai
            logging.getLogger('user').info('zua_pai.')
            if tableid==self.tableid:
                self.pai=''.join(sorted(self.pai+pai))
                reactor.callLater(3, partial(self.drop))
        @registe_msg_handler(self.ro, 'hu_pai')
        def hu_pai(*args):
            tableid,pai=args
            print 'hu_pai->', tableid, pai
            logging.getLogger('user').info('hu_pai.')
            reactor.callLater(5, partial(self.standby))

    def register(self):
        res=Buffer()
        res.write_ushort(1024)
        res.write_string(self.id)
        res.write_string(self.pwd)
        res.write_string(self.nick)
        res.write_string(self.mail)
        res.write_short(self.sex)
        res.write_short(self.avata)
        print 'register_request:', self.id, self.pwd
        self.ro.sendData(res.getValue())

    def login(self, u, p):
        self.id=u
        res=Buffer()
        res.write_ushort(1025)
        res.write_string(u)
        res.write_string(p)
        print 'login_request:', u, p
        self.ro.sendData(res.getValue())

    def lobby(self):
        res=Buffer()
        res.write_ushort(1030)
        res.write_short(1)
        res.write_short(1)
        self.ro.sendData(res.getValue())

    def joinroom(self,roomid=-1, tableid=3):
        res=Buffer()
        res.write_ushort(1032)
        res.write_short(roomid)
        res.write_byte(tableid)
        res.write_string('')
        self.ro.sendData(res.getValue())

    def standby(self):
        res=Buffer()
        res.write_ushort(1050)
        self.ro.sendData(res.getValue())

    def paipass(self):
        res=Buffer()
        res.write_ushort(1067)
        self.ro.sendData(res.getValue())

    def drop(self):
        res=Buffer()
        res.write_ushort(1058)
        i=random.choice(range(len(self.pai)))
        pai=self.pai[i]
        self.pai=self.pai[:i]+self.pai[i+1:]
        print '======================================================='
        print '->my_pai[%s]: %s' % (self.tableid, self.pai)
        res.write_byte(ord(pai))
        self.ro.sendData(res.getValue())

    def zua(self):
        res=Buffer()
        res.write_ushort(1054)
        self.ro.sendData(res.getValue())

