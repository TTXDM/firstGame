#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/6/26 17:06  
from collections import defaultdict
from functools import partial
from twisted.internet.defer import inlineCallbacks
from twisted.internet import defer
import txredisapi as redis

import weakref, logging
from core.packet import Parser,Buffer
from core.packet import registe_request_handler,registe_msg_handler,unregiste_msg_handler
from core.consts import *
from core.game_logic import *

class BaseObject(object):
    def __init__(self,obj=None):
        if not obj or not self.__slots__: return
        for k in self.__slots__:
            if obj.has_key(k):
                setattr(self,k,obj[k])

class User(BaseObject):
    __slots__=('id','nick','mail','pwd','sex','avata')
    id,nick,mail,pwd,sex,avata='','','','',0,0
    def __repr__(self):
        return '{"id":"%s","nick":"%s","sex":%s,"mail":"%s","pwd":"%s","avata":"%s"}' % \
               (self.id,self.nick,self.sex,self.mail,self.pwd,self.avata)

class Room(BaseObject):
    __slots__=('id','players','pwd','ready')
    id,players,pwd,ready=0,[None,None,None,None],'',[0,0,0,0]
    def __init__(self,obj=None):
        self.ready=[0,0,0,0]
        self.players=[None,None,None,None]
        super(Room,self).__init__(obj)
    # def __repr__(self):
    #     return '{"id":%d,"pwd":"%s","p1":%s,"p2":%s,"p3":%s,"p4":%s}' %\
    #            (self.id,self.pwd,repr(self.players[0]),repr(self.players[1]),repr(self.players[2]),repr(self.players[3]))

connections={}
def User_connected(usr,sock):
    sock.user=usr
    usr.sock=weakref.proxy(sock)
    connections[usr.id]=weakref.proxy(sock)
    @registe_msg_handler(sock,'connectionLost')
    def User_disconnected(*args,**kwargs):
        unregiste_msg_handler(sock,'connectionLost')
        logging.getLogger('user').info('User_disconnected: '+usr.id)

def getUsrBySock(sock):
    return sock.get('user',None)

def getSockByUsrId(usrId):
    try:
        sock = connections.get(usrId,None)
        if sock:
            return sock
        elif connections.has_key(usrId):
            del connections[usrId]
    except ReferenceError,e:
        pass
    return None

page_manager={}
def page_get_users(pageId):
    try:
        users = page_manager.get(str(pageId),None)
        if type(users)==dict:
            return users
        elif page_manager.has_key(str(pageId)):
            del page_manager[str(pageId)]
    except ReferenceError,e:
        pass
    return {}

def page_join_user(ro, pageId):
    if not page_manager.has_key(str(pageId)):
        page_manager[str(pageId)]=dict()
    users = page_manager.get(str(pageId),None)
    if type(users)!=dict:
        page_manager[str(pageId)]=dict()
    users[ro.user.id]=ro
    ro.user.pageId=pageId
    print 'page_join_user:', pageId
    for u in users:
        print u'->', u

def page_remove_user(ro,pageId):
    users = page_manager.get(str(pageId),None)
    if type(users)==dict and users.has_key(ro.user.id):
        del users[ro.user.id]
        print 'page_remove_user:', pageId, ro.user.id
        for u in users:
            print u'->', u

room_manager={}
def room_get_room(roomId):
    try:
        room = room_manager.get(str(roomId),None)
        if room:
            return room
        elif room_manager.has_key(str(roomId)):
            del room_manager[roomId]
    except ReferenceError,e:
        pass
    return None

def room_get_user(room,postion):
    try:
        if room:
            oldUsr=room.players[postion]
            if oldUsr:
                return oldUsr
    except ReferenceError,e:
        pass
    return None

def room_get_users(room):
    arr=[]
    for i in range(4):
        arr.append(room_get_user(room,i))
    return arr

def room_get_user_tableid(room, user):
    for i in range(4):
        usr=room_get_user(room,i)
        if usr and usr.id==user.id:
            return i
    return -1

