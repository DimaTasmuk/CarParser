import scrapy
import re

from car_parser.items import AutoUncleItem
from car_parser.loaders import AutoUncleLoader


class AutoUncleParser(scrapy.Spider):
    name = "autouncle_parser"
    start_urls = ["https://www.autouncle.de/de/gebrauchtwagen/"]

    custom_settings = {
        'ITEM_PIPELINES': {
            'car_parser.pipelines.AutoUnclePipeline': 100
        }
    }

    models = dict()
    adverts = list()
    count = 0

    def parse(self, response):
        brands_models_response = response.css("body script").re(r"'search_brands_models'] = {(.*)};")[0]
        brands_models = brands_models_response.split("]]")
        for row in brands_models[:-1]:  # last element in list is empty
            # row - line with brand and models ("Hummer":[["H3 Alpha","H3 Alpha"],["H3T","H3T"],["H3X","H3X")
            brand = self.replace_symbols_in_line(row.split(":[[")[0])
            self.models[brand] = [
                self.replace_symbols_in_line(model)
                for model in row.split(":[[")[1].replace("],[", ",").split(",")[1::2]
            ]
            if brand == "Volvo":
                yield response.follow(response.url + "?s%5Bbrand%5D=" + brand, self.parse_price)

    def parse_price(self, response):
        count = self.get_count(response)
        if count is not None and count > 2000:
            for price in range(100, 200000, 100):
                yield response.follow(response.url + "&s%5Bmin_price%5D=" + str(price) + "&s%5Bmax_price%5D=" + str(price + 99), self.parse_model)
            for price in range(200000, 10000000, 50000):
                yield response.follow(response.url + "&s%5Bmin_price%5D=" + str(price) + "&s%5Bmax_price%5D=" + str(price + 49999), self.parse_model)
        else:
            for car in self.parse_car(response):
                yield car

    def parse_model(self, response):
        brand = re.search('s%5Bbrand%5D=(\w+)', response.url).group(1)
        count = self.get_count(response)
        if count is not None and count > 2000:
            for model in self.models[brand]:
                yield response.follow(response.url + "&model_name%5D=" + model, self.parse_car)
        else:
            for car in self.parse_car(response):
                yield car

    def parse_car(self, response):
        count = self.get_count(response)
        if count and count > 2000:
            print(count, response.url)
        for car in response.css("div.car-list-item div.car-details-wrapper"):
            loader = AutoUncleLoader(item=AutoUncleItem(), selector=car)
            loader.add_css('brand', "h3.car-title span b::text")
            loader.add_css('title', "h3.car-title span span::text")
            loader.add_css('year', "ul li.year span::text")
            loader.add_css('km', "ul li.km span::text")
            loader.add_css('engine', "ul li.engine span::text")
            loader.add_css('fuel_efficiency', "ul li.fuel_efficiency span span::text")
            loader.add_css('fuel_efficiency', "ul li.fuel_efficiency dfn::text")
            loader.add_css('co2_emission', "ul li.co2_emission span::text")
            loader.add_css('location', "ul li.location span::text")
            loader.add_css('price', "div.pricing span.price")
            loader.add_css('advert_link', "h3.car-title a::attr(href)")

            info = loader.load_item().__str__()
            if info not in self.adverts:
                self.count += 1
                self.adverts.append(info)
                yield loader.load_item()
        print(self.count)
        try:
            url = response.css("div.pagination-container span.next a::attr(href)").extract_first()
            yield response.follow(url, self.parse_car)
        except AttributeError:
            pass

    def get_count(self, response):
        count_line = response.css("div.search-summary span h1::text").extract_first()
        try:
            return int(count_line.split(" ")[0].replace(".", ''))
        except AttributeError:
            return None

    def replace_symbols_in_line(self, line):
        return line.replace('"', "").replace(",", "").replace(" ", "+")
