from .config import profile
from urllib.parse import urlencode
import requests
from lxml import etree
import json
import re

URL_ROOT = 'http://106.37.227.19:7003'
URL_ROOT = 'http://192.168.29.31:7003'
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

    def log(self, project_key, project_name, content, start='', end='', iscomplete="100"):
        data = {
            "projectid": project_key,
            "formid": "frmCreate",
            "projectname": project_name,
            "weeklycontent": content,
            "starttime": start,
            "endtime": end,
            "iscomplete": iscomplete,
            # 计划
            "plancontent": "",
            # 问题
            "problem": "",
            # 备注
            "remark": "",
            "btnAdd": "",
            "btnSave": "clicked",
            "btnBack": "",
            "startstr": "",
            "endstr": "",
            "overstartstr": "",
            "overendstr": "",
            "otherprojerctid": "",
        }
        data = urlencode(data)
        print(data)
        self.session.get('{}/{}'.format(URL_ROOT, 'ams/ams_weekly/WeeklyweeklyBrowse.do?ctrl=weeklyweeklyvalueobject&action=Create'))
        response = self.session.post('{}/{}'.format(URL_ROOT, PATH_LOG), data=data, headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            'Content-Length': str(len(data)),
            "Referer": "{}/{}".format(URL_ROOT, PATH_LOG),
            # "Referer": "{}/{}".format(URL_ROOT, 'ams/ams_weekly/WeeklyweeklyBrowse.do?flag=true'),
            # "Host": URL_ROOT.replace("http://", ""),
        })
        print('cook : [{}]'.format(
            '; '.join(['{}={}'.format(key, value) for key, value in self.session.cookies.items()])))
        print('refe : [{}]'.format('{}/ams/ams_weekly/WeeklyweeklyAdd.do'.format(URL_ROOT)))
        print('host : [{}]'.format(URL_ROOT.replace('http://', '')))
        print('len  : [{}]'.format(str(len(data))))
        print(response)
        # print(response.content.decode())
        # print(response.headers)

    def log_modify(self):
        # TODO
        data = {
            "projectid": "40289d9f65ef74e10166ae3c4d7b0d28",
            "formid": "frmAdd",
            "projectname": "",
            "weeklycontent": "",
            "starttime": "2018-10-28+15%3A00",
            "endtime": "2018-10-28+18%3A00",
            "startstr": "",
            "endstr": "",
            "iscomplete": "60",
            "overstartstr": "",
            "overendstr": "",
            "userid": "xuwenzhe",
            "orgcode": "9004005001013",
            "weeklydate": "2018-10-29",
            "otherprojerctid": "",
            "plancontent": "",
            "problem": "",
            "remark": "",
            "btnSave": "",
            "btnBack": "",
        }

    def demo(self):
        self.login()

        project = self.project('工程效率改进平台')
        # self.log(project_key=project[0]['key'], project_name=project[0]['name'],
        #          content="与信息技术部李彦斌讨论云管理需求, 工程效率平台及协同开发工作方向梳理及云管理平台需求整理",
        #          start="2018-10-29 09:00", end="2018-10-29 18:00")
        # for detail in self.query(username='许文哲', begin='2018-10-28', end='2018-10-31'):
        #     print(detail)
        self.log(project_key=project[0]['key'], project_name=project[0]['name'],
                 content="测试",
                 start="2018-10-29 09:00", end="2018-10-29 18:00", iscomplete="50")
        for detail in self.query(username='许文哲', begin='2018-10-28', end='2018-10-31'):
            print(detail)