def room_join_usr(user,roomId,postion):
    room = room_get_room(roomId)
    if not room:
        room = Room({'id':roomId})
        print 'create_room:', roomId, room.id, id(room)
        room_manager[str(roomId)]=weakref.proxy(room)
    else:
        oldUsr = room_get_user(room,postion)
        if oldUsr:
            return None,None,u'座位已占用',0
    user.room=room
    user.tableid=postion
    players=0
    for i in range(4):
        if room.players[i]:
            players=players+1
    print 'room_join_usr:', roomId, room.id, postion, user.id, players
    room.players[postion]=weakref.proxy(user)
    return room,postion,'',players

def room_exit_usr(user,roomId,postion):
    room = room_get_room(roomId)
    if not room: return
    oldUsr = room_get_user(room,postion)
    if not oldUsr: return
    if oldUsr.id==user.id:
        room.players[postion]=None
        del user.room
        del user.tableid

def room_list(pagesize=20):
    ss=[]
    for roomId in range(pagesize):
        room = room_get_room(roomId)
        if room:
            rr=[]
            for player in room_get_users(room):
                if player:
                    rr.append('{"id":"%s","nick":"%s","sex":%s,"avata":%s}'%(player.id,player.nick,player.sex,player.avata))
                else:
                    rr.append("null")
            ss.append('{"id":%s,"p1":%s,"p2":%s,"p3":%s,"p4":%s}' % (room.id, rr[0],rr[1],rr[2],rr[3]) )
        else:
            ss.append('{"id":%d}' % roomId)
    res=','.join(ss)
    res='{"rooms":[%s],"pages":1}' % res
    print 'room_list:\n',res
    return res

@defer.inlineCallbacks
def room_cast_msg(room,data):
    for i in range(4):
        usr=room_get_user(room,i)
        if not usr: continue
        sock=getSockByUsrId(usr.id)
        if not sock:continue
        yield sock.sendData(data)

def room_find_waiting():
    for roomId in room_manager:
        # print 'room_find_waiting:', roomId
        room = room_get_room(roomId)
        if not room: continue
        for i in range(4):
            player=room.players[i]
            # print '>>>>>>>>>>', i,  player
            if not player:
                return roomId,i,''
    for roomId in range(20):
        # print 'room_find_waiting:', roomId
        room = room_get_room(roomId)
        if not room:
            return roomId,0,''
    return None,None,u'自动匹配失败'

@defer.inlineCallbacks
def getUser(uId):
    rc = yield redis.Connection()
    yield rc.select("0")
    usr = yield rc.get("usr_"+uId)
    if usr:
        obj=User(eval(usr))
    else:
        obj=None
    defer.returnValue(obj)

@registe_request_handler(1024)
@defer.inlineCallbacks
def account_create(ro,data):
    '''
    创建用户账号；
    '''
    obj=Parser(data)
    u=obj.read_string()
    p=obj.read_string()
    nick=obj.read_string()
    mail=obj.read_string()
    sex=obj.read_ushort()
    avata=obj.read_ushort()
    print u"account_create:",u,p,mail,sex,avata
    rc = yield redis.Connection()
    print u'redis connected!'
    yield rc.select("0")
    usr = yield rc.get("usr_"+u)
    if usr:
        print u'用户已存在'
        yield rc.disconnect()
        res=Buffer()
        res.write_ushort(1024)
        res.write_short(-100)
        res.write_string(u'用户已存在')
        ro.sendData(res.getValue())
    else:
        m=User()
        m.id,m.pwd,m.nick,m.mail,m.sex,m.avata=u,p,nick,mail,sex,avata
        yield rc.set("usr_"+u, repr(m))
        yield rc.disconnect()
        res=Buffer()
        res.write_ushort(1024)
        res.write_short(1)
        res.write_string(u'ok')
        # dat=res.getValue()
        # for i in range(len(dat)):
        #     print dat[i]
        ro.sendData(res.getValue())
        logging.getLogger('user').info(u'用户账号注册成功:%s<%s>'%(nick,u))

