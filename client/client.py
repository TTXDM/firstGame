#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/10/9 13:56  
import struct, logging, sys
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.protocols.policies import TimeoutMixin

########################################################
#                     socket_client
########################################################
class AppProtocol(Protocol, TimeoutMixin):
    def __init__(self, data_handler, *args, **kwargs):
        self._buffer = ''
        self._packetLen = 0
        self.data_handler=data_handler

    def connectionMade(self):
        logging.getLogger('sock').info(u'connected:'+str(self.transport.getPeer()))

    def connectionLost(self, reason):
        logging.getLogger('sock').info(u'disconnected:'+str(self.transport.getPeer()))
        from packet import msg_notify
        msg_notify(self,'connectionLost')

    def dataReceived(self, data):
        '''
        协议数据拼包处理;
        '''
        print '\n------------------------------------------------------------------------------------'
        print 'dataReceived:',  len(data),  len(self._buffer)
        self._buffer+=data
        while True:
            if self._packetLen==0 and len(self._buffer)>=4:
                self._buffer, head = self._buffer[4:], self._buffer[:4]
                self._packetLen=struct.unpack(">I", head)[0]
                # print u'拼包：', self._packetLen, len(self._buffer)

            if self._packetLen>0 and self._packetLen <= len(self._buffer):
                self._packetLen, self._buffer, pack = 0, self._buffer[self._packetLen:], self._buffer[:self._packetLen]
                # print u'处理：', len(pack)
                self.data_handler(self, pack)

            if self._packetLen==0 and len(self._buffer)<4:
                # print u'+++++++++', len(self._buffer)
                break

            if self._packetLen>0 and self._packetLen > len(self._buffer):
                # print u"========", self._packetLen, len(self._buffer)
                break

    def sendData(self, data):
        str_size = len(data)
        self.transport.write(struct.pack(">I", str_size))
        self.transport.write(struct.pack(">%ds"%str_size, data))
        # print u"发送:", len(data), self.transport.getPeer()





