#!/usr/bin/env python
# -*- coding:utf-8 -*
from bottle import *
import requests
from time import time
from random import random
import re
import ujson as json
from io import BytesIO
import arrow
import pyexcel as pe
from uuid import uuid4

attachments = {}
sourceURL = 'http://qun.qq.com/member.html'


class QQGroup(object):
    """QQ Group Members"""

    def __init__(self):
        super(QQGroup, self).__init__()
        self.js_ver = '10233'
        self.newSession()

    def newSession(self):
        self.sess = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
        }
        self.sess.headers.update(headers)
        return

    def qrShow(self):
        self.newSession()
        url = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin'
        params = {
            'appid': '715030901',
            'daid': '73',
            'pt_no_auth': '1',
            's_url': sourceURL
        }
        resp = self.sess.get(url, params=params, timeout=1000)
        pattern = r'imgcache\.qq\.com/ptlogin/ver/(\d+)/js'
        try:
            self.js_ver = re.search(pattern, resp.content).group(1)
        except:
            pass
        self.sess.headers.update({'Referer': url})
        url = 'https://ssl.ptlogin2.qq.com/ptqrshow'
        params = {
            'appid': '715030901',
            'e': '2',
            'l': 'M',
            's': '3',
            'd': '72',
            'v': '4',
            't': '%.17f' % (random()),
            'daid': '73',
            'pt_3rd_aid': '0'
        }
        resp = self.sess.get(url, params=params, timeout=1000)
        return resp

    def qrLogin(self):
        login_sig = self.sess.cookies.get_dict().get('pt_login_sig', '')
        qrsig = self.sess.cookies.get_dict().get('qrsig', '')
        if not all([login_sig, qrsig]):
            return
        url = 'https://ssl.ptlogin2.qq.com/ptqrlogin'
        params = {
            'u1': sourceURL,
            'ptqrtoken': self.genQRToken(qrsig),
            'ptredirect': '1',
            'h': '1',
            't': '1',
            'g': '1',
            'from_ui': '1',
            'ptlang': '2052',
            'action': '0-0-%d' % (time() * 1000),
            'js_ver': self.js_ver,
            'js_type': '1',
            'login_sig': login_sig,
            'pt_uistyle': '40',
            'aid': '715030901',
            'daid': '73'
        }
        resp = self.sess.get(url, params=params, timeout=1000)
        return resp

    def getGroupList(self):
        self.sess.headers.update({'Referer': sourceURL})
        skey = self.sess.cookies.get_dict().get('skey', '')
        url = 'http://qun.qq.com/cgi-bin/qun_mgr/get_group_list'
        data = {
            'bkn': self.genBKN(skey)
        }
        resp = self.sess.post(url, data=data, timeout=1000)
        return resp

    def searchGroupMembers(self, gc):
        skey = self.sess.cookies.get_dict().get('skey', '')
        url = 'http://qun.qq.com/cgi-bin/qun_mgr/search_group_members'
        st = 0
        group = {}
        while 1:
            end = st + 20
            data = {
                'gc': str(gc),
                'st': str(st),
                'end': str(end),
                'sort': '0',
                'bkn': self.genBKN(skey),
            }
            resp = self.sess.post(url, data=data, timeout=1000)
            content = resp.json()
            count = content['count']
            if st == 0:
                group.update(content)
            else:
                group['mems'].extend(content['mems'])
            if end >= int(count):
                break
            else:
                st += 21
        return group

    def genQRToken(self, qrsig):
        e = 0
        for i in xrange(0, len(qrsig)):
            e += (e << 5) + ord(qrsig[i])
        qrtoken = (e & 2147483647)
        return str(qrtoken)

    def genBKN(self, skey):
        b = 5381
        for i in xrange(0, len(skey)):
            b += (b << 5) + ord(skey[i])
        bkn = (b & 2147483647)
        return str(bkn)


def rmWTS(content):
    try:
        pattern = r'\[em\]e\d{4}\[/em\]|</?[^>]+>|&nbsp;|&#\d+;'
        content = re.sub(pattern, ' ', content)
        content = content.replace('&lt;', '<').strip()
        content = content.replace('&gt;', '>').strip()
        content = content.replace('&amp;', '&').strip()
    except:
        pass
    return content


app = Bottle()
q = QQGroup()


@app.route('/static/<path:path>')
def server_static(path):
    return static_file(path, root='static')


@app.route('/')
def home():
    redirect('/qgmems/')


@app.route('/qgmems')
@app.route('/qgmems/')
@view('qgmems')
def qgmems():
    response.set_header('Content-Type', 'text/html; charset=UTF-8')
    response.add_header('Cache-Control', 'no-cache')
    return


@app.route('/qgmems/qrshow')
def qrShow():
    response.set_header('Content-Type', 'image/png')
    response.add_header('Cache-Control', 'no-cache, no-store')
    response.add_header('Pragma', 'no-cache')
    return q.qrShow()


