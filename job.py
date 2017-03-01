# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import functools
import requests
import time
import re
import urlparse
import json
import pymysql
import maya


def random_ip():
    from faker import Faker
    faker = Faker()
    ip = faker.ipv4()
    return ip


# Connect to the database
db = pymysql.connect(host='120.27.201.184', user='root', password='bestoffer', db='bestoffer', charset='utf8mb4')


def dump2mysql(table, job):
    try:
        with db.cursor() as cursor:
            mapping = {
                'education': 'education',
                'work_year_min': 'work_year_min',
                'work_year_max': 'work_year_max',
                'work_year': 'work_year',
                'salary_min': 'salary_min',
                'salary_max': 'salary_max',
                'salary': 'salary',
                'create_time': 'create_time',
                'company_id': 'company_id',
                'company_name': 'company_name',
                'company_size': 'company_size',
                'position_id': 'position_id',
                'position_name': 'position_name',
                'url': 'url',
                'city': 'city',
                'source': 'source'
            }
            # Create a new record
            keys = mapping.values()
            columns = ", ".join(keys)
            values_template = ", ".join(["%s"] * len(keys))
            values = tuple(job[k] for k in mapping.keys())

            sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, columns, values_template)
            cursor.execute(sql, values)
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db.commit()
    except:
        db.rollback()


headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Connection': 'keep-alive',
    'X-Forwarded-For': random_ip(),
    'Client-IP': random_ip(),
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cookie': 'user_trace_token=20161216232858-d55af3950207433d8f7aa363ac9a76ff; LGUID=20161216232858-5d12c08d-c3a4-11e6-b15f-525400f775ce; index_location_city=%E4%B8%8A%E6%B5%B7; JSESSIONID=85628EFE21CD9ECA73F06627C0BCFF63; PRE_UTM=; PRE_HOST=; PRE_SITE=; PRE_LAND=https%3A%2F%2Fwww.lagou.com%2F; TG-TRACK-CODE=index_search; SEARCH_ID=01bfa35b8a9b447ba4affa7d18cfaf2a; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1486541112,1486998011; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1487817009; _ga=GA1.2.1703120497.1481902153; LGSID=20170223100713-ca95759c-f96c-11e6-8822-525400f775ce; LGRID=20170223103009-ff10c6ca-f96f-11e6-8829-525400f775ce'
}


def is_static_resource(url):
    if re.match('.(jpg|png|bmp|mp3|wma|wmv|gz|pdf|js|css|zip|rar|iso|pdf|txt|db)$', url):
        return True
    return False


def is_relative_path(url):
    if url.startswith('/'):
        return True
    return False


def complemented_url(seed, path):
    parts = urlparse.urlsplit(seed)
    url = '{0}://{1}{2}'.format(parts.scheme, parts.netloc, path)
    return url


def is_js_path(url):
    if url.startswith('javascript') or url.startswith('#'):
        return True
    return False


def ip2int(ip):
    o = map(int, ip.split('.'))
    return (o[0] << 24) + (o[1] << 16) + (o[2] << 8) + o[3]


