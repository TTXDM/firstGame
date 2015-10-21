#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/7/8 15:36  
'''
SYS_ALERT=1000;         //alert；
ACCOUNT_REGISTER=1024;  //注册账号； 请求及返回；
AUTON_LOGIN=1025;       //登录验证   请求及返回
LOBBY_ROOMLIST=1030;    //获取大厅房间列表   请求及返回
LOBBY_ENTER_ROOM=1032;  //进入房间   请求及返回

LOBBY_CHAT_SEND=1040;   //大厅里发送聊天消息;
LOBBY_CHAT_MSG=1042;    //大厅聊天消息接收;

GAME_CHAT_MSG=1043;     //房间内聊天消息接收;
GAME_PLAYER_READY=1050; //客户端准备好开始游戏;
GAME_ALL_START=1051;    //游戏开始;
GAME_PLAYER_JOIN=1052;  //新玩家进入房间;
GAME_PLAYER_EXIT=1053;  //房间内玩家退出;

GAME_ZUA_PAI=1054;      //抓牌;
GAME_DROP=1058;         //打出一张牌;
GAME_DROP_PAI=1059;     //（广播）其他玩家打出一张牌;

GAME_CHI=1055; 		 //吃牌;
GAME_PENG=1056; 		 //碰牌;
GAME_GANG=1057; 		 //杠牌;
GAME_ANGANG=1062; 		 //暗杠牌;
GAME_CHI_PAI=1063; 	 //吃牌（广播）;
GAME_PENG_PAI=1064; 	 //碰牌（广播）;
GAME_GANG_PAI=1065; 	 //杠牌（广播）;
GAME_ANGANG_PAI=1066; 	 //暗杠牌（广播）;

GAME_TING=1060; 		 //听牌 &&（广播）;

GAME_QIANG=1061; 		 //抢牌（点击碰，杠时广播）;

GAME_HU=1088; 			 //胡牌;
GAME_HU_PAI=1089; 		 //（广播）胡牌;
'''

HOST='localhost'
PORT=6988

PAI_DONG = 'r'  #东风
PAI_NAN = 's'   #南风
PAI_XI = 't'    #西风
PAI_BEI = 'u'   #北风
PAI_ZHONG = 'x' #红中
PAI_FA = 'y'    #发财
PAI_BAI = 'z'   #白板
PAI_WAN = '123456789'   #一万~九万
PAI_TIAO = 'ABCDEFGHI'  #一条~九条
PAI_TONG = 'abcdefghi'  #一筒~九筒
PAI_JIAN = PAI_ZHONG+PAI_FA+PAI_BAI   #箭牌
PAI_FENG = PAI_DONG+PAI_NAN+PAI_XI+PAI_BEI  #风牌
ALL_PAI=PAI_WAN+PAI_TIAO+PAI_TONG+PAI_FENG+PAI_JIAN
ALL_PAI_NAME=[u'一万',u'二万',u'三万',u'四万',u'五万',u'六万',u'七万',u'八万',u'九万',\
              u'一条',u'二条',u'三条',u'四条',u'五条',u'六条',u'七条',u'八条',u'九条',\
              u'一筒',u'二筒',u'三筒',u'四筒',u'五筒',u'六筒',u'七筒',u'八筒',u'九筒',\
              u'东风',u'南风',u'西风',u'北风',u'红中',u'发财',u'白板']

def PAI_NAME(p):
    idx=ALL_PAI.find(p)
    return (idx<0 and '' or ALL_PAI_NAME[idx])+'['+p+']'