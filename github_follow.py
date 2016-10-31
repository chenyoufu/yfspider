# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import functools
import requests
import time
import sys


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


def parse_token(html):
    soup = BeautifulSoup(html)
    token = soup.find("input", attrs={"name": "authenticity_token"}).attrs["value"]
    return token


@profile
def login_session(user, password):
    us = requests.session()
    r = us.get("https://github.com/login")
    login_data = {
        "commit": "Sign in",
        "authenticity_token": parse_token(r.text),
        "login": user,
        "password": password,
    }
    r = us.post("https://github.com/session", data=login_data, allow_redirects=True)
    if r.status_code == 200:
        return us
    else:
        print "login failed"
        sys.exit(0)


def get_context(form):
    soup = BeautifulSoup(form)
    action = soup.find("form").attrs["action"]
    token = parse_token(form)
    return action, token


@profile
def get_pages(username, tab="followers"):
    url = "https://github.com/{0}".format(username)
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    href = "/{0}?tab={1}".format(username, tab)
    tmp = soup.find("a", attrs={"href": href}).find("span").text.strip()
    c = 0
    if tmp[-1] == 'k':
        c = int(round(float(tmp[:-1]) * 1000))
    else:
        c = int(tmp)
    page_size = 51
    pages = c / page_size
    if c % page_size != 0:
        pages += 1
    return pages


@profile
def get_pages_api(username, tab):
    url = "https://api.github.com/users/{0}".format(username)
    r = requests.get(url)
    if r.status_code == 403:
        return get_pages(username, tab)
    c = r.json()[tab]
    page_size = 51
    pages = c / page_size
    if c % page_size != 0:
        pages += 1
    return pages


@profile
def get_user_api(username):
    url = "https://api.github.com/users/{0}".format(username)
    r = requests.get(url)
    return r.json()


def fucking(request_session, start_user, action):
    page_num = get_pages_api(start_user, "followers")
    for i in range(1, page_num):
        url = "https://github.com/{0}?page={1}&tab=followers".format(start_user, i)
        r = request_session.get(url)
        soup = BeautifulSoup(r.text)
        forms = soup.find_all("form", attrs={"data-remote": "true"})
        print "{0} page {1} forms count: {2}".format(start_user, i, len(forms))
        ctx = map(lambda x: get_context(x.encode()), forms)
        for cx in ctx:
            cx[0].startswith("/users/" + action) and follow(s, cx[0], cx[1])


def follow(request_session, action, token):
    url = "https://github.com/{0}".format(action)
    follow_data = {
        "authenticity_token": token
    }
    r = request_session.post(url, data=follow_data)
    print action, r.status_code


def check_args():
    if len(sys.argv) < 4:
        print "github_follow.py <login> <pw> <follow|unfollow> <seed>"
        sys.exit(0)
    if sys.argv[3] not in ["follow", "unfollow"]:
        print "The third param must be 'follow' or 'unfollow'"
        sys.exit(0)


if __name__ == '__main__':
    check_args()
    s = login_session(sys.argv[1], sys.argv[2])
    fucking(s, sys.argv[4], sys.argv[3])
