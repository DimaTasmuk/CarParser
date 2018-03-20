import boto3
import time

import os

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dateutil import tz

from car_parser.settings import DYNAMO_REGION, aws_access_key_id, aws_secret_access_key
from car_parser.spiders import AutoParser
from car_parser.spiders.autoscout import AutoScoutParser
from car_parser.spiders.autouncle import AutoUncleParser

if os.name == 'nt':
    def _naive_is_dst(self, dt):
        timestamp = tz.tz._datetime_to_timestamp(dt)
        # workaround the bug of negative offset UTC prob
        if timestamp+time.timezone < 0:
            current_time = timestamp + time.timezone + 31536000
        else:
            current_time = timestamp + time.timezone
        return time.localtime(current_time).tm_isdst

    tz.tzlocal._naive_is_dst = _naive_is_dst


class DynamoPipeline(object):

    iteration_id = 0

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
                                       region_name=DYNAMO_REGION,
                                       aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key
                                       )
        self.table = None
        self.iteration_table = self.dynamodb.Table("Iteration")

    def open_spider(self, spider):
        self.table = self.dynamodb.Table(spider.table_name)

        self.iteration_id = self.iteration_table.query(
            ProjectionExpression="site_name, iteration_id",
            KeyConditionExpression=Key('site_name').eq(spider.table_name)
        )['Items'][0].get('iteration_id')
        print(self.iteration_id)
        self.iteration_id += 1
        print(self.iteration_id)

    def process_item(self, item, spider):
        origin_link = item.get('origin_link')
        info = dict()
        response = self.table.query(
            ProjectionExpression="origin_link, is_synced",
            KeyConditionExpression=Key('origin_link').eq(origin_link) & Key('is_synced').eq(0)
        )
        # TODO: add logger for error
        # try:
        if len(response['Items']) == 0:
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
            info.update(info_update)
            info['iteration_id'] = self.iteration_id
            info.pop('origin_link')
            self.table.put_item(
                Item={
                    'origin_link': origin_link,
                    'is_synced': 0,
                    'info': info
                }
            )
        else:
            self.table.update_item(
                Key={
                    'is_synced': 0,
                    'origin_link': origin_link
                },
                UpdateExpression="set info.iteration_id = :iteration_id",
                ExpressionAttributeValues={
                    ":iteration_id": self.iteration_id
                }
            )

        # except ClientError as e:
        #     print('ERROR', e)
        # except Exception as e:
        #     print('ERROR', e)
        return item

    def close_spider(self, spider):
        self.iteration_table.update_item(
            Key={
                'site_name': spider.table_name
            },
            UpdateExpression="set iteration_id = :iter",
            ExpressionAttributeValues={
                ":iter": self.iteration_id
            }
        )