@registe_request_handler(1025)
@defer.inlineCallbacks
def auth_login(ro, data):
    '''
    用户登录
    :param ro:连接
    :param data:客户端数据包
    :return:
    '''
    obj=Parser(data)
    u=obj.read_string()
    p=obj.read_string()
    print u"auth_login:", u, p
    rc = yield redis.Connection()
    yield rc.select("0")
    usr = yield getUser(u)
    if not usr or usr.pwd!=p:
        print u'登录失败',usr, usr or u'无次用户'
        yield rc.disconnect()
        res=Buffer()
        res.write_ushort(1025)
        res.write_short(-100)
        res.write_string(u'登录失败')
        ro.sendData(res.getValue())
    else:
        ro2 = getSockByUsrId(u)
        if ro2:
            res=Buffer()
            res.write_ushort(1025)
            res.write_short(-102)
            res.write_string(u'账号被重新登录')
            ro2.sendData(res.getValue())
            ro2.transport.loseConnection()
        yield rc.sadd('lobby_usr',u)
        yield rc.disconnect()
        res=Buffer()
        res.write_ushort(1025)
        res.write_short(1)
        res.write_ushort(int(usr.avata))
        ro.sendData(res.getValue())
        User_connected(usr, ro)
        logging.getLogger('user').info(u'登录成功:'+u)

@registe_request_handler(1040)
@defer.inlineCallbacks
def lobby_user_chat(ro, data):
    '''
    大厅用户聊天
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    peer=obj.read_string()
    msg=obj.read_string()
    print u"user_chat:", peer, msg
    rc = yield redis.Connection()
    yield rc.select("0")
    me=ro.user
    if not me:
        print u'msg发送失败', u'登录过期'
        yield rc.disconnect()
        res=Buffer()
        res.write_ushort(1040)
        res.write_short(-101)
        res.write_string(u'登录过期')
        ro.sendData(res.getValue())
        return
    if peer=='All':
        res=Buffer()
        res.write_ushort(1040)
        res.write_short(1)
        res.write_string(u'ok')
        ro.sendData(res.getValue())
        mems=yield rc.smembers("lobby_usr")
        for mm in mems:
            ro2 = getSockByUsrId(mm)
            if not ro2: continue
            res=Buffer()
            res.write_ushort(1042)
            res.write_string(me.id)
            res.write_string(me.nick)
            res.write_string(msg)
            ro2.sendData(res.getValue())
        yield rc.disconnect()
        print u'发送成功!'
    else:
        usr = yield getUser(peer)
        if not usr:
            print u'msg发送失败',usr, usr or u'无次用户'
            yield rc.disconnect()
            res=Buffer()
            res.write_ushort(1040)
            res.write_short(-100)
            res.write_string(u'无此用户')
            ro.sendData(res.getValue())
            return
        ro2 = getSockByUsrId(peer)
        if not ro2:
            print u'msg发送失败', u'用户不在线'
            yield rc.disconnect()
            res=Buffer()
            res.write_ushort(1040)
            res.write_short(-101)
            res.write_string(u'用户不在线')
            ro.sendData(res.getValue())
            return
        yield rc.disconnect()
        print u'发送成功!'
        res=Buffer()
        res.write_ushort(1040)
        res.write_short(1)
        res.write_string(u'ok')
        ro.sendData(res.getValue())
        res=Buffer()
        res.write_ushort(1042)
        res.write_string(me.id)
        res.write_string(me.nick)
        res.write_string(msg)
        ro2.sendData(res.getValue())

@registe_request_handler(1030)
@defer.inlineCallbacks
def list_rooms(ro, data):
    '''
    获取大厅房间列表；
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    page=obj.read_short()
    pagesize=obj.read_short()
    print u"list_rooms:", page, pagesize
    jsonStr=room_list()
    pageId=getattr(ro.user,'pageId',None)
    page_remove_user(ro,pageId)
    page_join_user(ro,page)
    res=Buffer()
    res.write_ushort(1030)
    res.write_short(1)
    res.write_string(jsonStr)
    yield ro.sendData(res.getValue())