@app.route('/qgmems/qrlogin')
def qrLogin():
    resp = q.qrLogin()
    content = resp.content
    status = -1
    errorMsg = ''
    try:
        if '二维码未失效' in content:
            status = 0
        elif '二维码认证中' in content:
            status = 1
        elif '登录成功' in content:
            status = 2
            pattern = r"(http://ptlogin2\.qun\.qq\.com/check_sig[^']+)"
            url = re.search(pattern, content).group(1)
            q.sess.get(url, timeout=1000)
        elif '二维码已失效' in content:
            status = 3
        else:
            errorMsg = str(content.text)
    except:
        try:
            errorMsg = str(resp.status_code)
        except:
            pass
    loginResult = {
        'status': status,
        'errorMsg': errorMsg,
        'time': time()
    }
    response.body = json.dumps(loginResult)
    response.set_header('Content-Type', 'application/json; charset=UTF-8')
    response.add_header('Cache-Control', 'no-cache; must-revalidate')
    response.add_header('Expires', '-1')
    return response


@app.route('/qgmems/glist')
def groupList():
    resp = q.getGroupList()
    content = resp.json()
    create = content.get('create', [])
    manage = content.get('manage', [])
    joinin = content.get('join', [])
    markup = []
    if len(create) > 0:
        desc = u'<span>我创建的群(%s)</span>' % (len(create))
        markup.append(desc)
        groups = ['<ul>']
        for g in create:
            item = '<li title="%s" onclick="gMembers(%s)"><img src="//p.qlogo.cn/gh/%s/%s_1/40">&nbsp;&nbsp;%s</li>' % (
                rmWTS(g['gn']),
                g['gc'],
                g['gc'],
                g['gc'],
                rmWTS(g['gn'])
            )
            groups.append(item)
        groups.append('</ul>')
        markup.append(''.join(groups))
    if len(manage) > 0:
        desc = u'<span>我管理的群(%s)</span>' % (len(create))
        markup.append(desc)
        groups = ['<ul>']
        for g in manage:
            item = '<li title="%s" onclick="gMembers(%s)"><img src="//p.qlogo.cn/gh/%s/%s_1/40">&nbsp;&nbsp;%s</li>' % (
                rmWTS(g['gn']),
                g['gc'],
                g['gc'],
                g['gc'],
                rmWTS(g['gn'])
            )
            groups.append(item)
        groups.append('</ul>')
        markup.append(''.join(groups))
    if len(joinin) > 0:
        desc = u'<span>我加入的群(%s)</span>' % (len(joinin))
        markup.append(desc)
        groups = ['<ul>']
        for g in joinin:
            item = '<li title="%s" onclick="gMembers(%s)"><img src="//p.qlogo.cn/gh/%s/%s_1/40">&nbsp;&nbsp;%s</li>' % (
                rmWTS(g['gn']),
                g['gc'],
                g['gc'],
                g['gc'],
                rmWTS(g['gn'])
            )
            groups.append(item)
        groups.append('</ul>')
        markup.append(''.join(groups))
    response.set_header('Content-Type', 'text/html; charset=UTF-8')
    response.add_header('Cache-Control', 'no-cache')
    return ''.join(markup)


@app.route('/qgmems/gmembers', method='POST')
def groupMembers():
    gc = request.forms.get('gc')
    group = q.searchGroupMembers(gc)
    data = [(u'昵称', u'群角色', u'群名片', u'QQ号', u'性别', u'Q龄',
             u'入群时间', u'积分(活跃度)', u'最后发言', u'QQ邮箱')]
    for m in group['mems']:
        nick = m['nick']
        nick = rmWTS(nick)
        role = m['role']
        role = rmWTS(role)
        if str(role) == '0':
            role = u'群主'
        elif str(role) == '1':
            role = u'管理员'
        else:
            role = ''
        card = m['card']
        card = rmWTS(card)
        uin = m['uin']
        gender = m['g']
        if str(gender) == '0':
            gender = u'男'
        elif str(gender) == '1':
            gender = u'女'
        else:
            gender = u'未知'
        qage = u'%s年' % (m['qage'])
        join_time = m['join_time']
        try:
            join_time = arrow.get(str(join_time)).format('YYYY/MM/DD')
        except:
            join_time = 'NULL'
        lv_point = str(m['lv']['point'])
        last_speak_time = m['last_speak_time']
        try:
            last_speak_time = arrow.get(str(last_speak_time)).format('YYYY/MM/DD')
        except:
            last_speak_time = 'NULL'
        mail = '%s@qq.com' % (uin)
        item = (nick, role, card, uin, gender, qage,
                join_time, lv_point, last_speak_time, mail)
        data.append(item)
    f = BytesIO()
    sheet = pe.Sheet(data)
    sheet.save_to_memory('xls', f)
    resultId = uuid4().hex
    attachments.update(
        {
            resultId: {
                'name': gc,
                'content': f
            }
        }
    )
    response.set_header('Content-Type', 'text/html; charset=UTF-8')
    response.add_header('Cache-Control', 'no-cache; must-revalidate')
    response.add_header('Expires', '-1')
    return resultId


@app.route('/qgmems/download')
def download():
    resultId = request.query.rid or ''
    result = attachments.get(resultId, '')
    if result:
        fileNme = '%s.xls' % (result['name'])
        content = result['content']
        response.set_header('Content-Type', 'application/vnd.ms-excel')
        response.add_header('Content-Disposition',
                            'attachment; filename="%s"' % (fileNme))
        return content.getvalue()
    else:
        abort(404)


if __name__ == '__main__':
    # https://bottlepy.org/docs/dev/deployment.html#switching-the-server-backend
    run(app, server='paste', host='localhost',
        port=8080, debug=True, reloader=True)
