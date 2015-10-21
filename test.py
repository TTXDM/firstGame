#!/usr/bin/env python
# coding:utf-8
#Author:  Administrator
#Created: 2015/9/23 14:26
from core.consts import *

from twisted.internet import reactor

from core.game_logic import *


game=Pai()
game.init_game(None,True)
game.game_jin(5)
game.lastOpt=Opt_info(0,opt_cup)
game.delay_15s=reactor.callLater(15000, lambda a:a);

class User():
    def __init__(self):
        self.id='eric1@test.com'
class Ro():
    def __init__(self):
        self.user=User()

ro=Ro()
print game.pais

pai=[2,'44,aaa,DDDD,789,abc']
pai=[2,'aaa,DDDD,789,abc,'+game.jin2[0]*2]
pai=[4,''.join(sorted('13579BDrstuxyc'))]
# pai=[3,'52345566388'+game.jin2[0]*3]

game.pais[0]=pai[1].replace(',','')
def test1():
    d=defer.maybeDeferred(game.hu_pai,ro,0,pai[0],pai[1])
    if d:
        print 'hu 000', d

test1()

