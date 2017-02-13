from scrapy_redis.spiders import RedisSpider
from Weibo.weiboID import weiboID
from scrapy.http import Request
import re
import requests
import logging
from lxml import etree
from Weibo.items import InformationItem
from datetime import datetime,timedelta
from scrapy.selector import Selector

class Spider(RedisSpider):
    name = 'weibo'
    host = 'http://weibo.cn'
    start_urls = list(set(weiboID))
    logging.getLogger("requests").setLevel(logging.WARNING)  #将requests的日志级别设成WARNING

    def start_requests(self):
        for uid in self.start_urls:
            yield Request(url='http://weibo.cn/{0}/profile'.format(uid), callback=self.parse_active, priority=4)

    def parse_active(self,response):
        """判断是否是活跃用户"""
        selector = Selector(response)
        ID = re.findall('(\d+)/profile',response.url)[0]
        tweets = selector.xpath('body/div[@class="c" and @id]')
        if len(tweets)>=10:
            others = tweets[0].xpath('div/span[@class="ct"]/text()').extract_first()
            first_tweet_time = timeDispose(others.split("来自")[0].strip())
            first_tweet_time = [int(_) for _ in first_tweet_time.replace("-"," ").replace(":"," ").split(" ")]
            others = tweets[1].xpath('div/span[@class="ct"]/text()').extract_first()
            second_tweet_time = timeDispose(others.split("来自")[0].strip())
            second_tweet_time = [int(_) for _ in second_tweet_time.replace("-"," ").replace(":"," ").split(" ")]
            if compareTime(first_tweet_time,second_tweet_time):
                recent_time = first_tweet_time
            else:
                recent_time = second_tweet_time
            check_time = [2016,9,30,0,0,0]
            if compareTime(recent_time,check_time):
                yield Request(url="http://weibo.cn/{0}/info".format(ID), callback=self.parse_information, priority=3)

    def parse_information(self,response):
        """抓取个人信息"""
        informationItems = InformationItem()
        selector = Selector(response)
        ID = re.findall('(\d+)/info',response.url)[0]
        try:
            text1 = ";".join(selector.xpath('body/div[@class="c"]/text()').extract())  #获取标签里的所有text()
            nickname = re.findall(u'\u6635\u79f0[:|\uff1a](.*?);', text1)  #昵称
            gender = re.findall(u'\u6027\u522b[:|\uff1a](.*?);', text1)  #性别
            place = re.findall(u'\u5730\u533a[:|\uff1a](.*?);', text1)  #地区（包括省份和城市）
            briefIntroduction = re.findall(u'\u7b80\u4ecb[:|\uff1a](.*?);', text1)  #个人简介
            authentication = re.findall(u'\u8ba4\u8bc1[:|\uff1a](.*?);', text1)  #认证
            url = re.findall(u'\u4e92\u8054\u7f51[:|\uff1a](.*?);', text1)  #首页链接

            informationItems['_id'] = ID
            if nickname and nickname[0]:
                informationItems["NickName"] = nickname[0]
            if gender and gender[0]:
                informationItems["Gender"] = gender[0]
            if place and place[0]:
                place = place[0].split(" ")
                informationItems["Province"] = place[0]
                if len(place) > 1:
                    informationItems["City"] = place[1]
            if briefIntroduction and briefIntroduction[0]:
                informationItems["BriefIntroduction"] = briefIntroduction[0]
            if authentication and authentication[0]:
                informationItems["Authentication"] = authentication[0]
            if url:
                informationItems["URL"] = url[0]

            try:
                urlothers = "http://weibo.cn/attgroup/opening?uid={0}".format(ID)
                r = requests.get(url=urlothers, cookies=response.request.cookies, timeout=2)
                if r.status_code == 200:
                    selector = etree.HTML(r.content)
                    texts = ";".join(selector.xpath('//body//div[@class="tip2"]/a//text()')) 
                    if texts:
                        num_tweets = re.findall(u'\u5fae\u535a\[(\d+)\]', texts)  #微博数
                        num_follows = re.findall(u'\u5173\u6ce8\[(\d+)\]', texts)  #关注数
                        num_fans = re.findall(u'\u7c89\u4e1d\[(\d+)\]', texts)  #粉丝数
                        if num_tweets:
                            informationItems['Num_Tweets'] = int(num_tweets[0])
                        if num_follows:
                            informationItems['Num_Follows'] = int(num_follows[0])
                        if num_fans:
                            informationItems['Num_Fans'] = int(num_fans[0])
            except Exception as e:
                pass

        except Exception as e:
            pass
        else:
            yield informationItems
            yield Request(url="http://weibo.cn/{0}/follow".format(ID), callback=self.parse_relationship, dont_filter=True,priority=1)
            yield Request(url="http://weibo.cn/{0}/fans".format(ID), callback=self.parse_relationship, dont_filter=True,priority=0)

    def parse_relationship(self,response):
        selector = Selector(response)
        if "follow" in response.url:
            ID = re.findall('(\d+)/follow', response.url)[0]
            if ID:
                urls = selector.xpath(u'body//table/tr/td/a[text()="\u5173\u6ce8\u4ed6" or text()="\u5173\u6ce8\u5979"]/@href').extract()
                uids = re.findall('uid=(\d+)', ";".join(urls), re.S)
                for uid in uids:
                    yield Request(url="http://weibo.cn/{0}/profile".format(uid), callback=self.parse_active, priority=2)
                url_next = selector.xpath(u'body//div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()
                if url_next:
                    yield Request(url=self.host+url_next[0], callback=self.parse_relationship,dont_filter=True,priority=1)
        elif "fans" in response.url:
            ID = re.findall('(\d+)/fans', response.url)[0]
            if ID:
                urls = selector.xpath(u'body//table/tr/td/a[text()="\u5173\u6ce8\u4ed6" or text()="\u5173\u6ce8\u5979"]/@href').extract()
                uids = re.findall('uid=(\d+)', ";".join(urls), re.S)
                for uid in uids:
                    yield Request(url="http://weibo.cn/{0}/profile".format(uid), callback=self.parse_active, priority=2)
                url_next = selector.xpath(u'body//div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()
                if url_next:
                    yield Request(url=self.host+url_next[0], callback=self.parse_relationship,dont_filter=True, priority=0)

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

