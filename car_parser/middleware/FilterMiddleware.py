from scrapy.exceptions import IgnoreRequest

from car_parser.spiders.autoscout import AutoScoutParser
from car_parser.utilities.uri import clear_parameters


class FilterMiddleware(object):

    def __init__(self):
        self.scraped_records = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):

        if isinstance(spider, AutoScoutParser):
            if not spider.deep_parse_enabled:
                return None

            url = clear_parameters(request.url)
            if 'https://www.autoscout24.de/ergebnisse' in url:
                return None

            if url in self.scraped_records:
                spider.logger.info("Dropped request to %s" % url)
                raise IgnoreRequest
            else:
                self.scraped_records.add(url)