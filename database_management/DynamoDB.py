import boto3
from boto3.dynamodb.conditions import Key, Attr

from settings import DYNAMO_ENDPOINT, DYNAMO_REGION


class DynamoDB(object):

    dynamodb = None

    table = None

    new_items = set()

    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMO_REGION, endpoint_url=DYNAMO_ENDPOINT)
        self.table = self.dynamodb.Table(table_name)
        super(DynamoDB, self).__init__()

    def structure_data(self):
        synced_items = self.table.query(
            ProjectionExpression="origin_link",
            KeyConditionExpression=Key('is_synced').eq(1)
        )
        self.remove_certain_items(synced_items)

        # Need 'while' because Query operation can retrieve a maximum of 1 MB of data
        while 'LastEvaluatedKey' in synced_items:
            synced_items = self.table.query(
                ProjectionExpression="origin_link",
                KeyConditionExpression=Key('is_synced').eq(1),
                ExclusiveStartKey=synced_items['LastEvaluatedKey']
            )
            self.remove_certain_items(synced_items)

        # Add origin_link of not_synced_items to new_item's set for deep parsing these adverts
        just_parsed_items = self.table.query(
            ProjectionExpression="origin_link",
            KeyConditionExpression=Key('is_synced').eq(0)
        )

        self.new_items.update([i.get('origin_link') for i in just_parsed_items['Items']])
        while 'LastEvaluatedKey' in just_parsed_items:
            just_parsed_items = self.table.query(
                ProjectionExpression="origin_link",
                KeyConditionExpression=Key('is_synced').eq(0),
                ExclusiveStartKey=just_parsed_items['LastEvaluatedKey']
            )
            self.new_items.update([i.get('origin_link') for i in just_parsed_items['Items']])

    def remove_certain_items(self, synced_items):
        """
        Delete just parsed data if exist synchronized. Before that, update price
        in synchronized data with value from parsed item.

        Also delete synchronized items in DynamoDB if advert has been deleted.

        :param synced_items: items synchronized with MongoDB
        """
        for item in synced_items:
            parsed_items = self.table.query(
                ProjectionExpression="origin_link, info.sales_price_incl_vat",
                KeyConditionExpression=Key('is_synced').eq(0)
            )
            if len(parsed_items['Items']) > 0:
                # Update price
                self.update_price(parsed_items['Items'][0])

                # Delete just parsed item
                self.table.delete_item(
                    Key={
                        'is_synced': 0,
                        'origin_link': parsed_items['Items'][0].get('origin_link')
                    }
                )
            else:
                # Delete existing item
                self.table.delete_item(
                    Key={
                        'is_synced': 1,
                        'origin_link': item['Items'][0].get('origin_link')
                    }
                )

    def update_price(self, parsed_item):
        self.table.update_item(
            Key={
                'is_synced': 1,
                'origin_link': parsed_item['origin_link']
            },
            UpdateExpression="set info.sales_price_incl_vat = :incl_vat",
            ExpressionAttributeValues={
                ":incl_vat": parsed_item.get("info.sales_price_incl_vat")
            }
        )