@registe_request_handler(1032)
@defer.inlineCallbacks
def enter_room(ro, data):
    '''
    加入游戏房间；
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    roomid=str(obj.read_short())
    tableid=obj.read_ubyte()
    pwd=obj.read_string()
    print u"enter_room:", roomid, tableid, pwd
    if roomid=='-1':
        roomid,tableid,msg = room_find_waiting()
        print u'room_find_waiting>>', roomid,tableid,msg
        if msg:
            res=Buffer()
            res.write_ushort(1032)
            res.write_short(-100)
            res.write_string(msg)
            ro.sendData(res.getValue())
            print u'自动匹配失败'
            return
    room,pos,msg,num=room_join_usr(ro.user,roomid,tableid)
    if not room:
        res=Buffer()
        res.write_ushort(1032)
        res.write_short(-100)
        res.write_string(msg)
        ro.sendData(res.getValue())
        return
    res=Buffer()
    res.write_ushort(1032)
    res.write_short(1)
    res.write_ushort(int(roomid))
    res.write_byte(tableid)
    ro.sendData(res.getValue())
    logging.getLogger('user').info(u'房间[%s]座位[%d]玩家<%s>加入ok' % (roomid,tableid,ro.user.id))

    res=Buffer()
    res.write_ushort(1052)
    res.write_string(ro.user.id)
    res.write_string(ro.user.nick)
    res.write_ushort(ro.user.sex)
    res.write_ushort(int(ro.user.avata))
    res.write_byte(tableid)
    res.write_short(int(roomid))
    res.write_byte(num)
    ddat=res.getValue()
    # 广播新玩家加入房间的消息；
    yield room_cast_msg(room,ddat)
    pageId=getattr(ro.user,'pageId',None)
    ss=page_get_users(pageId)
    for kk in ss:
        print '\t->', kk
        yield ss[kk].sendData(ddat)
    page_remove_user(ro,pageId)
    for i in range(4):
        if i==tableid: continue
        user=room_get_user(room,i)
        if not user:   continue
        res=Buffer()
        res.write_ushort(1052)
        res.write_string(user.id)
        res.write_string(user.nick)
        res.write_ushort(user.sex)
        res.write_ushort(int(user.avata))
        res.write_byte(i)
        ro.sendData(res.getValue())

    @registe_msg_handler(ro,'connectionLost')
    @defer.inlineCallbacks
    def User_disconnected(*args,**kwargs):
        if hasattr(ro.user,'room'):
            room=ro.user.room
            logging.getLogger('room').info('room_disconnected: <%s>room[%s]table[%s]'%(ro.user.id,roomid,tableid))
            if hasattr(ro.user.room,'maj'):
                ro.user.room.maj.game_exit(ro,ro.user.tableid)
                res=Buffer()
                res.write_ushort(1099)
                res.write_string('exit')
                yield room_cast_msg(room, res.getValue())
                for i in range(4):
                    user=room_get_user(room, i)
                    if not user: continue
                    if hasattr(user.room,'maj'):
                        del user.room.maj
                room_exit_usr(ro.user,ro.user.room.id,ro.user.tableid)

            res=Buffer()
            res.write_ushort(1053)
            res.write_string(ro.user.id)
            res.write_string(ro.user.nick)
            res.write_byte(tableid)
            res.write_short(int(roomid))
            ddat=res.getValue()
            # yield room_cast_msg(room,res.getValue())
            pageId=getattr(ro.user,'pageId',None)
            ss=page_get_users(pageId)
            for kk in ss:
                print '\t->',ss[kk].user.id
                yield ss[kk].sendData(ddat)
            page_remove_user(ro,pageId)
            # for i in range(4):
            #     user=room_get_user(room, i)
            #     if not user: continue
            #     room_exit_usr(user,user.room.id,user.tableid)

@registe_request_handler(1050)
@defer.inlineCallbacks
def game_init(ro, data):
    '''
    玩家准备好开始游戏；发送 庄家tableid 以及初始发牌；
    :param ro:
    :param data:
    :return:
    '''
    if not hasattr(ro.user,'room'):
        print 'check_ready: state_wrong.', ro.user.room, ro.user.tableid
        return
    print u'game_init:', ro.user.room.id, ro.user.tableid
    all_ready=True
    ro.user.ready=True
    for i in range(4):
        user=room_get_user(ro.user.room, i)
        if not user:
            all_ready=False
            continue
        if not hasattr(user,'ready') or not user.ready:
            all_ready=False
        elif i!=ro.user.tableid:
            res=Buffer()
            res.write_ushort(1050)
            res.write_byte(i)
            yield ro.sendData(res.getValue())
    res=Buffer()
    res.write_ushort(1050)
    res.write_byte(ro.user.tableid)
    yield room_cast_msg(ro.user.room, res.getValue())
    if not all_ready:
        return
    logging.getLogger('game').info(u'游戏开始: check_all_ready.')
    ro.user.room.maj=Pai()
    ro.user.room.maj.init_game(room=ro.user.room,debug=False)

    rnd_saizi=[random.choice(range(1,7)) for i in range(6)]

    #精牌：正精/副精；上精/下精
    jin_arr=ro.user.room.maj.game_jin((rnd_saizi[-1]+rnd_saizi[-2])*2)

    for i in range(4):
        user=room_get_user(ro.user.room, i)
        pai=user.room.maj.pais[user.tableid]
        res=Buffer()
        res.write_ushort(1051)
        res.write_byte(ro.user.room.maj.zuang)
        res.write_string(pai)

        for i in range(6):
            res.write_byte(rnd_saizi[i])
        res.write_byte(ord(ro.user.room.maj.jin1))
        res.write_byte(ord(ro.user.room.maj.jin2))

        for i in range(len(jin_arr)):
            res.write_string(str(jin_arr[i]))
        #for i in range(len(jin_arr)):
        #    res.write_byte(ro.user.room.maj.ct[i])

        sock=getSockByUsrId(user.id)
        if sock: yield sock.sendData(res.getValue())

def check_room_state(ro):
    if not hasattr(ro.user,'room'):
        print 'check_ready: state_wrong.room not exist.', ro.user.room, ro.user.tableid, ro.user.id
        return False
    if not hasattr(ro.user.room,'maj'):
        print 'check_ready: state_wrong.game not init.', ro.user.room, ro.user.tableid, ro.user.id
        return False
    return True

@registe_request_handler(1099)
@defer.inlineCallbacks
def game_exit(ro, data):
    '''
    游戏结束；
    :param ro:
    :param data:
    :return:
    '''
    print u"game_exit:", ro.user.tableid
    if not check_room_state(ro):
        print 'game_exit error.'
        return
    ro.user.room.maj.game_exit(ro, ro.user.tableid)
    del ro.user.room.maj.room
    del ro.user.room.maj
    logging.getLogger('game').info(u'游戏结束: %s'%(ro.user.id))
    res=Buffer()
    res.write_ushort(1099)
    res.write_string('exit')
    yield room_cast_msg(ro.user.room, res.getValue())

##################################################################################
@registe_request_handler(1058)
@defer.inlineCallbacks
def game_drop_one(ro, data):
    '''
    出牌；
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    pai=chr(obj.read_ubyte())
    print u"game_drop_one:", PAI_NAME(pai), ro.user.id, ro.user.tableid
    if not check_room_state(ro): return
    ff=ro.user.room.maj.drop_one(ro.user.tableid, pai)
    if ff:
        logging.getLogger('game').info(u'%s出牌OK:[%s]'%(ro.user.id, pai))
        res=Buffer()
        res.write_ushort(1059)
        res.write_byte(ro.user.tableid)
        res.write_byte(ord(pai))
        res.write_byte(0)
        yield room_cast_msg(ro.user.room, res.getValue())
        # '''
        #     update all players state
        # '''
        #print 'game_drop_one ok.'
    else:
        print 'game_drop_one 出牌ERR.', ro.user.id
        res=Buffer()
        res.write_ushort(1058)
        res.write_short(-1)
        yield ro.sendData(res.getValue())

