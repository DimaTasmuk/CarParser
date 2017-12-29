import pymongo
from car_parser.settings import AUTO_UNCLE_URI, AUTO_UNCLE_DATABASE


class AutoUnclePipeline(object):

    collection_name = 'autouncle_collection'

    def __init__(self):
        self.client = pymongo.MongoClient(AUTO_UNCLE_URI)
        self.db = self.client[AUTO_UNCLE_DATABASE]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item
