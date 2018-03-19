from scrapinghub import ScrapinghubClient

from car_parser.settings import SCRAPY_API_KEY, SCRAPY_PROJECT_ID


class ParserManager(object):
    client = ScrapinghubClient(SCRAPY_API_KEY)

    spider = None

    def __init__(self, spider):
        self.spider = spider
        super(ParserManager, self).__init__()

    def run_deep_parse(self, item_urls):
        self.client.get_project(SCRAPY_PROJECT_ID).jobs.run(self.spider, job_args=item_urls)