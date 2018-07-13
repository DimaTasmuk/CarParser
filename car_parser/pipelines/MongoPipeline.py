import copy
import inspect

import pymongo
from pymongo.errors import DuplicateKeyError
from scrapy import Request

from car_parser.credentials import MONGO_URI, MONGO_DATABASE
from car_parser.spiders import AutoParser
from car_parser.spiders.autoscout import AutoScoutParser
from car_parser.spiders.autouncle import AutoUncleParser


class MongoPipeline(object):

    mandatory = ['make', 'model', 'sales_price_incl_vat', 'currency', 'body_type',
                 'mileage', 'fuel_consumption_comb', 'first_registration', 'colour']

    good_mandatory_fields = dict()

    iteration_id = 0
    bucket_for_insert = []
    bucket_for_update = []
    bucket_of_items_to_process = []

    MAX_BUCKET_SIZE = 1000

    @staticmethod
    def log_method_name(method_name='Unknown'):
        print('Method: {0}'.format(method_name))

    @staticmethod
    def log_error(error):
        print('Error: {0}'.format(error))

    def log(self, error, method_name='Unknown', item_origin_link=None):
        self.log_method_name(method_name)
        if item_origin_link is not None:
            print('Problems with such car: {0}'.format(item_origin_link))
        self.log_error(error)

    def __init__(self):
        try:
            # Set mongo connection string
            self.client = pymongo.MongoClient(MONGO_URI)
            self.mongodb = self.client[MONGO_DATABASE]

            self.collection = None

            # Get collection with iteration id
            self.iteration_collection = self.mongodb["Iteration"]
        except Exception as e:
            self.log(e, inspect.stack()[0][3])

    def open_spider(self, spider):
        try:
            # Get collection for current spider
            self.collection = self.mongodb[spider.table_name]

            # Get current iteration id for such spider
            self.iteration_id = self.iteration_collection.find_one(
                {
                    'site_name': spider.table_name
                },
                projection={'iteration_id': True, '_id': False}
            ).get('iteration_id', 0)

            # Check iteration id
            print("Previous iteration_id", self.iteration_id)
            self.iteration_id += 1
            print("Current iteration_id", self.iteration_id)
        except Exception as e:
            self.log(e, inspect.stack()[0][3])

    # Processing item after yield in the spider
    def process_item(self, item, spider):
        try:
            # Add current item to the bucket for future processing
            item = dict(item)
            self.bucket_of_items_to_process.append(item)

            if len(self.bucket_of_items_to_process) >= self.MAX_BUCKET_SIZE:
                # Create copy of the global variable for future process
                copy_of_bucket_of_items_to_process = copy.copy(self.bucket_of_items_to_process)
                self.bucket_of_items_to_process = []
                self.process_items_bucket(copy_of_bucket_of_items_to_process, spider)
            return item
        except Exception as e:
            self.log(e, inspect.stack()[0][3], item.get('origin_link'))

    def process_items_bucket(self, bucket_of_items_to_process, spider):
        try:
            # Get origin links for every car(item)
            bucket_of_origin_links = []
            for item in bucket_of_items_to_process:
                bucket_of_origin_links.append(item.get('origin_link'))

            # Check if such car(origin link) has been already added into collection
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

            # Get all added to the db cars and their origin links
            already_added_cars = []
            already_added_cars_origin_links = []
            for car in response:
                already_added_cars.append(car)
                already_added_cars_origin_links.append(car['origin_link'])

            for item in bucket_of_items_to_process:
                try:
                    # Check if car price was changed at the site
                    index = already_added_cars_origin_links.index(item['origin_link'])
                    if item.get('sales_price_incl_vat') is None:
                        continue
                    item['is_price_changed'] = \
                        (item.get('sales_price_incl_vat') != already_added_cars[index].get('sales_price_incl_vat'))

                    try:
                        # Process this item as added before
                        current_item = item
                        self.process_added_items(item, spider)
                    except Exception as e:
                        self.log(e, inspect.stack()[0][3], current_item.get('origin_link'))

                # Catching when item hasn't previous price(wasn't added)
                except ValueError as e:
                    # Process item as new
                    self.process_new_items(item, spider)

                except Exception as e:
                    self.log(e, inspect.stack()[0][3], item.get('origin_link'))

        except Exception as e:
            self.log(e, inspect.stack()[0][3], item.get('origin_link'))

    def process_new_items(self, item, spider):
        try:
            origin_link = item['origin_link']
            info = dict()
            info_update = dict()

            # Send item to the deep processing for each spider separately
            if isinstance(spider, AutoParser):
                deep_parsed_item = spider.create_one_deep_request(origin_link)
                if deep_parsed_item is None:
                    return {
                        "origin_link": origin_link,
                        "information": "Already in database"
                    }
                info_update = dict(deep_parsed_item)
            elif isinstance(spider, AutoUncleParser):
                info_update = dict(spider.create_one_deep_request(origin_link, item['model']))
                info_update['colour'] = item.get('colour')
                info_update['body_type'] = item.get('body_type')
            elif isinstance(spider, AutoScoutParser):
                deep_parsed_item = spider.create_deep_parse_request(
                    item['old_url'],
                    item['new_url'],
                    'update'
                )
                if deep_parsed_item is None:
                    return {
                        "origin_link": origin_link,
                        "information": "Car was sold"
                    }
                elif isinstance(deep_parsed_item, Request):
                    return {
                        "origin_link": origin_link,
                        "information": "Car will parse again"
                    }
                else:
                    info_update = dict(deep_parsed_item)
                    for key, field in info_update.items():
                        if field is None or field == "":
                            info_update.pop(key)

            # Add car description
            info.update(info_update)
            info['iteration_id'] = self.iteration_id
            info['is_synced'] = 0
            # Save item for future insert
            if item.get('currency') is None:
                return {
                    "origin_link": origin_link,
                    "information": "Invalid response"
                }
            if item.get('sales_price_incl_vat') is None:
                return {
                    "origin_link": origin_link,
                    "information": "Car hasn't price"
                }
            self.bucket_for_insert.append(info)

            if len(self.bucket_for_insert) >= self.MAX_BUCKET_SIZE:
                try:
                    # Create copy of the global variable for future process
                    copy_of_bucket_for_insert = copy.copy(self.bucket_for_insert)

                    # Find mandatory fields that is empty
                    self.find_bad_fields(copy_of_bucket_for_insert)

                    self.bucket_for_insert = []

                    # Insert data
                    self.mongodb[spider.table_name].insert(copy_of_bucket_for_insert)
                except DuplicateKeyError:
                    self.bucket_for_insert = []

            return info
        except Exception as e:
            self.log(e, inspect.stack()[0][3], item.get('origin_link'))

    def process_added_items(self, item, spider):
        try:
            origin_link = item.get('origin_link')

            # Update car information
            if item['is_price_changed']:
                # Update price, status and iteration id
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
                # Save item for future iteration id update
                self.bucket_for_update.append(origin_link)
                if len(self.bucket_for_update) >= self.MAX_BUCKET_SIZE:
                    try:
                        # Create copy of the global variable for future process
                        copy_of_bucket_for_update = copy.copy(self.bucket_for_update)
                        self.bucket_for_update = []

                        # Update only iteration id
                        self.mongodb[spider.table_name].update(
                            {
                                'origin_link':
                                {
                                    '$in': copy_of_bucket_for_update
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
                    except DuplicateKeyError:
                        self.bucket_for_update = []
                return {
                    "origin_link": origin_link,
                    "information": "Already in database"
                }
        except Exception as e:
            self.log(e, inspect.stack()[0][3], item.get('origin_link'))

    def close_spider(self, spider):
        try:
            # Work with unprocessed items
            if len(self.bucket_of_items_to_process) > 0:
                # Create copy of the global variable for future process
                copy_of_bucket_of_items_to_process = copy.copy(self.bucket_of_items_to_process)
                self.bucket_of_items_to_process = []
                self.process_items_bucket(copy_of_bucket_of_items_to_process, spider)

            if len(self.bucket_for_insert) > 0:
                # Create copy of the global variable for future process
                copy_of_bucket_for_insert = copy.copy(self.bucket_for_insert)

                # Find mandatory fields that is empty
                self.find_bad_fields(copy_of_bucket_for_insert)

                self.bucket_for_insert = []
                self.mongodb[spider.table_name].insert(copy_of_bucket_for_insert)

            if len(self.bucket_for_update) > 0:
                # Create copy of the global variable for future process
                copy_of_bucket_for_update = copy.copy(self.bucket_for_update)
                self.bucket_for_update = []
                self.mongodb[spider.table_name].update(
                    {
                        'origin_link':
                            {
                                '$in': copy_of_bucket_for_update
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
            self.iteration_collection.update(
                            {
                                'site_name': spider.table_name
                            },
                            {
                                '$set':
                                {
                                    'iteration_id': self.iteration_id,
                                    'bad_fields': self.mandatory
                                }
                            }
                        )
        except Exception as e:
            self.log(e, inspect.stack()[0][3])
        finally:
            self.client.close()

    def find_bad_fields(self, copy_of_bucket_for_insert):
        for b_item in copy_of_bucket_for_insert:
            copy_of_mandatory = copy.copy(self.mandatory)
            for m_field in copy_of_mandatory:
                if b_item.get(m_field) is not None:
                    self.good_mandatory_fields[m_field] = True
                    self.mandatory.remove(m_field)
