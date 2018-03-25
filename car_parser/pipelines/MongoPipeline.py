import random

import pymongo
from pymongo.errors import DuplicateKeyError

from car_parser.credentials import MONGO_URI, MONGO_DATABASE
from car_parser.spiders import AutoParser
from car_parser.spiders.autoscout import AutoScoutParser
from car_parser.spiders.autouncle import AutoUncleParser


class MongoPipeline(object):

    iteration_id = 0
    bucket_for_insert = []
    bucket_for_update = []

    MAX_BUCKET_SIZE = 200

    def __init__(self):
        # Set mongo connection string
        self.client = pymongo.MongoClient(MONGO_URI)
        self.mongodb = self.client[MONGO_DATABASE]

        self.collection = None

        # Get collection with iteration id
        self.iteration_collection = self.mongodb["Iteration"]

    def open_spider(self, spider):
        # Get collection for current spider
        self.collection = self.mongodb[spider.table_name]

        # Get current iteration id for such spider
        self.iteration_id = self.iteration_collection.find_one(
            {
                'site_name': spider.table_name
            },
            projection={'iteration_id': True, '_id': False}
        ).get('iteration_id', 0)

        print(self.iteration_id)
        self.iteration_id += 1
        print(self.iteration_id)

    # def process_item(self, item, spider):
    #     origin_link = item.get('origin_link')
    #     info = dict()
    #
    #     # Check if such car is already inside collection
    #     response = self.collection.find_one(
    #         {
    #             'origin_link': origin_link,
    #             'is_synced': 0
    #         },
    #         projection={'origin_link': True, 'is_synced': True}
    #     )
    #
    #     # TODO: add logger for error
    #     # try:
    #
    #     if response is None:
    #         info_update = dict()
    #
    #         if isinstance(spider, AutoParser):
    #             info_update = dict(spider.create_one_deep_request(origin_link))
    #         elif isinstance(spider, AutoUncleParser):
    #             info_update = dict(spider.create_one_deep_request(origin_link, item['model']))
    #         elif isinstance(spider, AutoScoutParser):
    #             info_update = dict(spider.create_deep_parse_request(
    #                 item['old_url'],
    #                 item['new_url'],
    #                 'update'
    #             ))
    #             for key, field in info_update.items():
    #                 if field is None or field == "":
    #                     info_update.pop(key)
    #
    #         # Add car description
    #         info.update(info_update)
    #         info['iteration_id'] = self.iteration_id
    #         info['is_synced'] = 0
    #
    #         self.bucket_for_insert.append(info)
    #         if len(self.bucket_for_insert) >= self.MAX_BUCKET_SIZE:
    #             try:
    #                 self.mongodb[spider.table_name].insert(self.bucket_for_insert)
    #                 self.bucket_for_insert = []
    #             except DuplicateKeyError:
    #                 self.bucket_for_insert = []
    #
    #         return info
    #     else:
    #         # update current iteration id for car
    #         self.bucket_for_update.append(item['origin_link'])
    #         if len(self.bucket_for_update) >= self.MAX_BUCKET_SIZE:
    #             try:
    #                 self.mongodb[spider.table_name].update(
    #                     {
    #                         'origin_link':
    #                         {
    #                             '$in': self.bucket_for_update
    #                         }
    #                     },
    #                     {
    #                         '$set':
    #                         {
    #                             'iteration_id': self.iteration_id
    #                         }
    #                     }
    #                 )
    #                 self.bucket_for_update = []
    #             except DuplicateKeyError:
    #                 self.bucket_for_update = []
    #
    #     # except ClientError as e:
    #     #     print('ERROR', e)
    #     # except Exception as e:
    #     #     print('ERROR', e)

    def process_item(self, item, spider):
        info = dict(item)

        info['iteration_id'] = self.iteration_id
        info['is_synced'] = 0

        self.bucket_for_insert.append(info)
        if len(self.bucket_for_insert) >= self.MAX_BUCKET_SIZE:
            try:
                self.mongodb[spider.table_name].insert(self.bucket_for_insert)
                self.bucket_for_insert = []
            except DuplicateKeyError:
                self.bucket_for_insert = []

    def close_spider(self, spider):
        if len(self.bucket_for_insert) > 0:
            self.mongodb[spider.table_name].insert(self.bucket_for_insert)
            self.bucket_for_insert = []

        # if len(self.bucket_for_update) >= 0:
        #     self.mongodb[spider.table_name].update(
        #         {
        #             'origin_link':
        #                 {
        #                     '$in': self.bucket_for_update
        #                 }
        #         },
        #         {
        #             'iteration_id': self.iteration_id
        #         }
        #     )
        #     self.bucket_for_update = []
        # self.iteration_collection.update(
        #                 {
        #                     'site_name': spider.table_name
        #                 },
        #                 {
        #                     '$set':
        #                     {
        #                         'iteration_id': self.iteration_id
        #                     }
        #                 }
        #             )
        self.client.close()
