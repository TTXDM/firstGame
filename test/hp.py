#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: eric_li
# created: 2015/7/15 18:09  

#encoding:utf-8
import random, re, itertools
#风牌-箭牌-字牌[万条筒]
_wan = list('123456789')#万牌的集合;
_tiao = list('ABCDEFGHI')#条子的集合;
_tong = list('abcdefghi')#筒子的集合;
_feng = list('kmwusoq')#风牌和箭牌的集合;
_pais = _wan + _tiao + _tong + _feng
_allPai = _pais * 4#所有牌的集合
_pai = random.sample(_allPai, 14 + 13 + 13 + 13)#随机发牌
_Pai = ''.join(_pai[:14])
print '->随机发牌：庄0:', _Pai
print '\t->闲1：', ''.join(_pai[14:27])
print '\t->闲2：', ''.join(_pai[27:40])
print '\t->闲3：', ''.join(_pai[40:])

class HasHuPai(Exception): pass
class NotTinPai(Exception): pass

def strSort(str):
    '''
             排序一个字符串
    '''
    tmp = list(str); tmp.sort()
    return ''.join(tmp)

def dupRemove(seq):
    '''
             元素唯一的数组（去除重复项）;
    '''
    checked = []
    for e in seq:
        if e not in checked: checked.append(e)
    return checked

def sunzi(arr):
    '''
              找出序列中所有可能的顺子;
    '''
    try:
        arr = map(int, arr)
        for p in arr:
            if  p + 1 in arr and p + 2 in arr:
                yield [p, p + 1, p + 2]
    except:
        raise StopIteration

class ResObject():
    '''
              牌面扫描结果;
    '''
    def __init__(self, j=[], g=[], k=[], s=[], z=[]):
        self.ke = k
        self.sun = s
        self.jang = j
        self.gang = g
        self.zuhe = z
#    def __repr__(self):
#        _arr = [self.jang, self.sun, self.ke, self.gang, self.zuhe]
#        _arr = map(lambda x:len(x) > 0 and x or None, _arr)
#        _arr = map(str, _arr)
#        print '\n\t->----'.join(_arr)
#        return '\t->'.join(_arr)

def groupScan(flag, arr):
    '''
              检测每一组牌是否合格; 空牌返回None; 未听牌产生异常;
    '''
    try:
#       print '\t————————' + ['万', '条', '筒', '风'][flag] + '————————'
        print '----------------------------', arr
        if len(arr) == 0: print '\t->牌: Null'; return None
        arr.sort(); tmp = ''.join(map(str, arr))
        jang = re.compile(r'(\w)\1').findall(tmp)
        ke = re.compile(r'(\w)\1{2}').findall(tmp)
        gang = re.compile(r'(\w)\1{3}').findall(tmp)
        if flag == 3:
            sun = []
            ke = [[str(s)] * 3 for s in ke]
            jang = [[str(s)] * 2 for s in jang]
            gang = [[str(s)] * 4 for s in gang]
        else:
            ke = [[str(s)] * 3 for s in ke]
            jang = [[str(s)] * 2 for s in jang]
            gang = [[str(s)] * 4 for s in gang]
            sun = [s for s in sunzi(arr[:])]

        print '\n\t->牌:', tmp
        if len(sun) > 0:    print '\t->顺:', sun
        if len(jang) > 0:   print '\t->将:', jang
        if len(ke) > 0:     print '\t->刻:', ke
        if len(gang) > 0:   print '\t->杠:', gang

        z0 = len(arr)
        v1 = len(sun)
        v2 = len(gang)
        v3 = len(jang)
        v4 = len(ke)
        v0 = v1 + v2 + v3 + v4
        if v0 == 0:
            raise NotTinPai
        elif v2 == v0 and  z0 == v2 * 4:
            zuhe = [gang]
        elif v3 == v0 and  z0 == v3 * 2:
            zuhe = [jang]
        elif v4 == v0 and  z0 == v4 * 3:
            zuhe = [ke]
        else:
            zuhe = []
            zz = len(arr)
            pp = sun[:]
            pp.extend(ke)
            pp.extend(gang)
            gg = dupRemove(jang)
            gg.append([])

            ff = len(pp)
            ff = ff > 4 and 4 or ff
            for g in gg:
                for i in range(ff):
                    for s in itertools.combinations(pp, i + 1):
                        _sn = list(s)[:]
                        _sn.append(g)
                        if sum([len(n) for n in _sn]) == zz:
                            _p = strSort(''.join([''.join(map(str, i)) for i in _sn]))
                            if _p == tmp:
                                zuhe.append(filter(lambda x: x != [], _sn))
            zuhe = dupRemove(zuhe)
        for s in zuhe: print '\t->组合:', s
        if len(zuhe) == 0:  raise NotTinPai
        return ResObject(jang, sun, ke, gang, zuhe)
    except EOFError, e:
        print e
        return None

