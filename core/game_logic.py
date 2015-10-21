#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/6/19 14:32  
import re
import sys
import random
import logging
from pickle import NONE
from functools import partial
from collections import Counter
from itertools import combinations,chain,product
from twisted.internet import reactor,defer
from twisted.internet.error import AlreadyCalled,AlreadyCancelled

from core.consts import *

DEBUG=True

#风牌-箭牌-字牌[万条筒]
_wan = list(PAI_WAN)#万牌的集合;
_tiao = list(PAI_TIAO)#条子的集合;
_tong = list(PAI_TONG)#筒子的集合;
_feng = list(PAI_FENG+PAI_JIAN)#风牌【东>南v西<北^】和箭牌【发财$红中+白板o】的集合;
_allPai = (_wan + _tiao + _tong + _feng) * 4

#opt_zua 抓牌; opt_cup 出牌; opt_chi 吃牌; opt_peng 碰牌; opt_gang 杠牌;opt_agng 暗杠; opt_hdn 补牌; opt_hu 胡牌
opt_zua, opt_cup, opt_chi, opt_peng, opt_gang, opt_agng, opt_bu, opt_hu=101,102,103,104,105,106,107,108

class Opt_info():
    def __init__(self, tableid=-1, opt=None, defered_call=None):
        self.tableid=tableid
        self.opt=opt
        self.defered_call=defered_call
        self.pai=''
    def __eq__(self, other):
        return self.tableid==other.tableid and self.opt==other.opt

