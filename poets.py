# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import re


def parse_poet(html, encoding):
    soup = BeautifulSoup(html, from_encoding=encoding)
    title = soup.find("table", attrs={"width": "95%", "border": "0", "align": "center"}).text
    text = re.sub('\n[ \t]+', '\n', soup.find("blockquote").text)
    hrefs = soup.find("p", attrs={"align": "right"}).find_all('a')
    next_page = None
    if len(hrefs) == 3:
        next_page = hrefs[-1].get('href')
    return title, text, next_page


url = "http://www.eywedu.com/haizi/01/001.htm"

with open('haizi.txt', 'a') as mfile:
    while url is not None:
        r = requests.get(url)
        if r.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(r.content)
            if encodings:
                r.encoding = encodings[0]
            else:
                r.encoding = r.apparent_encoding

        poet = parse_poet(r.text, r.encoding)
        mfile.write(poet[0].encode('utf8'))
        mfile.write(poet[1].encode('utf8'))
        url = poet[2] and '/'.join(url.split('/')[0:-1]) + '/' + poet[2] or None
