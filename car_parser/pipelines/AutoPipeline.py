import pymongo
from car_parser.settings import AUTO_URI, AUTO_DATABASE


class AutoPipeline(object):

    collection_name = 'auto_collection'

    def __init__(self):
        self.client = pymongo.MongoClient(AUTO_URI)
        self.db = self.client[AUTO_DATABASE]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item
