#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/10/13 15:26  

page_manager={}
def page_get_users(pageId):
    try:
        users = page_manager.get(str(pageId),None)
        if type(users)==set and len(users)>0:
            return users
        elif page_manager.has_key(str(pageId)):
            del page_manager[str(pageId)]
    except ReferenceError,e:
        pass
    return []

def page_join_user(user, pageId):
    if not page_manager.has_key(str(pageId)):
        page_manager[str(pageId)]=set()
    users = page_manager.get(str(pageId),None)
    if type(users)!=set:
        page_manager[str(pageId)]=set()
    users.add(user)

def page_remove_user(user,pageId):
    users = page_manager.get(str(pageId),None)
    if type(users)==set and len(users)>0 and user in users:
        users.remove(user)


page_join_user('666',8)
page_join_user('444',8)
page_join_user('333',8)
page_join_user('333',8)
print page_get_users(8)
page_remove_user('666',8)
page_remove_user('666',8)
page_remove_user('333',8)
page_remove_user('333',8)
page_remove_user('33',8)

print page_get_users(8)