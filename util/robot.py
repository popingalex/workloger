from .config import profile
from urllib.parse import urlencode
import requests
from html.parser import HTMLParser
import json
import re

URL_ROOT = 'http://106.37.227.19:7003'
PATH_LOGIN = 'ams/util/sys/login.do?method=login&username={}&pwd={}'
PATH_DETAIL = 'ams/ams_weekly/WeeklyweeklyDisplay.do?weeklyweeklyid={}'
PATH_HISTORY = 'ams/ams_weekly/WeeklyweeklyBrowse.do?flag=false'

PATTERN_PARAM = r'/ams/ams_weekly/WeeklyweeklyBrowse.do\?ctrl=weeklyweeklyvalueobject&action=Drilldown&param=(?P<param>\w+)'
PATTERN_TIMES = {
    'start_time': r'var sst = \'(?P<time>[-\w: ,]+)\'',
    'end_time': r'var set = \'(?P<time>[-\w: ,]+)\'',
    'over_start_time': r'var osst = \'(?P<time>[-\w: ,]+)\'',
    'over_end_time': r'var oset = \'(?P<time>[-\w: ,]+)\''
}


def foreground():
    pass


class HistoryParamParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.depth = 0
        self.flag = False
        self.parse = False
        self.params = []

    def get_params(self):
        return list(set(self.params))

    def handle_starttag(self, tag, attrs):
        def get_attr(_attrs, name):
            for k, v in _attrs:
                if name == k:
                    return v
            return None

        self.depth += 1

        if ('table' == tag) and ('lcb' == get_attr(attrs, 'class')):
            self.flag = self.depth

        if self.flag:
            if 'a' == tag:
                href = get_attr(attrs, 'href').replace("¶m", "&param")
                result = re.search(PATTERN_PARAM, href)
                if result:
                    param = result.group('param')
                    self.params.append(param)

    def handle_endtag(self, tag):
        if self.depth == self.flag:
            self.flag = False
        self.depth -= 1


class DetailParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.data = {}
        self.key = None

    def get_data(self):
        return self.data

    def handle_starttag(self, tag, attrs):
        def get_attr(_attrs, name):
            for k, v in _attrs:
                if name == k:
                    return v
            return None

        if 'script' == tag and get_attr(attrs, 'src') is None:
            self.key = 'script'
        if 'textarea' == tag and 'weeklycontent' == get_attr(attrs, 'name'):
            self.key = 'content'

    def handle_data(self, data):
        if self.key is not None:
            self.data[self.key] = data
            self.key = None
        pass


class Background:
    def __init__(self):
        print('username : {}'.format(profile['username']))
        self.session = requests.session()

    def login(self):
        response = self.session.get('{}/{}'.format(URL_ROOT, PATH_LOGIN).format(profile['username'],
                                                                                profile['password']))
        print(response)
        if response.status_code == 200 and "toUrl:'ams_weekly/AnaphaseTreatmentBrowse.do'" in response.content.decode():
            print('login success')
            # print(response.cookies)
        else:
            print('login faield: {}'.format(response.content.decode()))
            exit(1)

    def detail(self, param):
        response = self.session.get('{}/{}'.format(URL_ROOT, PATH_DETAIL).format(param))
        detail_parser = DetailParser()
        detail_parser.feed(response.content.decode())
        data = detail_parser.get_data()
        content = {'content': data['content'].strip()}
        for key, value in PATTERN_TIMES.items():
            result = re.search(value, data['script'])
            content[key] = result.group('time').split(',')[:-1][0] if result else ''
        return content

    def history(self, username='', begin='', end=''):
        response = self.session.post('{}/{}'.format(URL_ROOT, PATH_HISTORY), data=urlencode({
            'begintime': begin,
            'endtime': end,
            'username': username,
            'projectname': '',
            'projectid': '',
            'btnSearch': 'clicked',
            'btnLoad': '',
            'formid': 'frmSearch',
            'zhours': ''
        }), headers={'Content-Type': 'application/x-www-form-urlencoded'})
        param_parser = HistoryParamParser()
        param_parser.feed(response.content.decode())
        return [self.detail(param) for param in param_parser.get_params()]

    def demo(self):
        self.login()
        for detail in self.history(username='许文哲', begin='2018-03-08', end='2018-03-10'):
            print(detail)
        pass
