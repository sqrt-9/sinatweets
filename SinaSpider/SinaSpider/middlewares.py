# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

import os
import redis
import json
import logging
import random
from datetime import datetime,timedelta
from scrapy import signals
from SinaSpider.cookies import initCookie,updateCookie,removeCookie
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import response_status_message
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from SinaSpider.user_agents import agents

logger = logging.getLogger(__name__)

a = set()  #存跟新过的cookie
before_time = 0
next_time = 0

class UserAgentMiddleware(object):
    """ CHANGE USER-AGENT """
    def process_request(self,request,spider):
        agent = random.choice(agents)
        request.headers["User-Agent"] = agent


class CookiesMiddleware(RetryMiddleware):
    """ CHANGE COOKIE """
    def __init__(self, settings, crawler):
        RetryMiddleware.__init__(self, settings)
        self.rconn = settings.get("RCONN", redis.Redis(crawler.settings.get('REDIS_HOST', 'localhost'), crawler.settings.get('REDIS_PORT', 6379)))
        initCookie(self.rconn, crawler.spider.name)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler)

    def process_request(self, request, spider):
        redisKeys = self.rconn.keys()
        while len(redisKeys) > 0:
            elem = bytes.decode(random.choice(redisKeys))
            if "SinaSpider:Cookies" in elem:
                cookie = json.loads(bytes.decode(self.rconn.get(elem)))
                request.cookies = cookie
                request.meta["accountText"] = elem.split("Cookies:")[-1]
                break
            else:
                try:
                    redisKeys.remove(elem)
                except Exception as e:
                    pass

    def process_response(self, request, response, spider):
        global a,before_time,next_time
        if response.status in [300,301,302,303]:
            try:
                redirect_url =  bytes.decode(response.headers["location"])
                if "login.weibo" in redirect_url or "login.sina" in redirect_url:
                    if len(a) == 5:
                        if not before_time:
                            before_time = datetime.now()
                        next_time = datetime.now()
                        time = (next_time - before_time).total_seconds()
                        before_time = next_time
                        if time > 3600:
                            a.clear()
                    if request.meta["accountText"] not in a:
                        a.add(request.meta["accountText"])
                        logger.warning("One Cookie need to be updating...")
                        updateCookie(request.meta['accountText'], self.rconn, spider.name)
                elif "weibo.cn/security" in redirect_url:
                    logger.warning("One Account is locked! Remove it!")
                    removeCookie(request.meta["accountText"], self.rconn, spider.name)
                elif "weibo.cn/pub" in redirect_url:
                    logger.warning(
                            "Redirect to 'http://weibo.cn'! (Account:{0})".format(request.meta["accountText"].split('--')[0])
                            )
                reason = response_status_message(response.status)
                return self._retry(request, reason, spider) or response
            except Exception as e:
                raise IgnoreRequest
        elif response.status in [403,414]:
            logger.error("{0}! Stopping...".format(response.status))
            os.system("echo Press enter to continue; read dummy;")
        else:
            return response


class SinaspiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
