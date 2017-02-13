import pymongo
from SinaSpider.items import InformationItem,TweetsItem,RelationshipItem

class MongoDBPipleline(object):
    def __init__(self):
        client = pymongo.MongoClient("localhost",27017)
        db = client["Sina"]
        self.Information = db["Information"]
        self.Tweets = db["Tweets"]
        self.Relationships = db["Relationship"]

    def process_item(self,item,spider):
        if isinstance(item,InformationItem):
            try:
                self.Information.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item,TweetsItem):
            try:
                self.Tweets.insert(dict(item))
            except Exception:
                pass
        elif isinstance(item,RelationshipItem):
            try :
                self.Relationships.insert(dict(item))
            except Exception:
                pass
        return item