def timestamp():
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def profile(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t1 = time.time()
        # call the method
        ret = func(*args, **kwargs)
        t2 = time.time()
        print("function      = {0}".format(func.__name__))
        print("    time      = %.6f sec" % (t2 - t1))
        return ret

    return wrapper


class Job(dict):
    def __init__(self, ctx=None):
        self.ctx = ctx
        self.company_id = ctx['companyId']
        self.position_id = ctx['positionId']
        self.url = 'https://www.lagou.com/jobs/{0}.html'.format(self.position_id)
        self.company_name = ctx['companyName']
        self.company_size = self.parse_company_size()
        self.position_name = ctx['positionName']
        self.city = ctx['city']
        self.salary = ctx['salary']
        self.parse_salary()
        self.work_year = ctx['workYear']
        self.parse_work_year()
        self.education = ctx['education']
        self.create_time = maya.parse(self.ctx['createTime']).iso8601()
        self.source = 'lagou'

    def parse_company_size(self):
        l = re.findall('\d+', self.salary)
        if len(l) == 0:
            return 0
        return reduce(lambda x, y: x + y, l) / len(l)

    def parse_salary(self):
        salaries = re.findall('\d+', self.salary)
        self.salary_min = salaries[0]
        self.salary_max = salaries[1]

    def parse_work_year(self):
        years = re.findall('\d+', self.work_year)
        if len(years) == 0:
            self.work_year_min = 0
            self.work_year_max = 0
        elif len(years) == 1:
            self.work_year_min = 0
            self.work_year_max = years[0]
        elif len(years) == 2:
            self.work_year_min = years[0]
            self.work_year_max = years[1]
        else:
            self.work_year_min = 0
            self.work_year_max = 0

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, name, value):
        self[name] = value

    def __str__(self):
        return "%s %s %s %s %s" % (self.company_name.encode('utf8'),
                                   self.city.encode('utf8'),
                                   self.position_name.encode('utf8'),
                                   self.salary.encode('utf8'),
                                   self.url.encode('utf8'))


# class Company(object):
#     def __init__(self):
#         self.location = None
#         self.jobs = []
#         self.scale = None
#         self.url = None
#         self.name = None
#
#     def parse_id(self):
#         return self.url.rsplit('/', 1)[1].split('.')[0]
#
#     def __str__(self):
#         return "%s %s %s" % (self.name.encode('utf8'), self.location.encode('utf8'), self.url.encode('utf8'))


# def parse_company(soup):
#     c = Company()
#     c.name = soup.find("a", attrs={"class": "item_title tj_exposure"}).text.strip()
#     c.url = soup.find("a", attrs={"class": "item_title tj_exposure"}).attrs['href'].strip()[2:]
#     c.location = soup.find("div", attrs={"class": "company_state"}).find("span",
#                                                                          attrs={"class": "fr place"}).text.strip()
#     c.scale = soup.find("div", attrs={"class": "company_state"}).find("span", attrs={"class": "type"}).text.strip()
#     return c


# def parse_companies(html):
#     companies = []
#     soup = BeautifulSoup(html)
#     lis = soup.find("div", attrs={"id": "company_list", "data-lg-tj-track-code": "gongsi_list"}).find_all("li")
#     for s in lis:
#         c = parse_company(s)
#         companies.append(c)
#     return companies


def parse_jobs(company_id):
    url = 'https://www.lagou.com/gongsi/searchPosition.json'
    payload = 'companyId={0}&positionFirstType=%E6%8A%80%E6%9C%AF&pageNo=1&pageSize=20'.format(company_id)
    r = requests.post(url, headers=headers, data=payload)
    if r.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(r.content)
        if encodings:
            r.encoding = encodings[0]
        else:
            r.encoding = r.apparent_encoding
    jobs = json.loads(r.text)['content']['data']['page']['result']
    return [Job(j) for j in jobs if j['city'] == u'无锡']


def parse_companies(url, pn):
    payload = 'first=false&pn={0}&sortField=0&havemark=0'.format(pn)
    r = requests.post(url, headers=headers, data=payload)
    if r.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(r.content)
        if encodings:
            r.encoding = encodings[0]
        else:
            r.encoding = r.apparent_encoding
    companies = json.loads(r.text)['result']
    return companies


if __name__ == '__main__':
    seed = 'https://www.lagou.com/gongsi/84-0-0.json'
    page_no = 1
    payload = 'first=false&pn={0}&sortField=0&havemark=0'.format(page_no)
    r = requests.post(seed, headers=headers, data=payload)
    page_size = json.loads(r.text)['pageSize']
    total_count = int(json.loads(r.text)['totalCount'])
    for pn in range(1, total_count/page_size+2):
        time.sleep(0.1)
        for c in parse_companies(seed, pn):
            for job in parse_jobs(c['companyId']):
                dump2mysql('t_job', job)
    db.close()
