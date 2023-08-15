# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
from .items import WikiItem



class WikiMongoDBPipeline:

    def __init__(self):
        self.mongodb_uri = 'mongodb://localhost:27017/'
        self.mongodb_db = 'wiki'
        self.data_collection = 'wiki_math' 

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongodb_uri)
        self.db = self.client[self.mongodb_db]
        # # Start with a clean database
        self.db[self.data_collection].delete_many({})

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):

        data = dict(WikiItem(item))
        self.db[self.data_collection].update_one({"key": data["key"]}, {"$set": data}, upsert=True)

        return item
    
