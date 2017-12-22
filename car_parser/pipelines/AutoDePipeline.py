import pymongo
from car_parser.settings import MONGO_URI, MONGO_DATABASE


class AutoDePipeline(object):

    collection_name = 'auto_de_collection'

    def __init__(self):
        self.mongo_uri = MONGO_URI
        self.mongo_db = MONGO_DATABASE

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item