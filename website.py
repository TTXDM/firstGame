#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/10/13 9:58  

from twisted.web.resource import Resource
from twisted.web import server
from twisted.web import static
from twisted.internet import reactor

PORT = 1234

########################################################################
class ReStructed(Resource):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, filename, *a):
        """Constructor"""
        self.rst = open(filename).read()
    def render(self, request):
        return self.rst

resource = static.File('log/')
resource.processors = {'.html':ReStructed}
resource.indexNames = ['index.html']

reactor.listenTCP(PORT, server.Site(resource))
reactor.run()


