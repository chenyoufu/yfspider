# -*- coding: utf-8 -*-
import requests
import json

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'referer': 'https://www.zhihu.com/people/youfuchen/following/questions',
    'cookie': '_zap=c3d497e3-1130-4473-b4d7-7c803025edf3; d_c0="AJCCW1fBKgyPTt9jbyagVAGsiap22vtWdo8=|1501807685"; q_c1=8c40cd804a9b4f18bf909296b2d9e87d|1507342335000|1501763479000; _ga=GA1.2.656689896.1501807686; __DAYU_PP=Z6ZveBAFnfuYEjIBQJuV62e883c2719c; z_c0="2|1:0|10:1539856836|4:z_c0|92:Mi4xMGpFUkFBQUFBQUFBa0lKYlY4RXFEQ1lBQUFCZ0FsVk54S2UxWEFCSV9pTkpRMzh2SXlhUzV1SVVrSF91SjltUzl3|88bead565a70fb9834f3d68fe9e8e2820262b430554386c5f1e7d5ae4968f291"; tst=r; _xsrf=64a3080d-8d9c-4bc0-a3e3-7bd9a18547b2; oauth_from="/settings/account"; __utmc=51854390; __utmv=51854390.100-1|2=registration_date=20130723=1^3=entry_date=20130723=1; __utma=51854390.656689896.1501807686.1546937926.1547009186.2; __utmz=51854390.1547009186.2.2.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/search; q_c1=8c40cd804a9b4f18bf909296b2d9e87d|1547284797000|1501763479000; tgw_l7_route=8ffa4a0b7ecd9bdb5ad19b8c1037b063'
}


def init_login_session():
    login_data = {
        'password': '*',
        'remember_me': 'true',
        'email': 'youfu.ok@163.com'
    }
    s = requests.session()
    s.post('http://www.zhihu.com/login/email', data=login_data)
    return s


follows = {
    '100': [],
    '500': [],
    '1000': [],
}


questions = []


def delete_follow(s):
    qid = s.split('/')[-1]
    url = 'https://www.zhihu.com/api/v4/questions/{}/followers'.format(qid)
    r = requests.delete(url, headers=headers)
    print(r.status_code)


keywords = []


if __name__ == '__main__':
    # s = init_login_session()
    # s.headers.update(headers)
    offset = 0
    while True:
        query_string = "include=data%5B*%5D.created%2Canswer_count%2Cfollower_count&offset={offset}&limit=20".format(offset=offset)
        # print('xxxx', query_string)
        url = "https://www.zhihu.com/api/v4/members/youfuchen/following-questions?" + query_string
        print(url)
        r = requests.get(url, headers=headers)
        print(r.text)
        result = json.loads(r.text)
        if result['paging']['is_end']:
            break
        totals = result['paging']['totals']
        data = result['data']
        for d in data:
            d['url'] = d['url'].replace("questions", "question")
            questions.append(d)
            if d['answer_count'] < 50 or d['follower_count'] < 800:
                print(d['title'])
                delete_follow(d['url'])
            for k in keywords:
                if k in d['title']:
                    print(d['title'])
                    delete_follow(d['url'])
        offset += 20

    with open('./question.json', 'w') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
