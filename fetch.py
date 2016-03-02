from bs4 import BeautifulSoup
import traceback
import requests
import urlparse
import time
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) Chrome/48.0.2564.116 Safari/537.36'
}


def is_static_resource(url):
    if re.match('.(jpg|png|bmp|mp3|wma|wmv|gz|pdf|js|css|zip|rar|iso|pdf|txt|db)$', url):
        return True
    return False


def is_relative_path(url):
    if url.startswith('/'):
        return True
    return False


def is_js_path(url):
    if url.startswith('javascript'):
        return True
    return False


def ip2int(ip):
    o = map(int, ip.split('.'))
    return (o[0] << 24) + (o[1] << 16) + (o[2] << 8) + o[3]


def timestamp():
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def fetch_a_href(soup):
    links = set()
    for link in soup.find_all('a'):
        url = link.get('href')
        url and links.add(url)
    return links


def collect_urls(seed):
    try:
        s = requests.Session()
        r = s.get(seed, headers=headers, timeout=5, allow_redirects=False)
    except requests.exceptions.RequestException as e:
        traceback.print_exc()
        return
    soup = BeautifulSoup(r.text, 'lxml')
    urls = set()
    urls |= fetch_a_href(soup)
    return urls