class Pai():
    def init_game(self, room=None, debug=False):
        '''
            麻将游戏开始：  初始化状态； 发牌；
        '''
        self.left=_allPai[:]            #牌桌上未摸的牌
        random.shuffle(self.left)       #洗牌
        _pai = self.left[:13 + 13 + 13 + 13 + 1]    #随机发牌
        self.left=self.left[len(_pai):]
        self.pais=[]    #各玩家手上的牌[以字符串表示]
        self.lizhi=[None, None, None, None]     #各玩家吃碰杠的牌
        for i in range(4):
            self.lizhi[i]=[]
            self.pais.append(''.join(sorted(list(_pai[:13]))))
            _pai=_pai[13:]
        self.turn=0
        self.room=room
        self.lastOpt=None       #记录上一步操作
        self.drops=[]
        self.wait_opt=None
        self.ting=['','','','']
        self.zuang=random.choice(range(4)) #庄家[座位号]
        if DEBUG: self.zuang=3
        print u'->随机发牌：庄:', self.zuang, debug and u'调试' or ''
        self.pais[self.zuang]=''.join(sorted(list(self.pais[self.zuang]+_pai[0])))

        if DEBUG:
            self.pais[0]='rrr678zybbbCs'
            self.pais[1]='aaab88cccddde'
            self.pais[2]='AAA77BCCCDDD1'
            self.pais[3]='FFF66xyyyzzz41'
            self.left=list('678678678678')+self.left

        print u'\t->1：', self.pais[0], len(self.pais[0])
        print u'\t->2：', self.pais[1], len(self.pais[1])
        print u'\t->3：', self.pais[2], len(self.pais[2])
        print u'\t->4：', self.pais[3], len(self.pais[3])

    def game_jin(self, saizi=1):
        '''
            精牌：正精/副精<上精/下精>
                    @param  saizi   第三次摇骰子的点数和乘以2，倒数saizi的牌即为正精；
                                    下面那张为副精，副精字的下一个为下精(如副精上精为一万下精即为2万)
        '''
        self.ting=['','','','']
        self.turn=self.zuang            #当前轮到抓牌的玩家[座位号]
        self.jin1=self.left[-saizi]     #正精
        self.jin2=self.left[-saizi-1]   #副精<上精>
        # 副精<下精>。。。。。。。。。。。。。。。。。。。。。。。。。。！！！！！！！！！！！！！！！！！

        self.jin3 = self.get_jin(self.jin2)
        self.jin4 = self.get_jin(self.jin1)

        if DEBUG:
            self.jin1='s'
            self.jin2='A'
            self.jin3='B'
            self.jin4='t'

        print u'上精:', PAI_NAME(self.jin1)
        print u'下精:', PAI_NAME(self.jin2)
        print u'副精:', PAI_NAME(self.jin3)
        print u'癞子:', PAI_NAME(self.jin4), PAI_NAME(self.jin1)


        self.c1=[0,0,0,0]   #下精个数；
        self.c2=[0,0,0,0]   #副精个数；
        jins=['','','',''] #玩家副精分布；
        self.ct=[0,0,0,0]  #精分计算；
        for i in range(4):
            self.c1[i]=str(self.pais[i]).count(self.jin2)
            self.c2[i]=str(self.pais[i]).count(self.jin3)
            self.ct[i]=self.c1[i]*2+self.c2[i]
            jins[i]=self.c2[i]*self.jin3
            print u'精《冲关》', i, jins[i], self.c1[i],  self.c2[i], self.ct[i]
        tt=self.ct[0]+self.ct[1]+self.ct[2]+self.ct[3]
        for i in range(4):
            self.ct[i]=2*(self.ct[i]*3-tt)
        return jins

    def game_exit(self, ro, tableid):
        print u'关闭游戏:', tableid
        ro.user.ready=False
        if hasattr(self,'delay_15s') and not self.delay_15s.called and not self.delay_15s.cancelled:
            self.delay_15s.cancel()
            self.delay_15s=None
        if hasattr(self,'opt_wait') and self.opt_wait and len(self.opt_wait)>0:
            self.opt_wait=[]

    def opt_deal_by_prior(self):
        print u'\n@@@@@@@@@@<处理缓存队列：按优先级高低>@@@@@@@@@@@'
        if self.opt_wait and len(self.opt_wait)>0:
            self.opt_wait.sort(key=lambda a:a.opt)
            self.opt_wait.pop().defered_call()
            self.opt_wait=None
            self.wait_opt=None

    def turn_next(self, tableid):
        self.turn=tableid<3 and tableid+1 or 0
        self.turn2=self.get_next(self.turn)
        self.turn3=self.get_next(self.turn2)
        return self.turn

    def get_next(self, tableid):
        pp=tableid<3 and tableid+1 or 0
        return pp

    def turn_step(self, tableid):
        if tableid>=self.turn:
            return tableid-self.turn
        else:
            return tableid-self.turn+4

    def get_jin(self,pai):
        if pai in _wan:
            return (_wan*2)[_wan.index(pai)+1]
        elif pai in _tiao:
            return (_tiao*2)[_tiao.index(pai)+1]
        elif pai in _tong:
            return (_tong*2)[_tong.index(pai)+1]
        elif pai in list(PAI_FENG):
            return (list(PAI_FENG)*2)[list(PAI_FENG).index(pai)+1]
        elif pai in list(PAI_JIAN):
            return (list(PAI_JIAN)*2)[list(PAI_JIAN).index(pai)+1]
