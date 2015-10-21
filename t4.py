#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/10/13 11:09  

import base64
from twisted.web import xmlrpc, server
class Example(xmlrpc.XMLRPC):
    """An example object to be published."""
    def xmlrpc_attachfile(self, pagename, attachname, data):
        """
        Return sum of arguments.
        """
        filename = pagename+attachname
        fh = open(filename, 'wb+')
        fh.write(base64.decodestring(data))
        fh.close()

if __name__ == '__main__':
    from twisted.internet import reactor
    r = Example()
    reactor.listenTCP(7080, server.Site(r))
    reactor.run()