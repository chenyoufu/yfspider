from bs4 import BeautifulSoup
import functools
import traceback
import requests
import urlparse
import url_redis
import time
import json
import re

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) Chrome/48.0.2564.116 Safari/537.36'
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
        'password': '********',
        'remember_me': 'true',
        'email': '********@163.com'
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
    more_followers_page = 'https://www.zhihu.com/node/ProfileFollowersListV2'
    more_followees_page = 'https://www.zhihu.com/node/ProfileFolloweesListV2'
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
        self.hash_id = self.init_hash_id()
        self.followers_page = homepage + '/followers'
        self.followees_page = homepage + '/followees'
        self.urls = set()
        self.init_user_info()

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
    def collect_followers(self):
        r = self.session.get(self.followers_page, timeout=5)
        self.urls |= self.fetch_a_href(r.text, class_='zg-link')
        self.update_session_cookie()
        self.urls |= self.more_followers()

    @profile
    def collect_followees(self):
        r = self.session.get(self.followees_page, timeout=5)
        self.urls |= self.fetch_a_href(r.text, class_='zg-link')
        self.update_session_cookie()
        self.urls |= self.more_followees()

    def more_followers(self):
        links = set()
        params = {'order_by': 'created', 'hash_id': self.hash_id}
        payload = {'_xsrf': self.xsrf_token, 'method': 'next'}
        for offset in xrange(20, self.followers, 20):
            params['offset'] = offset
            payload['params'] = json.dumps(params)
            r = self.session.post(self.more_followers_page, data=payload)
            page = ''.join(r.json()['msg'])
            links |= self.fetch_a_href(page, class_='zg-link')
        return links

    def more_followees(self):
        links = set()
        params = {'order_by': 'created', 'hash_id': self.hash_id}
        payload = {'_xsrf': self.xsrf_token, 'method': 'next'}
        for offset in xrange(20, self.followees, 20):
            params['offset'] = offset
            payload['params'] = json.dumps(params)
            r = self.session.post(self.more_followees_page, data=payload)
            page = ''.join(r.json()['msg'])
            links |= self.fetch_a_href(page, class_='zg-link')
        return links

    def update_session_cookie(self):
        self.session.cookies.pop('_xsrf')
        self.session.cookies.set('_xsrf', 'de861dca006eedd1f1bd19e41ab17825')

    @staticmethod
    def fetch_a_href(page, **kwargs):
        links = set()
        soup = BeautifulSoup(page, 'lxml')
        for link in soup.find_all('a', **kwargs):
            url = link.get('href')
            url and links.add(url)
        return links

    def init_hash_id(self):
        r = self.session.get(self.homepage+'/followers')
        soup = BeautifulSoup(r.text, 'lxml')
        data_init = soup.find('div', attrs={'data-init': True}).attrs['data-init']
        return json.loads(data_init)['params']['hash_id']


if __name__ == '__main__':
    ur = url_redis.UrlRedis(host='127.0.0.1', port=6379, db=0)
    s = init_login_session()
    urls = set()
    homepage = 'https://www.zhihu.com/people/chen-you-fu-27'
    ur.insert(homepage)

    homepage = ur.fetch(size=1)[0]
    zhihu_user = ZhihuUser(homepage, s)
    print zhihu_user.__dict__
    if zhihu_user.followers >= zhihu_user.followees:
        zhihu_user.collect_followers()
    else:
        zhihu_user.collect_followees()
    print len(zhihu_user.urls)
    for u in zhihu_user.urls:
        ur.insert(u)