#####################################################################################################################
#################################             出牌                   #################################################
#####################################################################################################################
    def drop_one(self,tableid, _pai):
        if self.turn!=tableid:
            print u'\t规则限制:没轮到自己出牌', self.turn
            return False
        if self.lastOpt and self.lastOpt.tableid!=tableid:
            print u'\t规则限制:不能直接出牌（除非是第一轮）。', self.turn, tableid, self.lastOpt.tableid,self.lastOpt.opt
            return False
        if not _pai in self.pais[tableid]:
            print u'\t规则限制:不能出这张自己没有的牌。'
            return False
        pp=list(self.pais[tableid])
        pp.remove(_pai)
        self.drops.append(_pai)
        self.pais[tableid]=''.join(pp)
        self.lastOpt=Opt_info(tableid,opt_cup)
        self.lastOpt.pai=_pai
        self.opt_wait=[]
        self.wait_opt=[0,0,0,0]
        logging.getLogger('game').info(u'出牌[%s]%s: %s'%(tableid, PAI_NAME(_pai), self.pais[tableid]))
        self.delay_15s=reactor.callLater(15, partial(self.opt_deal_by_prior))
        pos1=self.turn_next(tableid)
        pos2,pos3=self.turn2,self.turn3
        pai1=''.join(sorted(list(self.pais[pos1])))
        pai2=''.join(sorted(list(self.pais[pos2])))
        pai3=''.join(sorted(list(self.pais[pos3])))
        # print pos1,pai1
        # print pos2,pai2
        # print pos3,pai3
        print 'pos:', pos1,pos2,pos3
        if _pai*2 in pai3:
            print u'\t->@下家3可碰/杠。'
            self.wait_opt[pos3]=opt_peng
        if _pai*2 in pai2:
            print u'\t->@下家2可碰/杠。'
            self.wait_opt[pos2]=opt_peng
        if _pai*2 in pai1:
            print u'\t->@下家1可碰/杠。'
            self.wait_opt[pos1]=opt_peng
        else:
            if _pai in PAI_FENG:
                p1=list(PAI_FENG)
                p1.remove(_pai)
                nn=Counter(pai1)
                if Counter([nn[i]for i in p1])[0]<2:
                    print u'\t->@下家1可吃。风牌。'
                    self.wait_opt[pos1]=opt_chi
            else:
                chk=chr(ord(_pai)-2)in pai1 and chr(ord(_pai)-1)in pai1
                chk=chk or chr(ord(_pai)-1)in pai1 and chr(ord(_pai)+1)in pai1
                chk=chk or chr(ord(_pai)+1)in pai1 and chr(ord(_pai)+2)in pai1
                if chk:
                    print u'\t->@下家1可吃。'
                    self.wait_opt[pos1]=opt_chi

        for i in range(4):
            print '\t->',i,':', self.pais[i], self.wait_opt[i], self.ting[i]
            if _pai in self.ting[i]:
                print u'\t->@玩家%s可胡。'%i
                self.wait_opt[i]=opt_hu

        from login.user_manager import room_get_user, getSockByUsrId,zhua_pai_ok,zhua_pai_err
        usr=room_get_user(self.room, self.turn)
        if usr:
            ro=getSockByUsrId(usr.id)
            self.d_zua=defer.Deferred()
            self.opt_wait.append(Opt_info(self.turn, opt_zua, partial(self._get_one, ro=ro, tableid=self.turn)))
            self.d_zua.addCallback(zhua_pai_ok)
            self.d_zua.addErrback(zhua_pai_err)
            logging.getLogger('game').info(u'\t->插入下家%s超时自动抓牌操作.'%ro.user.id)

        if self.wait_opt[pos1]==0 and self.wait_opt[pos2]==0 and self.wait_opt[pos3]==0:
            print u'\t->没有任何吃碰杠胡，立即自动抓牌.'
            self.delay_15s.reset(0)
        return True

#####################################################################################################################
#################################             抓牌                   #################################################
#####################################################################################################################
    def _get_one(self, ro, tableid):
        if len(self.left)<1:
            print u'流局。', self.turn
            if self.d_zua:
                self.d_zua.errback()
            else:
                return None
        _pai = self.left[0]
        self.left.remove(_pai)
        self.pais[tableid]=''.join(sorted(list(self.pais[tableid]+_pai)))
        print u'->抓牌[%s]:<%s> %s'%(ro.user.id, PAI_NAME(_pai), self.pais[tableid])
        self.lastOpt=Opt_info(tableid,opt_zua)
        self.lastOpt.pai=_pai
        self.ting[tableid]=''
        if self.d_zua:
            self.d_zua.callback((ro,_pai))
        else:
            print '_get_one.2', self.d_zua.called and 'called.'  or ''
        return _pai

    def get_one(self,ro,tableid):
        if self.turn!=tableid:
            print u'\t规则限制:', self.turn
            return defer.fail()
        if self.lastOpt==Opt_info(tableid,opt_zua):
            print u'\t规则限制:重复抓。', self.turn
            return defer.fail()
        elif self.lastOpt==Opt_info(tableid,opt_chi):
            print u'\t规则限制:吃牌以后不能抓。', self.turn
            return defer.fail()
        elif self.lastOpt==Opt_info(tableid,opt_peng):
            print u'\t规则限制:碰牌以后不能抓。', self.turn
            return defer.fail()
        elif self.lastOpt==Opt_info(tableid,opt_gang):
            print u'->杠以后抓牌.'   #杠以后抓牌
            _pai=self._get_one(ro,tableid)
            return defer.succeed((ro,_pai))
        else:
            print 'get_one 3'
            self.d_zua=defer.Deferred()
            self.wait_opt[tableid]=0
            self.opt_wait.append(Opt_info(tableid, opt_zua, partial(self._get_one, ro=ro, tableid=tableid)))
            if self.wait_opt[(tableid+1)%4]==0 and self.wait_opt[(tableid+2)%4]==0:
                print u'\t->没有下家碰杠胡，立即抓牌.'
                self.delay_15s.reset(0)
            return self.d_zua

