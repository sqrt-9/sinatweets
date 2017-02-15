# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from Weibo.items import InformationItem

class MongoDBPipleline(object):
    def __init__(self):
        client = pymongo.MongoClient("localhost",27017)
        db = client["Weibo"]
        self.Information = db["Information"]

    def process_item(self,item,spider):
        if isinstance(item,InformationItem):
            try:
                self.Information.insert(dict(item))
            except Exception:
                pass
        return item

