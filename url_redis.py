import redis


class UrlRedis(object):
    def __init__(self, host, port, db):
        self.rc = redis.StrictRedis(host=host, port=port, db=db)
        self.pipe = self.rc.pipeline()
        self.url_sets = 'url:parsed'
        self.url_lists = 'url:queue'

    def insert(self, url):
        self.rc.sadd(self.url_sets, url) and self.rc.rpush(self.url_lists, url)

    def fetch(self, size=1):
        for i in range(size):
            self.pipe.lpop(self.url_lists)
        return self.pipe.execute()


if __name__ == '__main__':
    ur = UrlRedis(host='127.0.0.1', port=6379, db=0)
    ur.insert('cc')
    ur.insert('aaa')
    ur.insert('bbb')
    ur.insert('b')
    print ur.fetch(2)