def groupZuhe(arr=[], *args):
    res = [None]
    arr = list(args)
    def merge(m, n): z = m and m[:] or []; z.extend(n); return z
    while len(arr) > 0:
        sss = arr.pop(0)
        if len(sss) > 0: res = [merge(i, j) for i in res for j in sss]
    return res

def isHu(_pai):
    '''
             判断是否胡牌；
    '''
    try:
        _pai = strSort(_pai)
        print '->手牌:', _pai

        if not re.match(r'^[1-9A-Ia-ikmwusoq]{14,}$', _pai):
            raise Exception('牌型错误.')

        if len(_pai) == 14 and re.compile(r'(?:(\w)\1{1}){7}').match(_pai):
            raise HasHuPai('七对')

        if re.sub(r'(\w)\1', '\\1', _pai) == '19AIaikmoqsuw':
            raise HasHuPai('国士无双')

        _sort = [ re.findall(_r, _pai) for _r in [r'\d', r'[A-I]', r'[a-i]', r'[kmwusoq]']]
        _conv = [lambda x:int(x), lambda x:1 + ord(x) - ord('A'), lambda x:1 + ord(x) - ord('a'), None]
        _scan = [groupScan(i, map(_conv[i], _sort[i])) for i in range(4)]

        _zuhe = [None]
        _arr = map(lambda x:(isinstance(x, ResObject) and len(x.zuhe) > 0) and x.zuhe or [] , _scan)
        _arr = filter(lambda x:len(x) > 0, _arr)
        def merge(m, n):
            res = m and m[:] or []
            res.extend(map(lambda x:len(x), n))
            return res
        while len(_arr) > 0:
            sss = _arr.pop(0)
            if len(sss) > 0:
                _zuhe = [merge(i, j) for i in _zuhe for j in sss]

        for s in _zuhe:
            s.sort()
            if re.match(r'^2[3,4]{4}$', ''.join(map(str, s))):
                print '胡牌型：', s

    except HasHuPai, e:
        print '[胡]', e
    except NotTinPai:
        print '[未听牌]'


###################################################################################################
if __name__ == "__main__":
    #s = isHu('aabbwwddeeffgg')
    #s = isHu('19AIaikmoqsuwm')
    #s = isHu('Gi4b5HIwgbwhb6')
    # s = isHu('1231ccc2322abc')

    #isHu("123123123acdww")

    xx = '1231ccc2322abc'
    def test():
        isHu('1231ccc2322abc')
        # for s in _allPai:
        #     isHu(xx + s)


    import profile, pstats
    profile.run('test()', 'test.prof')
    p = pstats.Stats("test.prof")
    p.sort_stats("time").print_stats()

    #import profile, pstats
    #profile.run('isHu("1231231231234444ww")', 'test.prof')
    #p = pstats.Stats("test.prof")
    #p.sort_stats("time").print_stats()

    #s = isHu('1231231231234444ww')
    #s = isHu('12334566789444')
    #s = isHu('23456ACGIahhow')
    #s = isHu('566DEFGHchmosu')
    #s = isHu(_Pai)


