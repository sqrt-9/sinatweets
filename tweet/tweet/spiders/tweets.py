import re
import pymongo
from datetime import datetime,timedelta
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from tweet.items import TweetsItem

class Spider(Spider):
    name = 'tweets'
    host = 'http://weibo.cn'
    weibo_db = pymongo.MongoClient('localhost').Weibo
    userid_collection = weibo_db.Information
    tweets_collection = weibo_db.Tweets
    start_urls_dict = userid_collection.find({},{'_id':1})
    start_urls = list(set([i['_id'] for i in start_urls_dict]))

    def start_requests(self):
        for uid in self.start_urls:
            yield Request(url='http://weibo.cn/{0}/profile?filter=1&page=1'.format(uid), callback=self.parse_tweets)

    def parse_tweets(self,response):
        flag = True
        selector = Selector(response)
        ID = re.findall('(\d+)/profile', response.url)[0]
        exsist_tweets_ID_dict = self.tweets_collection.find({'ID':ID},{'_id':1})
        exsist_tweets_ID = list(set(i['_id'].split('-')[1] for i in exsist_tweets_ID_dict))
        tweets = selector.xpath('body/div[@class="c" and @id]')
        for tweet in tweets:
            try:
                tweetsItems = TweetsItem()
                others = tweet.xpath('div/span[@class="ct"]/text()').extract_first()
                if others:
                    others = others.split(u'\u6765\u81ea')
                    pubtime = timeDispose(others[0].strip())
                    pubtime_list = [int(_) for _ in pubtime.replace('-',' ').replace(':',' ').split(' ')]
                    NewYear = [2017,1,1,0,0,0]
                    if compareTime(pubtime_list,NewYear):
                        id = tweet.xpath('@id').extract_first()
                        if id not in exsist_tweets_ID:
                            content = tweet.xpath('div/span[@class="ctt"]//text()').extract()
                            like = re.findall(u'\u8d5e\[(\d+)\]', tweet.extract())
                            tranfser = re.findall(u'\u8f6c\u53d1\[(\d+)\]', tweet.extract())
                            comment = re.findall(u'\u8bc4\u8bba\[(\d+)\]', tweet.extract())
                            tweetsItems["ID"] = ID
                            tweetsItems["_id"] = ID + "-" + id
                            if content:
                                tweetsItems["Content"] = " ".join(content).replace("\u200b","")
                            if like:
                                tweetsItems["Like"] = int(like[0])
                            if tranfser:
                                tweetsItems["Transfer"] = int(tranfser[0])
                            if comment:
                                 tweetsItems["Comment"] = int(comment[0])
                            tweetsItems["PubTime"] = pubtime
                            if len(others) == 2:
                                 tweetsItems['Tools'] = others[1]
                            yield tweetsItems
                    else:
                         flag = False
                         break
            except Exception as e:
                pass
        if flag:
            url_next = selector.xpath(u'body/div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()
            if url_next:
                page_num = int(url_next[0].split('&')[1].split('=')[1])
                yield Request(url=self.host + url_next[0], callback=self.parse_tweets)
                         


def timeDispose(n):
    if '月' in n:
        year = datetime.now().year
        month = int(n.split('月')[0])
        store = n.split('月')[1]
        day = int(store.split('日')[0])
        store = store.split('日')[1].strip()
        hour = int(store.split(':')[0])
        minute = int(store.split(':')[1])
        return datetime(year,month,day,hour,minute).strftime('%Y-%m-%d %H:%M:%S')
    elif '今天' in n:
        year = datetime.now().year
        month = datetime.now().month
        day = datetime.now().day
        store = n.split(' ')[1]
        hour = int(store.split(':')[0])
        minute = int(store.split(':')[1])
        return datetime(year,month,day,hour,minute).strftime('%Y-%m-%d %H:%M:%S')
    elif '分钟前' in n:
        minute = int(n.split('分')[0])
        return (datetime.now()-timedelta(minutes=minute)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        return n 

def compareTime(n,m):
    #函数用来比较两个日期的先后
    #参数为列表，存放年月日时秒分
    if datetime(n[0],n[1],n[2],n[3],n[4],n[5])>datetime(m[0],m[1],m[2],m[3],m[4],m[5]):
        return True
    else :
        return False

