from bs4 import BeautifulSoup
from multiprocessing import Pool
import functools
import traceback
import grequests
import requests
import urlparse
import psutil
import url_redis
import time
import json
import re

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh) Chrome/48.0.2564.116 Safari/537.36'
}

proxies = {
    'http': 'http://127.0.0.1:8080',
    'https': 'http://127.0.0.1:8080'
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


def fetch_a_href_bak(page, seed='', **kwargs):
    links = set()
    soup = BeautifulSoup(page, 'lxml')
    for link in soup.find_all('a', **kwargs):
        url = link.get('href')
        if url and is_js_path(url):
            continue
        url = url and is_relative_path(url) and complemented_url(seed, url) or url
        url and links.add(url)
    return links


def collect_urls(seed, payload=None, session=None):
    try:
        s = session or requests.Session()
        s.headers.update(headers)
        r = payload and s.post(seed, data=payload, timeout=5) or s.get(seed, timeout=5)
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return
    urls = set()
    urls |= fetch_a_href_bak(r.text, seed)
    return urls


def get_xsrf_token(page):
    soup = BeautifulSoup(page, 'lxml')
    xt = soup.find('input', attrs={"name": "_xsrf"}).attrs['value']
    return xt


def init_login_session():
    login_data = {
        'password': '*',
        'remember_me': 'true',
        'email': 'youfu.ok@163.com'
    }
    s = requests.session()
    s.post('http://www.zhihu.com/login/email', data=login_data)
    return s


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


class ZhihuUser(object):
    xsrf_token = 'de861dca006eedd1f1bd19e41ab17825'

    def __init__(self, homepage, session):
        self.homepage = homepage
        self.session = session
        self.followers = 0
        self.followees = 0
        self.agrees = 0
        self.thanks = 0
        self.nickname = None
        self.avatar = None
        self.resp_429 = 0
        self.resp_err = 0
        self.collect_page = None
        self.hash_id = self.init_hash_id()
        self.followers_page = homepage + '/followers'
        self.followees_page = homepage + '/followees'
        self.dup_urls = 0
        self.init_user_info()
        self.ur = url_redis.UrlRedis()

    def init_user_info(self):
        url_token = homepage.split('/')[-1]
        r = self.session.get(homepage)
        soup = BeautifulSoup(r.text, 'lxml')
        self.agrees = int(soup.find('span', class_="zm-profile-header-user-agree").find('strong').text)
        self.thanks = int(soup.find('span', class_="zm-profile-header-user-thanks").find('strong').text)
        self.followees = int(soup.find('a', href="/people/{0}/followees".format(url_token)).find('strong').text)
        self.followers = int(soup.find('a', href="/people/{0}/followers".format(url_token)).find('strong').text)
        self.nickname = soup.find('a', class_="zu-top-nav-userinfo").find('span', class_="name").text
        self.avatar = soup.find('img', class_="Avatar Avatar--l").attrs['src']

    @profile
    def collect_people(self):
        self.collect_page = self.followers_page if self.followers >= self.followees else self.followees_page
        r = self.session.get(self.collect_page, timeout=5)
        links = self.fetch_a_href(r.text, class_='zg-link')
        for l in links:
            if not self.ur.insert(l):
                self.dup_urls += 1
        self.update_session_cookie()
        #self.more_people_async2()
        self.more_people()

    @staticmethod
    def exception_handler(request, exception):
        print "Request failed" + str(exception)

    def dump_more_people(self, r):
        if r.status_code == 200:
            page = ''.join(r.json()['msg'])
            links = self.fetch_a_href(page, class_='zg-link')
            for l in links:
                if not ur.insert(l):
                    self.dup_urls += 1
        elif r.status_code == 429:
            self.resp_429 += 1
        else:
            self.resp_err += 1

    def more_people_async(self):
        if self.hash_id:
            params = {'order_by': 'created', 'hash_id': self.hash_id}
            payload = {'_xsrf': self.xsrf_token, 'method': 'next'}
            size = self.followers if self.followers >= self.followees else self.followees
            url = "https://www.zhihu.com/node/ProfileFollowe{0}sListV2"
            url = url.format('r') if self.followers >= self.followees else url.format('e')
            reqs = []
            for offset in xrange(20, size, 20):
                params['offset'] = offset
                payload['params'] = json.dumps(params)
                reqs.append(grequests.post(url, data=payload.copy(), session=self.session))
            resps = grequests.map(reqs, size=8, exception_handler=self.exception_handler)
            for resp in resps:
                self.dump_more_people(resp)

    def more_people_async2(self):
        resps = grequests.map(self.more_people_async_g(), size=8, exception_handler=self.exception_handler)
        for resp in resps:
            self.dump_more_people(resp)

    def more_people_async_g(self):
        url = "https://www.zhihu.com/node/ProfileFollowe{0}sListV2"
        url = url.format('r') if self.followers >= self.followees else url.format('e')
        for payload in self.more_people_payloads():
            yield grequests.post(url, data=payload.copy(), session=self.session)

    def more_people_payloads(self):
        if self.hash_id:
            params = {'order_by': 'created', 'hash_id': self.hash_id}
            payload = {'_xsrf': self.xsrf_token, 'method': 'next'}
            size = self.followers if self.followers >= self.followees else self.followees
            for offset in xrange(20, size, 20):
                params['offset'] = offset
                payload['params'] = json.dumps(params)
                yield payload

    @profile
    def more_people(self):
            url = "https://www.zhihu.com/node/ProfileFollowe{0}sListV2"
            url = url.format('r') if self.followers >= self.followees else url.format('e')
            for payload in self.more_people_payloads():
                try:
                    t1 = time.time()
                    r = self.session.post(url, data=payload, timeout=10)
                    t2 = time.time()
                    print t2 - t1
                    self.dump_more_people(r)
                except requests.exceptions.ReadTimeout as e:
                    print 'Request {0} {1} timeout'.format(url, payload)
                    continue

    def update_session_cookie(self):
        self.session.cookies.pop('_xsrf')
        self.session.cookies.set('_xsrf', self.xsrf_token)

    @staticmethod
    def fetch_a_href(page, **kwargs):
        soup = BeautifulSoup(page, 'lxml')
        links = map(lambda a: a.get('href'), soup.find_all('a', **kwargs))
        return links

    def init_hash_id(self):
        r = self.session.get(self.homepage+'/followers')
        soup = BeautifulSoup(r.text, 'lxml')
        try:
            data_init = soup.find('div', attrs={'data-init': True}).attrs['data-init']
            return json.loads(data_init)['params']['hash_id']
        except AttributeError as e:
            print str(e)
            print r.text
            return


def task(name):
    while True:
        dup_urls = 0
        homepage = ur.fetch(size=1)[0]
        #homepage = ur.dummy_fetch()[0][0]
        print homepage
        zhihu_user = ZhihuUser(homepage, s)
        print 'followers: ', zhihu_user.__dict__['followers']
        print 'followees: ', zhihu_user.__dict__['followees']
        zhihu_user.collect_people()
        print 'resp_429: ', zhihu_user.resp_429
        print 'resp_err: ', zhihu_user.resp_err
        print 'redis set dup urls: ', zhihu_user.dup_urls



if __name__ == '__main__':
    ur = url_redis.UrlRedis()
    s = init_login_session()
    #s.proxies = proxies
    s.headers.update(headers)
    homepage = 'https://www.zhihu.com/people/chen-you-fu-27'
    ur.insert(homepage)
    p = Pool()
    for i in range(psutil.cpu_count()):
        p.apply_async(task, args=('sipder{0}'.format(i),))
    print 'Waiting for all subprocesses done...'
    p.close()
    p.join()
    print 'All subprocesses done.'


