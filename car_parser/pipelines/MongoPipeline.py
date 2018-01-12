import pymongo
from car_parser.settings import MONGO_URI, MONGO_DATABASE


class MongoPipeline(object):

    bucket_for_insert = []

    MAX_BUCKET_SIZE = 3000

    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DATABASE]

    def close_spider(self, spider):
        if len(self.bucket_for_insert) > 0:
            self.db[spider.collection_name].insert(self.bucket_for_insert)
            self.bucket_for_insert = []
        self.client.close()

    def process_item(self, item, spider):
        self.bucket_for_insert.append(dict(item))
        if len(self.bucket_for_insert) > self.MAX_BUCKET_SIZE:
            self.db[spider.collection_name].insert(self.bucket_for_insert)
            self.bucket_for_insert = []
        return item