def zhua_pai_ok(result):
    ro, pai=result
    logging.getLogger('game').info(u'抓牌OK:%s[%s]'%(ro.user.id, pai))
    res=Buffer()
    res.write_ushort(1054)
    res.write_byte(ord(pai))
    res.write_byte(ro.user.tableid)
    # ro.sendData(res.getValue())
    room_cast_msg(ro.user.room,res.getValue())

def zhua_pai_err(*args):
    print 'zhua_pai_err.'

@registe_request_handler(1054)
@defer.inlineCallbacks
def game_zhua_pai(ro, data):
    '''
    抓牌
    :param ro:
    :param data:
    :return:
    '''
    print u"game_zhua_pai."
    if not check_room_state(ro):return
    print u"%s玩家[%s]抓牌" % (ro.user.id,ro.user.tableid)
    d=defer.maybeDeferred(partial(ro.user.room.maj.get_one), ro, ro.user.tableid)
    if d:
        d.addCallback(zhua_pai_ok)
        d.addErrback(zhua_pai_err)
    yield

def chipai_ok(result):
    try:
        ro,p1,p2,p3=result
        print 'chipai_ok.', ro.user.id, p1, p2, p3
        logging.getLogger('game').info(u'吃牌OK:%s[%s]'%(ro.user.id, [p1,p2,p3]))
        res=Buffer()
        res.write_ushort(1063)
        res.write_byte(ro.user.tableid)
        res.write_byte(ord(p1))
        res.write_byte(ord(p2))
        res.write_byte(ord(p3))
        room_cast_msg(ro.user.room,res.getValue())
    except:
        print 'chipai_ok_but_err.'