#####################################################################################################################
#################################             吃牌                   #################################################
#####################################################################################################################
    def _chi_pai(self, ro, tableid, p1, p2, p3):
        logging.getLogger('game').info(u'执行吃牌[%s]%s: %s'%(tableid, [p1,p2,p3], self.pais[tableid]))
        pp=list(self.pais[tableid])
        if p2 in pp: pp.remove(p2)
        if p3 in pp: pp.remove(p3)
        self.pais[tableid]=''.join(pp)
        if not list(self.lizhi[tableid]): self.lizhi[tableid]=[]
        self.lizhi[tableid].append(p1+p2+p3)
        self.lastOpt=Opt_info(tableid,opt_chi)
        print u'->吃[%d]:'%tableid, ro.user.id, PAI_NAME(p1), self.pais[tableid]
        self.d_chi.callback((ro,p1,p2,p3))
        # from login.user_manager import chipai_ok
        # chipai_ok(ro,p1,p2,p3)

    def chi_pai(self, ro, tableid, p1, p2, p3):
        if self.turn!=tableid:
            print u'\t规则限制:', self.turn
            return defer.fail()
        if not self.opt_wait:
            print u'\t规则限制：已经超时。', self.turn
            return defer.fail()
        if p1!=self.lastOpt.pai:
            print u'\t参数传递错误：吃牌必须是上家刚出的牌。', self.turn
            return defer.fail()
        if p2 not in self.pais[tableid] or p3 not in self.pais[tableid]:
            print u'\t参数传递错误：玩家手中没有合适吃牌的。', self.turn, p2, p3
            return defer.fail()
        if abs(ord(p1)-ord(p2))*abs(ord(p2)-ord(p3))*abs(ord(p3)-ord(p1))==2 or \
                p1 in PAI_FENG and p2 in PAI_FENG and p3 in PAI_FENG and p1!=p2 and p2!=p3:
            self.d_chi=defer.Deferred()
            self.opt_wait.append(Opt_info(tableid,opt_chi,partial(self._chi_pai, ro=ro, tableid=tableid, p1=p1, p2=p2, p3=p3)))
            self.wait_opt[tableid]=-opt_chi
            if self.wait_opt[(tableid+1)%4]<1 and self.wait_opt[(tableid+2)%4]<1:
                print u'\t->没有下家碰杠胡（或者已经pass），立即吃牌.'
                self.delay_15s.reset(0)
            return self.d_chi
        return defer.fail()

