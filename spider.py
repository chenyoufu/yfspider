from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Pool
import optparse
import url_redis
import fetch


def parse_options():
    usage = '''
                __           _     _
               / _|         (_)   | |
         _   _| |_ ___ _ __  _  __| | ___ _ __
        | | | |  _/ __| '_ \| |/ _` |/ _ \ '__|
        | |_| | | \__ \ |_) | | (_| |  __/ |
         \__, |_| |___/ .__/|_|\__,_|\___|_|
          __/ |       | |
         |___/        |_|
    '''

    parser = optparse.OptionParser(usage=usage)

    parser.add_option("-u", "--url",
                      dest="yfspider_url",
                      default='http://www.zhihu.com',
                      help='''Target URL (e.g. "http://www.site.com/")''')

    parser.add_option("-t", "--threads",
                      dest="yfspider_threads_num",
                      default=10,
                      help="Max number of concurrent HTTP(s) requests (default 10)")

    parser.add_option("--depth",
                      dest="yfspider_depth",
                      default=3,
                      help="Crawling depth")

    parser.add_option("--count",
                      dest="yfspider_count",
                      default=1000 * 1000,
                      help="Crawling number")

    parser.add_option("--time",
                      dest="yfspider_time",
                      default=3600 * 24 * 7,
                      help="Crawl time")

    parser.add_option("--focus-keyword",
                      dest="yfspider_focus_keyword",
                      default='',
                      help="Focus keyword in URL")

    parser.add_option("--filter-keyword",
                      dest="yfspider_filter_keyword",
                      default='',
                      help="Filter keyword in URL")

    parser.add_option("-q", "--quiet",
                  dest="verbose", default=True,
                  help="don't print status messages to stdout")

    (options, args) = parser.parse_args()
    print usage
    return options


if __name__ == '__main__':
    options = parse_options()
    #print options
    ur = url_redis.UrlRedis(host='127.0.0.1', port=6379, db=0)
    ur.insert(options.yfspider_url)
    seed = ur.fetch(size=1)
    urls = fetch.collect_urls(seed[0])
    print urls
    #pool = ThreadPool(options.yfspider_threads_num)
    #pool.map(urllib2.urlopen, urls)
    #pool.close()
    #pool.join()
