# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import functools
import requests
import time
import re
import urlparse


url = 'https://www.lagou.com/gongsi/84-0-0'

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
        print("    time      = %.6f sec" % (t2-t1))
        return ret
    return wrapper


class Company(object):
    def __init__(self):
        self.pay = None
        self.location = None
        self.jobs = 0
        self.scale = None
        self.url = None
        self.name = None

    def __str__(self):
        return "%s %s %s %s" % (self.name.encode('utf8'), self.location.encode('utf8'), self.pay, self.url.encode('utf8'))


def parse_company(soup):
    c = Company()
    c.name = soup.find("a", attrs={"class": "item_title tj_exposure"}).text.strip()
    c.url = soup.find("a", attrs={"class": "item_title tj_exposure"}).attrs['href'].strip()[2:]
    c.location = soup.find("div", attrs={"class": "company_state"}).find("span", attrs={"class": "fr place"}).text.strip()
    c.scale = soup.find("div", attrs={"class": "company_state"}).find("span", attrs={"class": "type"}).text.strip()
    c.jobs = soup.find("div", attrs={"class": "sub_title"}).find_all("span")[1].text.strip()
    return c


def parse_companies(html):
    companies = []
    soup = BeautifulSoup(html)
    lis = soup.find("div", attrs={"id": "company_list", "data-lg-tj-track-code": "gongsi_list"}).find_all("li")
    for s in lis:
        c = parse_company(s)
        companies.append(c)
    return companies


if __name__ == '__main__':

    r = requests.get(url, headers=headers)
    if r.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(r.content)
        if encodings:
            r.encoding = encodings[0]
        else:
            r.encoding = r.apparent_encoding

    for c in parse_companies(r.text):
        print c
