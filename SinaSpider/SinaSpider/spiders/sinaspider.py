import re
import requests
import logging
from lxml import etree
from SinaSpider.weiboID import weiboID
from datetime import datetime,timedelta
from scrapy_redis.spiders import RedisSpider
from scrapy.selector import Selector
from scrapy.http import Request
from SinaSpider.items import InformationItem,TweetsItem,RelationshipItem

class Spider(RedisSpider):
    name = "SinaSpider"
    redis_key = 'SinaSpider:start_urls'
    host = "http://weibo.cn"
    start_urls = list(set(weiboID))
    logging.getLogger("requests").setLevel(logging.WARNING)  #将requests的日志级别设成WARNING

    def start_requests(self):
        for uid in self.start_urls:
            yield Request(url="http://weibo.cn/{0}/info".format(uid), callback=self.parse_information)

    def parse_information(self,response):
        """抓取个人信息1"""
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
                r = requests.get(url=urlothers, cookies=response.request.cookies, timeout=1)
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
        yield Request(url="http://weibo.cn/{0}/profile?filter=1&page=1".format(ID), callback=self.parse_tweets, dont_filter=True)
        yield Request(url="http://weibo.cn/{0}/follow".format(ID), callback=self.parse_relationship, dont_filter=True)
        yield Request(url="http://weibo.cn/{0}/fans".format(ID), callback=self.parse_relationship, dont_filter=True)

    def parse_tweets(self,response):
        """抓取微博数据"""
        selector = Selector(response)
        ID = re.findall('(\d+)/profile', response.url)[0]
        tweets = selector.xpath('body/div[@class="c" and @id]')
        for tweet in tweets:
            try:
                tweetsItems = TweetsItem()
                id = tweet.xpath('@id').extract_first()  #微博ID
                content = tweet.xpath('div/span[@class="ctt"]//text()').extract()  #微博内容
                like = re.findall(u'\u8d5e\[(\d+)\]', tweet.extract())  #点赞数
                tranfser = re.findall(u'\u8f6c\u53d1\[(\d+)\]', tweet.extract())  #转载数
                comment = re.findall(u'\u8bc4\u8bba\[(\d+)\]', tweet.extract())  #评论数
                others = tweet.xpath('div/span[@class="ct"]/text()').extract_first()  #时间和使用工具（手机或平台）
                tweetsItems["ID"] = ID
                tweetsItems["_id"] = ID + "-" + id
                if content:
                    tweetsItems["Content"] = " ".join(content).replace("\u200b","").replace("건","").replace("🍗","")
                if like:
                    tweetsItems["Like"] = int(like[0])
                if tranfser:
                    tweetsItems["Transfer"] = int(tranfser[0])
                if comment:
                    tweetsItems["Comment"] = int(comment[0])
                if others:
                    others = others.split(u"\u6765\u81ea")
                    tweetsItems["PubTime"] = timeDispose(others[0].strip())
                    if len(others) == 2:
                        tweetsItems["Tools"] = others[1]
                yield tweetsItems
            except Exception as e:
                pass

        url_next = selector.xpath(u'body/div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()
        if url_next:
            page_num = int(url_next[0].split('&')[1].split('=')[1])
            if not page_num>10:
                yield Request(url=self.host + url_next[0], callback=self.parse_tweets, dont_filter=True)
    
    def parse_relationship(self,response):
        """抓取关注或粉丝"""
        selector = Selector(response)
        if "/follow" in response.url:
            ID = re.findall('(\d+)/follow', response.url)[0]
            flag = True
        elif "/fans" in response.url:
            ID = re.findall('(\d+)/fans', response.url)[0]
            flag = False
        else:
            ID = None
        if ID:
            urls = selector.xpath(u'body//table/tr/td/a[text()="\u5173\u6ce8\u4ed6" or text()="\u5173\u6ce8\u5979"]/@href').extract()
            uids = re.findall('uid=(\d+)', ";".join(urls), re.S)
            for uid in uids:
                relationshipItem = RelationshipItem()
                relationshipItem['Host1'] = ID if flag else uid
                relationshipItem['Host2'] = uid if flag else ID
                yield relationshipItem
                yield Request(url="http://weibo.cn/{0}/info".format(uid), callback=self.parse_information)


            url_next = selector.xpath(u'body//div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()
            if url_next:
                yield Request(url=self.host + url_next[0], callback=self.parse_relationship, dont_filter=True)

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