def chipai_err(*args):
    print '---------------chipai_err'

@registe_request_handler(1055)
@defer.inlineCallbacks
def game_chi_pai(ro, data):
    '''
    吃牌
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    p1=chr(obj.read_ubyte())
    p2=chr(obj.read_ubyte())
    p3=chr(obj.read_ubyte())
    print u"game_chi_pai: p1,p2,p3 = ", PAI_NAME(p1), PAI_NAME(p2), PAI_NAME(p3)
    if not check_room_state(ro): return
    logging.getLogger('game').info(u'玩家吃牌:%s[%s]'%(ro.user.id,[PAI_NAME(p1), PAI_NAME(p2), PAI_NAME(p3)]))
    # 方法一：在game_logic里面异步执行以回调方式接受后续数据包发送的逻辑（chipai_ok里面）;
    # ro.user.room.maj.chi_pai(ro, ro.user.tableid, p1, p2, p3)#
    # 方法二：异步Deferred回调机制执行后续逻辑;
    d=defer.maybeDeferred(partial(ro.user.room.maj.chi_pai),ro, ro.user.tableid, p1, p2, p3)
    if d:
        d.addCallback(chipai_ok)
        d.addErrback(chipai_err)
    yield


################################################################################
@registe_request_handler(1056)
@defer.inlineCallbacks
def game_peng_pai(ro, data):
    '''
    碰牌
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    pai=chr(obj.read_ubyte())
    print u"game_peng_pai:", PAI_NAME(pai)
    if not check_room_state(ro):return
    def peng_pai_ok(result):
        logging.getLogger('game').info(u'碰牌:%s[%s]'%(ro.user.id, PAI_NAME(pai)))
        res=Buffer()
        res.write_ushort(1064)
        res.write_byte(ro.user.tableid)
        res.write_byte(ord(pai))
        room_cast_msg(ro.user.room, res.getValue())

    def peng_pai_err(*args):
        print 'peng_pai_err'

    d=defer.maybeDeferred(partial(ro.user.room.maj.peng_pai),ro,ro.user.tableid, pai)
    if d:
        d.addCallback(peng_pai_ok)
        d.addErrback(peng_pai_err)
    yield

@registe_request_handler(1057)
@defer.inlineCallbacks
def game_gang_pai(ro, data):
    '''
    杠牌
    :param ro:
    :param data:
    :return:
    '''
    def gang_pai_ok(result):
        print 'gang_pai_ok'
        logging.getLogger('game').info(u'杠牌OK:%s[%s]'%(ro.user.id, PAI_NAME(pai)))
        res=Buffer()
        res.write_ushort(1065)
        res.write_byte(ro.user.tableid)
        res.write_byte(ord(pai))
        room_cast_msg(ro.user.room, res.getValue())

    def gang_pai_err(*args):
        print 'gang_pai_err'
        # logging.getLogger('game').info(u'杠牌ERR:%s[%s]'%(ro.user.id, pai))

    obj=Parser(data)
    pai=chr(obj.read_ubyte())
    print u"game_gang_pai:", PAI_NAME(pai)
    if not check_room_state(ro):return
    logging.getLogger('game').info(u'杠牌:%s[%s]'%(ro.user.id, PAI_NAME(pai)))
    d=defer.maybeDeferred(partial(ro.user.room.maj.gang_pai),ro,ro.user.tableid, pai)
    if d:
        print 'game_gang_pai 000', d
        d.addCallback(gang_pai_ok)
        print 'game_gang_pai 111'
        d.addErrback(gang_pai_err)
    yield
    print 'game_gang_pai 222'

def hupai_ok(result):
    print 'hupai_ok',result
    ro,str1,pai,int1,int2,int3,int4,flag = result
    logging.getLogger('game').info(u'胡牌:%s\n\t%s'%(ro.user.id, result))
    for i in range(4):
        usr=room_get_user(ro.user.room,i)
        usr.ready=False
    res=Buffer()
    res.write_ushort(1089)
    res.write_byte(ro.user.tableid)
    res.write_string(str1)
    res.write_byte(ord(pai))
    res.write_short(int1)
    res.write_short(int2)
    res.write_short(int3)
    res.write_short(int4)
    res.write_string(flag)
    room_cast_msg(ro.user.room, res.getValue())