#####################################################################################################################
#################################             碰牌                   #################################################
#####################################################################################################################
    def peng_pai(self, ro, tableid, _pai):
        print 'peng_pai:', ord(_pai)
        if ord(_pai)==0:
            _pai=self.lastOpt.pai  #测试

        def _peng_pai(tableid, _pai):
            pp=list(self.pais[tableid])
            pp.remove(_pai)
            pp.remove(_pai)
            self.pais[tableid]=''.join(pp)
            if not list(self.lizhi[tableid]): self.lizhi[tableid]=[]
            self.lizhi[tableid].append(_pai*3)
            self.turn=tableid
            self.lastOpt=Opt_info(tableid, opt_peng)
            print u'->碰[%d]:'%tableid, PAI_NAME(_pai), self.pais[tableid]
            self.d_peng.callback(True)
        if not self.opt_wait:
            print u'\t规则限制：已经超时。', self.turn
            return defer.fail()
        print u'peng_pai:', ro.user.id, _pai, self.pais[tableid]
        if _pai*2 in self.pais[tableid]:
            self.d_peng=defer.Deferred()
            self.opt_wait.append(Opt_info(tableid,opt_peng,partial(_peng_pai, tableid, _pai)))
            self.wait_opt[tableid]=-opt_peng
            pos1,pos2,pos3=self.turn,self.turn2,self.turn3
            if self.wait_opt[pos1]<opt_hu and self.wait_opt[pos2]<opt_hu and self.wait_opt[pos3]<opt_hu:
                print u'\t->没有玩家胡牌（或者已经pass），立即碰牌.'
                if not self.delay_15s.called:
                    self.delay_15s.reset(0.5)
            else:
                self.pass_pai(tableid)
            return self.d_peng
        return defer.fail()

    def gang_pai(self, ro, tableid, _pai):
        print 'gang_pai:', ord(_pai)
        if ord(_pai)==0:
            _pai=self.lastOpt.pai  #测试

        def _gang_pai(tableid, _pai):
            pp=list(self.pais[tableid])
            pp.remove(_pai)
            pp.remove(_pai)
            pp.remove(_pai)
            self.pais[tableid]=''.join(pp)
            if not list(self.lizhi[tableid]): self.lizhi[tableid]=[]
            self.lizhi[tableid].append(_pai*4)
            self.turn=tableid
            self.lastOpt=Opt_info(tableid, opt_gang)
            print u'->杠[%d]:'%tableid, PAI_NAME(_pai), self.pais[tableid]
            self.d_gang.callback(True)
            print u'杠牌以后自动补牌。'
            self.get_one(ro,tableid)

        if not self.opt_wait:
            print u'\t规则限制：已经超时。', self.turn
            return defer.fail()

        if _pai*3 in self.pais[tableid]:
            self.d_gang=defer.Deferred()
            self.opt_wait.append(Opt_info(tableid,opt_gang, partial(_gang_pai, tableid, _pai)))
            self.wait_opt[tableid]=-opt_gang
            pos1,pos2,pos3=self.turn,self.turn2,self.turn3
            if self.wait_opt[pos1]<opt_hu and self.wait_opt[pos2]<opt_hu and self.wait_opt[pos3]<opt_hu:
                print u'\t->没有玩家胡牌（或者已经pass），立即碰牌.'
                if not self.delay_15s.called:
                    self.delay_15s.reset(0.5)
            else:
                self.pass_pai(tableid)
            return self.d_gang
        return defer.fail()

    def angang_pai(self, tableid, _pai):
        # if self.turn!=tableid:
        #     print u'\t规则限制:', self.turn
        #     return defer.fail()
        # if _pai in re.compile(r'(\w)\1{3}').findall(self.pais[tableid]):
        #     pp=list(self.pais[tableid])
        #     pp.remove(_pai)
        #     pp.remove(_pai)
        #     pp.remove(_pai)
        #     pp.remove(_pai)
        #     self.pais[tableid]=''.join(pp)
        #     if not list(self.lizhi[tableid]): self.lizhi[tableid]=[]
        #     self.lizhi[tableid].append(_pai*4)
        #     self.lastOpt=Opt_info(tableid, opt_agng)
        #     print u'->暗杠[%d]:'%tableid, _pai, self.pais[tableid]
        #     return True
        return defer.fail()

    def pass_pai(self,tableid):
        '''
        wait_opt    等待玩家操作数组；
          0:        表示没有需要其他玩家等待的操作；
          opt_chi:  表示等待玩家吃牌；
          opt_peng:  表示等待玩家碰牌；
          opt_gang:  表示等待玩家杠牌；
          opt_hu:   表示等待玩家胡牌；
          玩家pass以后将值设为负值；
        '''
        if not self.wait_opt:
            print u'\t->忽略：当前未进入玩家操作冲突时段。'
            return False
        self.wait_opt[tableid]=-abs(self.wait_opt[tableid])
        pos1,pos2,pos3=self.turn,self.turn2,self.turn3
        if self.wait_opt[pos1]<1 and self.wait_opt[pos2]<1 and self.wait_opt[pos3]<1:
            if not self.delay_15s.called:
                self.delay_15s.reset(0.5)
                return True

    def hu_pai(self, ro, tableid, type, str1):
        '''
        :param tableid:
        :param drop:
        :return:
        胡牌的type，
            1表示德国，2表示正常胡牌，3表示七对，4表示十三烂，5表示七星十三烂
            德国就是没用精牌就胡了；德中德就是胡牌的时候，四个人手里都没有精牌；
            13烂就是没对子，没顺子，没刻子
            13烂，如果有东南西北中发白七张，就是七星十三烂
        '''
        # if not self.opt_wait:
        #     print u'\t规则限制：已经超时。', self.turn
        print u'hu_Pai:', tableid, type, str1
        print u'hu_Pai_lastOpt_tableid:', self.lastOpt.tableid
        print u'hu_Pai_lastOpt_opt:', self.lastOpt.opt
        # 7：七对
        # B：十三烂
        # E：七星十三烂
        # z：庄家x
        # t：天胡*
        # m：自摸*x
        # j：精吊
        # f：地胡*
        # 0~3：点炮玩家座位号*
        # d：德国
        # D：德中德

        #客户端显示：天胡，地胡，自摸，点炮
        rate=0
        base=1
        score=[0,0,0,0]
        pai=self.lastOpt.pai
        if self.lastOpt.tableid==tableid and self.lastOpt.opt==opt_zua:
            pai_0=sorted(self.pais[tableid]+''.join(self.lizhi[tableid]))
        else:
            pai_0=sorted(self.pais[tableid]+pai+''.join(self.lizhi[tableid]))
        if pai_0!=sorted(str1.replace(',','')):
            print u'\t->客户端服务端牌面不一致。', pai_0, str1, sorted(str1.replace(',',''))
            return defer.fail(ro)

        flag=''
        if self.lastOpt.tableid==tableid and self.lastOpt.opt==opt_zua:
            print u'->自摸。'
            flag+='m'
        else:
            print u'->玩家[%s]点炮。' % self.lastOpt.tableid
            flag+=str(self.lastOpt.tableid)
        if self.zuang==tableid:
            print u'->庄家胡牌。'
            flag+='z'
            if self.drops==[]:
                print u'->天胡。'
                flag=flag.replace('m','')
                flag+='t'
        elif len(self.drops)==1:
            print u'->地胡。'
            flag=flag.replace(str(self.lastOpt.tableid),'')
            flag+='f'

        _pai=''.join(pai_0)
        self.jins=set(self.jin1+self.jin4)
        if type==3:
            ff=self.test_qidui(_pai)
            if ff=='d':
                if self.test_dezhongde(tableid):
                    print u'七对/德中德'
                    flag+='7D'
                else:
                    print u'七对/德国'
                    flag+='7d'
            elif ff=='7':
                print u'七对'
                flag+='7'
            else:
                print u'七对验证不通过。', pai_0
                return defer.fail(ro)

        elif type==4 and str1.find(',')<0:
            xx=self.test_13lan(_pai)
            if xx==5:
                print u'七星十三烂'
                flag+='E'
            elif xx==4:
                print u'十三烂'
                flag+='B'
            else:
                print u'十三烂验证不通过。', pai_0
                return defer.fail(ro)
        elif type==1 or type==2:
            zz=self.test_putong_hu(str1)
            if zz=='d':
                if self.test_dezhongde(tableid):
                    print u'普通胡/德中德'
                    flag+='D'
                else:
                    print u'普通胡/德国'
                    flag+='d'
            elif zz:
                print u'普通胡'
            else:
                return defer.fail(ro)

        if flag.find('z')>=0:
            rate=rate+2
        if flag.find('t')>=0 or flag.find('f')>=0:
            rate=rate+20
        elif flag.find('m')>=0:
            rate=rate+2
        if flag.find('7')>=0 or flag.find('B')>=0:
            rate=rate+2
        elif flag.find('E')>=0:
            rate=rate+4
        if flag.find('D')>=0:
            rate=rate+4
        # 精吊2x；
        score=[-rate*base,-rate*base,-rate*base,-rate*base]
        score[tableid]=rate*base*3
        # 德国x2：点炮-5，自摸-5*3;
        if flag.find('d')>=0:
            ds=2*base
            if flag.find('m')>=0 and not flag.find('t'):
                score[tableid]=score[tableid]+(ds+5)*3
                for i in range(4):
                    if i!=tableid: score[i]=score[i]-(ds+5)
            elif flag.find('f')<=0:
                score[tableid]=score[tableid]+ds*3+5
                for i in range(4):
                    if i!=tableid: score[i]=score[i]-ds
                score[self.lastOpt.tableid]=score[self.lastOpt.tableid]-5
        # 点炮x2  点炮玩家-2x，其他-x
        if flag.find('m')<=0 and flag.find('t')<=0 and flag.find('f')<=0:
            score[tableid]=score[tableid]+(2+1+1)*base
            score[self.lastOpt.tableid]=score[self.lastOpt.tableid]-base
            for i in range(4):
                if i!=tableid: score[i]=score[i]-base
        # 抢杠4x

        if not self.delay_15s.called and not self.delay_15s.cancelled:
            self.delay_15s.cancel()
        return defer.succeed((ro,str1,pai,score[0],score[1],score[2],score[3],flag))

    def test_qidui(self,pai):
        '''
        验证七对;
        '''
        if len(pai)!=14:
            return False
        zz=set(pai)
        if len(zz)<=7:
            return 'd'                            #德国七对
        n=sum([pai.count(i) for i in self.jins])  #精牌个数
        if n<1: return False
        for i in zz:
            if not i in self.jins and pai.count(i)%2==1: n=n-1
        if n<0: return False
        print u'有万能牌的七对'
        return '7'

    def test_13lan(self,pai):
        '''
        验证十三烂/七星十三烂；
        '''
        if len(pai)!=14:
            return False
        for i in range(len(pai)):
            if i==0: continue
            if ord(pai[i])==ord(pai[i-1]): break
            if not(pai[i] in PAI_FENG or pai[i] in PAI_JIAN or abs(ord(pai[i])-ord(pai[i-1]))>1):break
        else:
            if PAI_JIAN in pai and PAI_FENG in pai:
                print u'七星13烂/德国'
                return 5
            else:
                print u'13烂/德国'
                return 4
        # ===============不支持13烂有精牌；=====================================================
        return False

    def test_putong_hu(self,pai):
        '''
        验证普通胡牌类型是否合法；返回d/True/False
        '''
        tt=[]
        vv=pai.split(',')
        for i in vv:
            if i: tt.append(i)
        if len(tt)!=5:
            print u'\t->普通胡牌面必须为5组。'
            return False
        zz=[len(kk)for kk in tt]
        if zz.count(2)!=1:
            print u'\t->普通胡有且仅有一对将。'
            return False
        if not set(zz).issubset(set([2,3,4])):
            print u'\t->普通胡每组只能3张或4张组合。'
            return False
        dd='d'  #德国标记；
        for zu in tt:
            rr=self.test_group(zu)
            if not rr:
                break
            if rr!='d':
                dd=True
        else:
            return dd
        return False

    def test_group(self, zu):
        '''
        验证普通胡牌的分组类型是否合法以及是不是德国；返回d/1/False
        '''
        nn=set(zu)
        if len(nn)==1:
            return 'd'      # 德国将/刻/杠；
        if len(nn)==3 and ord(max(nn))-ord(min(nn))==2:
            return 'd'      # 德国顺子
        ss=set(zu)-self.jins
        if len(ss)<=1:
            return 1        # 含赖子牌的将/刻/杠；
        elif len(ss)==2 and len(zu)==3:
            s2=list(ss)
            if abs(ord(s2[0])-ord(s2[1])) in [1,2]:
                return 1    # 含1个赖子牌的顺子;
        return False

    def test_dezhongde(self,tableid):
        '''
        判断德中德；返回True/False
        '''
        pos1=self.get_next(tableid)
        pos2=self.get_next(pos1)
        pos3=self.get_next(pos2)
        for i in self.jins:
            if i in self.pais[pos1] or i in self.pais[pos2] or i in self.pais[pos3]:
                return False
            if i in self.lizhi[pos1] or i in self.lizhi[pos2] or i in self.lizhi[pos3]:
                return False
        return True

    def ting_pai(self, tableid, ss):
        '''
        听牌；
        :param tableid:
        :param ss:
        :return:
        '''
        if not hasattr(self,'ting'): self.ting=['','','','']
        self.ting[tableid]=ss