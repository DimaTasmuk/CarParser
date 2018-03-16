# -*- coding: UTF-8 -*-
from database_management.DynamoDB import DynamoDB


def check_items_for_uniqueness(table_name):
    database = DynamoDB(table_name=table_name)