def hupai_err(result):
    print 'hupai_err.'
    print result
    import sys
    print >>sys.stderr
    ro=result.value
    res=Buffer()
    res.write_ushort(1088)
    res.write_short(-1)
    ro.sendData(res.getValue())

@registe_request_handler(1088)
@defer.inlineCallbacks
def game_hu_pai(ro, data):
    '''
    胡牌
    :param ro:
    :param data:
    胡牌的type，  1表示德国， 2表示正常胡牌， 3表示七对，  4表示十三烂，5表示七星十三烂
    德国就是没用精牌就胡了；德中德就是胡牌的时候，四个人手里都没有精牌；
    13烂就是没对子，没顺子，没刻子
    13烂，如果有东南西北中发白七张，就是七星十三烂
    :return:
    '''
    obj=Parser(data)
    type=obj.read_ubyte()
    str1=obj.read_string()
    tt=str1.split(',')
    print u"game_hu_pai:", ro.user.id, type, str1
    print u"game_hu_pai:", tt
    print u"game_hu_pai:", '\t'.join([''.join(map(PAI_NAME,m)) for m in tt])
    if not check_room_state(ro):return
    d=defer.maybeDeferred(partial(ro.user.room.maj.hu_pai),ro,ro.user.tableid, type, str1)
    if d:
        d.addCallback(hupai_ok)
        d.addErrback(hupai_err)
    yield


@registe_request_handler(1067)
@defer.inlineCallbacks
def game_pai_pass(ro, data):
    '''
    pass牌
    :param ro:
    :param data:
    :return:
    '''
    print u"game_pai_pass.", ro.user.id
    if not check_room_state(ro):return
    ro.user.room.maj.pass_pai(ro.user.tableid)
    res=Buffer()
    res.write_ushort(1068)
    res.write_byte(ro.user.tableid)
    yield room_cast_msg(ro.user.room, res.getValue())


@registe_request_handler(1101)
@defer.inlineCallbacks
def game_saizi_1(ro, data):
    '''
    1-庄家摇骰子1
    :param ro:
    :param data:
    :return:
    '''
    print u"game_saizi_1.", ro.user.id
    if not check_room_state(ro):return
    res=Buffer()
    res.write_ushort(1101)
    res.write_byte(ro.user.tableid)
    res.write_byte(random.choice(range(1,7)))
    res.write_byte(random.choice(range(1,7)))
    yield room_cast_msg(ro.user.room, res.getValue())

@registe_request_handler(1102)
@defer.inlineCallbacks
def game_saizi_2(ro, data):
    '''
    2-玩家摇骰子2
    :param ro:
    :param data:
    :return:
    '''
    print u"game_saizi_2.", ro.user.id
    if not check_room_state(ro):return
    res=Buffer()
    res.write_ushort(1102)
    res.write_byte(ro.user.tableid)
    res.write_byte(random.choice(range(1,7)))
    res.write_byte(random.choice(range(1,7)))
    yield room_cast_msg(ro.user.room, res.getValue())


@registe_request_handler(1103)
@defer.inlineCallbacks
def game_saizi_3(ro, data):
    '''
    3-玩家摇骰子3
    :param ro:
    :param data:
    :return:
    '''
    print u"game_saizi_3.", ro.user.id
    if not check_room_state(ro):return
    res=Buffer()
    res.write_ushort(1103)
    res.write_byte(ro.user.tableid)
    res.write_byte(random.choice(range(1,7)))
    res.write_byte(random.choice(range(1,7)))
    yield room_cast_msg(ro.user.room, res.getValue())


@registe_request_handler(1104)
@defer.inlineCallbacks
def game_ting(ro, data):
    '''
    听牌
    :param ro:
    :param data:
    :return:
    '''
    obj=Parser(data)
    ss=obj.read_string()
    print u"game_ting.", ro.user.id, ss
    if not check_room_state(ro):return
    ro.user.room.maj.ting_pai(ro.user.tableid,ss)
    yield