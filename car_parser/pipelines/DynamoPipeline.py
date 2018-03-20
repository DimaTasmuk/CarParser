import boto3
import time

import os

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dateutil import tz

from car_parser.settings import DYNAMO_REGION
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

    bucket = set()

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMO_REGION)
        self.table = None

    def open_spider(self, spider):
        self.table = self.dynamodb.Table(spider.table_name)

    def process_item(self, item, spider):
        origin_link = item.get('origin_link')
        info = dict()
        response = self.table.query(
            ProjectionExpression="origin_link, is_synced",
            KeyConditionExpression=Key('origin_link').eq(origin_link) & Key('is_synced').eq(1)
        )
        try:
            if len(response['Items']) == 0:
                info_update = dict()
                if spider == AutoParser:
                    info_update = dict(spider.create_one_deep_request(origin_link))
                elif spider == AutoUncleParser:
                    # info_update = dict()
                elif spider == AutoScoutParser:
                    # info_update = dict()
                    for key, field in info_update.items():
                        if field is None or field == "":
                            info_update.pop(key)
                info.update(info_update)
                info['iteration_id'] = 2
                info.pop('origin_link')
                self.table.put_item(
                    Item={
                        'origin_link': origin_link,
                        'is_synced': 0,
                        'info': info
                    }
                )
        except ClientError as e:
            print(e)
        except Exception as e:
            print(e)
        return item
