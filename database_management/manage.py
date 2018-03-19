from database_management import DynamoDB
from car_parser.ParserManager import ParserManager


class DatabaseManager(object):
    dynamo = None
    spider = None

    def __init__(self, table_name, spider_name):
        self.spider = spider_name
        self.dynamo = DynamoDB(table_name)
        super(DatabaseManager, self).__init__()

    def structure_dynamo(self):
        self.dynamo.structure_data()

        if len(self.dynamo.new_items) > 0:
            self.start_deep_parse()

    def start_deep_parse(self):
        parser_manager = ParserManager(self.spider)
        parser_manager.run_deep_parse(self.dynamo.new_items)
