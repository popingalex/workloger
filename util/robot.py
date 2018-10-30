from .config import profile
from urllib.parse import urlencode
import requests
from lxml import etree
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

URL_ROOT = 'http://106.37.227.19:7003'
PATH_MAIN = 'ams/ams_weekly/WeeklyweeklyBrowse.do'
PATH_LOGIN = 'ams/util/sys/login.do?method=login&username={}&pwd={}'
PATH_DETAIL = 'ams/ams_weekly/WeeklyweeklyDisplay.do?weeklyweeklyid={}'
PATH_HISTORY = 'ams/ams_weekly/WeeklyweeklyBrowse.do?flag=true'
PATH_PROJECT = 'ams/util/frametree/OpensingleXtreeAction.do'
PATH_LOG = 'ams/ams_weekly/WeeklyweeklyAdd.do'
PATH_EDIT = 'ams/ams_weekly/WeeklyweeklyEdit.do'

PATTERN_PARAM = '/ams/ams_weekly/WeeklyweeklyBrowse.do\?ctrl=weeklyweeklyvalueobject&action=Drilldown&param=(?P<p>\w+)'
PATTERN_TIMES = {
    'start_time': r'var sst = \'(?P<time>[-\w: ,]+)\'',
    'end_time': r'var set = \'(?P<time>[-\w: ,]+)\'',
    # 'over_start_time': r'var osst = \'(?P<time>[-\w: ,]+)\'',
    # 'over_end_time': r'var oset = \'(?P<time>[-\w: ,]+)\''
}
PATTERN_PROJECT_NAME = "nodes\['(?P<key>[a-z0-9]{32})'\] = new xyTree.NodeNormal\('(?P<name>.*)'\);.*"


class Foreground:
    def __init__(self):
        if profile['ie_driver'] == 'Locate your IE Driver':
            print('Locate your IE Driver please.')
            exit(1)

    def demo(self):
        # 需要关闭保护模式，部分网站需要开启兼容视图
        self.driver = webdriver.Ie(profile['ie_driver'])
        self.driver.maximize_window()
        self.driver.get('{}/ams'.format(URL_ROOT))
        self.driver.find_element_by_xpath('//input[@name="username"]').send_keys(profile['username'])
        self.driver.find_element_by_xpath('//input[@name="password"]').send_keys(profile['password'])
        self.driver.find_element_by_xpath('//div[@id="btnlogin"]').send_keys(Keys.ENTER)

        # self.driver.switch_to.default_content()
        # Keys.BACKSPACE
        self.driver.switch_to.frame('catiframe')
        self.driver.find_element_by_xpath('//a[@title="增加条目"]').send_keys(Keys.ENTER)
        self.driver.find_element_by_xpath('//input[@name="projectname"]').send_keys(' ', Keys.BACKSPACE)
        self.driver.switch_to.frame(self.driver.find_elements_by_xpath('//iframe[contains(@src, "项目工作")]'))



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
            'param': param,
            'weeklycontent': node_page.xpath("//textarea[@name='weeklycontent']")[0].text.strip(),
            'iscomplete': node_page.xpath("//tr[@id='tr_iscomplete']//td[@class='fd']")[0].text.strip(),
            'remark': (node_page.xpath("//textarea[@name='remark']")[0].text or '').strip(),
            'problem': (node_page.xpath("//textarea[@name='problem']")[0].text or '').strip(),
            'plancontent': (node_page.xpath("//textarea[@name='plancontent']")[0].text or '').strip(),
            'project': node_page.xpath("//tr[@id='tr_attendanceprojectprojectname']/td[@class='fd']")[0].text.strip()
        }
        script_time = node_page.xpath("//script[@type='text/javascript' and not(@src)]")[0].text
        for key, value in PATTERN_TIMES.items():
            result = re.search(value, script_time)
            content[key] = result.group('time').split(',')[:-1][0] if result else ''
        return content

    def query(self, username='', begin='', end='', search={}):
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
                list_param.append(matcher.group('p'))
        list_detail = [self.detail(param) for param in set(list_param)]

        def numtime(src):
            return int(src.split(' ')[-1].replace(':', ''))

        if 'project' in search:
            list_detail = [detail for detail in list_detail if search['project'] in detail['project']]
        if 'content' in search:
            list_detail = [detail for detail in list_detail if search['content'] in detail['content']]
        if 'begin' in search:
            list_detail = [detail for detail in list_detail if numtime(search['begin']) < numtime(detail['start_time'])]
        if 'end' in search:
            list_detail = [detail for detail in list_detail if numtime(search['end']) > numtime(detail['end_time'])]
        return list_detail

    def project(self, name=None):
        response = self.session.get('{}/{}'.format(URL_ROOT, PATH_PROJECT), params={'datatype': 'son',
                                                                                    'openid': 'attendance_project',
                                                                                    'conds': 'projectname@like',
                                                                                    'keyname': 'projectid'})
        node_page = etree.HTML(response.content.decode())
        script_init = node_page.xpath("//script[contains(text(), '//开始初始化树数据')]")[0].text
        list_matcher = re.findall(PATTERN_PROJECT_NAME, script_init)
        list_project = [{'key': key, 'name': name} for key, name in list_matcher]
        if name is not None:
            list_project = [project for project in list_project if project['name'].__eq__(name)]
        return list_project

    def log(self, project_key, project_name, content, start='', end='',
            iscomplete='100', problem='', plancontent='', remark='', over_start='', over_end=''):
        data = urlencode({
            'weeklycontent': content,
            'projectname': project_name,
            'iscomplete': iscomplete,
            'projectid': project_key,
            'starttime': start,
            'endtime': end,
            'startstr': start,
            'endstr': end,
            'formid': 'frmCreate',
            # 'overtimestart': over_start,
            # 'overtimeend': over_end,
            # 'overstartstr': over_start,
            # 'overendstr': over_end,
            'otherprojectid': '',
            'plancontent': plancontent,
            'problem': problem,
            'remark': remark,
            'btnAdd': '',
            'btnBack': '',
            'btnSave': 'clicked',
        })
        response = self.session.post('{}/{}'.format(URL_ROOT, PATH_LOG), data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(data)),
            'Referer': '{}/{}'.format(URL_ROOT, PATH_LOG),
            'Host': URL_ROOT.replace('http://', '')
        }, allow_redirects=False)
        print(response)

    def demo(self):
        self.login()

        # project = self.project('项目名称')
        # self.log(project_key=project[0]['key'], project_name=project[0]['name'],
        #          content="工作日志",
        #          start="2018-10-29 09:00", end="2018-10-29 18:00")
        for detail in self.query(username='许文哲', begin='2018-10-20', end='2018-10-30'):
            print(detail)

        pass
