from .config import profile
from urllib.parse import urlencode
import requests
from lxml import etree
import json
import re

URL_ROOT = 'http://106.37.227.19:7003'
PATH_MAIN = 'ams/ams_weekly/WeeklyweeklyBrowse.do'
PATH_LOGIN = 'ams/util/sys/login.do?method=login&username={}&pwd={}'
PATH_DETAIL = 'ams/ams_weekly/WeeklyweeklyDisplay.do?weeklyweeklyid={}'
PATH_HISTORY = 'ams/ams_weekly/WeeklyweeklyBrowse.do?flag=true'
PATH_PROJECT = 'ams/util/frametree/OpensingleXtreeAction.do?datatype=son&openid=attendance_project&conds=projectname@like&keyname=projectid'
PATH_LOG = 'ams/ams_weekly/WeeklyweeklyAdd.do'

PATTERN_PARAM = '/ams/ams_weekly/WeeklyweeklyBrowse.do\?ctrl=weeklyweeklyvalueobject&action=Drilldown&param=(?P<param>\w+)'
PATTERN_TIMES = {
    'start_time': r'var sst = \'(?P<time>[-\w: ,]+)\'',
    'end_time': r'var set = \'(?P<time>[-\w: ,]+)\'',
    'over_start_time': r'var osst = \'(?P<time>[-\w: ,]+)\'',
    'over_end_time': r'var oset = \'(?P<time>[-\w: ,]+)\''
}
PATTERN_PROJECT_NAME = "nodes\['(?P<key>[a-z0-9]{32})'\] = new xyTree.NodeNormal\('(?P<name>.*)'\);.*"


def foreground():
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
            # 必须登陆一下这个页面才行
            self.session.get('{}/{}'.format(URL_ROOT, PATH_MAIN), params={'flag': 'true'}, timeout=10)
        else:
            print('login faield: {}'.format(response.content.decode()))
            exit(1)

    def detail(self, param):
        response = self.session.get('{}/{}'.format(URL_ROOT, PATH_DETAIL).format(param))
        node_page = etree.HTML(response.content.decode())

        content = {
            'content': node_page.xpath("//textarea[@name='weeklycontent']")[0].text.strip(),
            'project': node_page.xpath("//tr[@id='tr_attendanceprojectprojectname']/td[@class='fd']")[0].text.strip()
        }
        script_time = node_page.xpath("//script[@type='text/javascript' and not(@src)]")[0].text
        for key, value in PATTERN_TIMES.items():
            result = re.search(value, script_time)
            content[key] = result.group('time').split(',')[:-1][0] if result else ''
        return content

    def query(self, username='', begin='', end=''):
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
        node_page = etree.HTML(response.content.decode())
        list_node_record = node_page.xpath("//table[@class='lcb']//table/tr[@class!='header']//a")
        list_param = []
        for record in list_node_record:
            matcher = re.search(PATTERN_PARAM, record.attrib['href'])
            if matcher:
                list_param.append(matcher.group('param'))
        return [self.detail(param) for param in set(list_param)]

    def project(self, name=None):
        response = self.session.get('{}/{}'.format(URL_ROOT, PATH_PROJECT))
        node_page = etree.HTML(response.content.decode())
        script_init = node_page.xpath("//script[contains(text(), '//开始初始化树数据')]")[0].text
        list_matcher = re.findall(PATTERN_PROJECT_NAME, script_init)
        list_project = [{'key': key, 'name': name} for key, name in list_matcher]
        if name is not None:
            list_project = [project for project in list_project if project['name'].__eq__(name)]
        return list_project

    def log(self, project_key, project_name, content, start='', end='', over_start='', over_end=''):
        data = urlencode({
            'projectid': project_key,
            'formid': 'frmCreate',
            'projectname': project_name,
            'weeklycontent': content,
            'starttime': start,
            'endtime': end,
            'startstr': start,
            'endstr': end,
            'iscomplete': '100',
            # 'overtimestart': over_start,
            # 'overtimeend': over_end,
            # 'overstartstr': over_start,
            # 'overendstr': over_end,
            'btnSave': 'clicked',
            'otherprojectid': '',
            'plancontent': '',
            'problem': '',
            'remark': '',
            'btnAdd': '',
            'btnBack': '',
        })
        response = self.session.post('{}/{}'.format(URL_ROOT, PATH_LOG), data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(data)),
            'Referer': 'http://192.168.29.31:7003/ams/ams_weekly/WeeklyweeklyAdd.do',
            'Host': '106.37.227.19'
        }, allow_redirects=False)
        print(response.content)

    def demo(self):
        self.login()
        # for detail in self.query(username='许文哲', begin='2018-03-08', end='2018-03-10'):
        #     print(detail)

        for detail in self.query(username='许文哲', begin='2018-10-20', end='2018-10-30'):
            print(detail)
        project = self.project('工程效率改进平台')
        self.log(project_key=project[0]['key'], project_name=project[0]['name'],
                 content="工程效率平台工作内容整理",
                 start="2018-10-23 06:00", end="2018-10-23 18:00")
        pass
