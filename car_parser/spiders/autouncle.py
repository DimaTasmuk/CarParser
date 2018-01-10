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

    PARAMETER_BRAND_NAME = "?s%5Bbrand%5D="
    PARAMETER_MIN_PRICE_NAME = "&s%5Bmin_price%5D="
    PARAMETER_MAX_PRICE_NAME = "&s%5Bmax_price%5D="
    PARAMETER_MODEL_NAME = "&model_name%5D="

    MIN_PRICE = 0
    MAX_PRICE = 10000000
    MAX_ADVERTS = 2000

    models = dict()
    adverts = list()

    def parse(self, response):
        brands_models_response = response.css("body script").re(r"'search_brands_models'] = {(.*)};")[0]
        brands_models = brands_models_response.split("]]")
        for row in brands_models[:-1]:  # last element in list is empty
            # row - line with brand and models ("Hummer":[["H3 Alpha","H3 Alpha"],["H3T","H3T"],["H3X","H3X")
            brand = self.replace_symbols_in_line(row.split(":[[")[0])
            self.models[brand] = [
                self.replace_symbols_in_line(model) for model in row.split(":[[")[1]
                                                                     .replace("],[", ",")
                                                                     .split(",")[1::2]
            ]
            if brand == "Alfa+Romeo":
                yield response.follow(response.url + self.PARAMETER_BRAND_NAME + brand, self.parse_model)

    def parse_model(self, response):
        brand = re.search('\\' + self.PARAMETER_BRAND_NAME + '(\S+)', response.url).group(1)
        if self.is_filter_required(response):
            for model in self.models[brand]:
                yield response.follow(response.url + self.PARAMETER_MODEL_NAME + model, self.parse_price)
        else:
            for car in self.parse_car(response):
                yield car

    def parse_price(self, response):
        if self.get_count(response) > 0:
            yield self.create_request_with_price_limit(response.url, self.MIN_PRICE, self.MAX_PRICE)

    def create_request_with_price_limit(self, url, min_value, max_value):
        return scrapy.Request(url +
                              self.PARAMETER_MIN_PRICE_NAME +
                              str(min_value) +
                              self.PARAMETER_MAX_PRICE_NAME +
                              str(max_value),
                              self.binary_filter_by_price)

    def binary_filter_by_price(self, response):
        min_price = self.get_int_value_by_parameter(response.url, self.PARAMETER_MIN_PRICE_NAME)
        max_price = self.get_int_value_by_parameter(response.url, self.PARAMETER_MAX_PRICE_NAME)
        if self.is_filter_required(response) and min_price != max_price:
            url = response.url\
                .replace(self.PARAMETER_MIN_PRICE_NAME + str(min_price), "")\
                .replace(self.PARAMETER_MAX_PRICE_NAME + str(max_price), "")

            # Create new price limits(from the left limit to the middle)
            left_min_price = min_price
            left_max_price = min_price + (max_price - min_price) // 2
            left_request = self.create_request_with_price_limit(url, left_min_price, left_max_price)
            yield left_request

            # Create new price limits(from the middle to the right)
            right_min_price = (min_price + (max_price - min_price) // 2) + 1
            right_max_price = max_price
            right_request = self.create_request_with_price_limit(url, right_min_price, right_max_price)
            yield right_request
        elif self.is_filter_required(response) and min_price == max_price:
            # return error
            self.get_error_by_price(response)
            # show first 2000 cars with that parameters
            for car in self.parse_car(response):
                yield car
        else:
            for car in self.parse_car(response):
                yield car

    def parse_car(self, response):
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
            loader.add_css('price', "div.pricing span.price::attr(content)")
            loader.add_css('advert_link', "h3.car-title a::attr(href)")

            info = loader.load_item().__str__()
            if info not in self.adverts:
                self.adverts.append(info)
                yield loader.load_item()
        try:
            url = response.css("div.pagination-container span.next a::attr(href)").extract_first()
            yield response.follow(url, self.parse_car)
        except AttributeError:
            pass

    def get_error_by_price(self, response):
        url = response.url
        return dict(
            error='Too many cars with such parameters. Show only first 2000',
            brand=self.get_string_value_by_parameter(url, self.PARAMETER_BRAND_NAME),
            model=self.get_string_value_by_parameter(url, self.PARAMETER_MODEL_NAME),
            price=self.get_int_value_by_parameter(url, self.PARAMETER_MIN_PRICE_NAME)
        )

    def is_filter_required(self, response):
        return self.get_count(response) > self.MAX_ADVERTS

    def get_count(self, response):
        count_line = response.css("div.search-summary span h1::text").extract_first()
        try:
            return int(count_line.split(" ")[0].replace(".", ''))
        except AttributeError:
            return 0

    def replace_symbols_in_line(self, line):
        return line.replace('"', "").replace(",", "").replace(" ", "+")

    def get_string_value_by_parameter(self, url, parameter):
        return str(re.search(parameter + '(\w+)', url).group(1))

    def get_int_value_by_parameter(self, url, parameter):
        return int(self.get_string_value_by_parameter(url, parameter))
