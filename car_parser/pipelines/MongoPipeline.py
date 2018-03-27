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
    bucket_of_items_to_process = []

    MAX_BUCKET_SIZE = 2000

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

    def process_item(self, item, spider):
        try:
            self.bucket_of_items_to_process.append(item)

            if len(self.bucket_of_items_to_process) >= self.MAX_BUCKET_SIZE:
                self.process_items_bucket(spider)
                self.bucket_of_items_to_process = []
            return item
        except Exception as e:
            print(e.message)

    def process_items_bucket(self, spider):
        bucket_of_origin_links = []
        for item in self.bucket_of_items_to_process:
            bucket_of_origin_links.append(item.get('origin_link'))

        # Check if such car is already inside collection
        response = self.collection.find(
            {
                'origin_link':
                {
                    '$in': bucket_of_origin_links
                },
            },
            projection=
            {
                '_id': False,
                'origin_link': True,
                'is_synced': True,
                'sales_price_incl_vat': True
            }
        )
        already_added_cars = []
        already_added_cars_origin_links = []
        for car in response:
            already_added_cars.append(car)
            already_added_cars_origin_links.append(car['origin_link'])

        for item in self.bucket_of_items_to_process:
            try:
                index = already_added_cars_origin_links.index(item['origin_link'])
                item['is_price_changed'] = (item['sales_price_incl_vat'] != already_added_cars[index]['sales_price_incl_vat'])
                self.process_added_items(item, spider)
            except ValueError:
                self.process_new_items(item, spider)
            except Exception as e:
                print(e.message)

    def process_new_items(self, item, spider):
        origin_link = item['origin_link']
        info = dict()
        info_update = dict()

        if isinstance(spider, AutoParser):
            info_update = dict(spider.create_one_deep_request(origin_link))
        elif isinstance(spider, AutoUncleParser):
            info_update = dict(spider.create_one_deep_request(origin_link, item['model']))
        elif isinstance(spider, AutoScoutParser):
            info_update = dict(spider.create_deep_parse_request(
                item['old_url'],
                item['new_url'],
                'update'
            ))
            for key, field in info_update.items():
                if field is None or field == "":
                    info_update.pop(key)

        # Add car description
        info.update(info_update)
        info['iteration_id'] = self.iteration_id
        info['is_synced'] = 0

        self.bucket_for_insert.append(info)
        if len(self.bucket_for_insert) >= self.MAX_BUCKET_SIZE:
            try:
                self.mongodb[spider.table_name].insert(self.bucket_for_insert)
                self.bucket_for_insert = []
            except DuplicateKeyError:
                self.bucket_for_insert = []

        return info

    def process_added_items(self, item, spider):
        origin_link = item.get('origin_link')

        # update current iteration id for car
        if item['is_price_changed']:
            self.mongodb[spider.table_name].update(
                {
                    'origin_link': origin_link
                },
                {
                    '$set':
                        {
                            'iteration_id': self.iteration_id,
                            'is_synced': 0,
                            'sales_price_incl_vat': item['sales_price_incl_vat']
                        }
                }
            )
            return {
                "origin_link": origin_link,
                "information": "Updated car price"
            }
        else:
            self.bucket_for_update.append(origin_link)
            if len(self.bucket_for_update) >= self.MAX_BUCKET_SIZE:
                try:
                    self.mongodb[spider.table_name].update(
                        {
                            'origin_link':
                            {
                                '$in': self.bucket_for_update
                            }
                        },
                        {
                            '$set':
                            {
                                'iteration_id': self.iteration_id
                            }
                        },
                        multi=True
                    )
                    self.bucket_for_update = []
                except DuplicateKeyError:
                    self.bucket_for_update = []
            return {
                "origin_link": origin_link,
                "information": "Already in database"
            }
        # except ClientError as e:
        #     print('ERROR', e)
        # except Exception as e:
        #     print('ERROR', e)

    def close_spider(self, spider):
        if len(self.bucket_of_items_to_process) > 0:
            self.process_items_bucket(spider)
            self.bucket_of_items_to_process = []

        if len(self.bucket_for_insert) > 0:
            self.mongodb[spider.table_name].insert(self.bucket_for_insert)
            self.bucket_for_insert = []

        if len(self.bucket_for_update) > 0:
            self.mongodb[spider.table_name].update(
                {
                    'origin_link':
                        {
                            '$in': self.bucket_for_update
                        }
                },
                {
                    '$set':
                        {
                            'iteration_id': self.iteration_id
                        }
                },
                multi=True
            )
            self.bucket_for_update = []
        self.iteration_collection.update(
                        {
                            'site_name': spider.table_name
                        },
                        {
                            '$set':
                            {
                                'iteration_id': self.iteration_id
                            }
                        }
                    )
        self.client.close()
