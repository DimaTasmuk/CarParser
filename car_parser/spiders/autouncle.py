# coding=utf-8

import scrapy
import re

from car_parser.items import AutoUncleItem
from car_parser.loaders import AutoUncleLoader


class AutoUncleParser(scrapy.Spider):
    name = "autouncle_parser"
    start_urls = ["https://www.autouncle.de/de/gebrauchtwagen/"]

    collection_name = 'autouncle_collection'

    PARAMETER_BRAND_NAME = "?s%5Bbrand%5D="
    PARAMETER_MIN_PRICE_NAME = "&s%5Bmin_price%5D="
    PARAMETER_MAX_PRICE_NAME = "&s%5Bmax_price%5D="
    PARAMETER_MODEL_NAME = "model_name%5D="

    ORIGIN_LINK = u"www.autouncle.de"

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
            brand = self.replace_symbols_in_line(row.split(":[[")[0]).encode('utf-8').replace("ë", "e")
            self.models[brand] = [
                self.replace_symbols_in_line(model) for model in row.split(":[[")[1]
                                                                     .replace("],[", ",")
                                                                     .split(",")[1::2]
            ]
            # if brand == "Mitsubishi" or brand == "Hyundai" or brand == "Dacia":
            # if brand == 'Audi':
            yield response.follow(response.url + self.PARAMETER_BRAND_NAME + brand, self.parse_model)

    def parse_model(self, response):
        brand = re.search('\\' + self.PARAMETER_BRAND_NAME + '(\S+)', response.url).group(1)

        # replace UTF-8 ë to e
        if "%C3%AB" in brand:
            brand = self.replace_HEX_to_character(brand)

        for model in self.models[brand]:
            yield response.follow(response.url + "&" + self.PARAMETER_MODEL_NAME + model, self.parse_price)

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
            model = self.replace_HEX_to_character(
                self.get_string_value_by_parameter(response.url, self.PARAMETER_MODEL_NAME)
            )
            loader = AutoUncleLoader(item=AutoUncleItem(), selector=car)
            loader.add_css('brand', "h3.car-title span b::text")
            loader.add_value('model', model)
            loader.add_css('title', 'h3.car-title span span::text')
            loader.add_css('price', "div.pricing span.price::attr(content)")

            loader.add_value('details_link', self.ORIGIN_LINK)
            loader.add_css('details_link', "h3.car-title a::attr(href)")

            loader.add_css('image_url', "div.picture.left-half a.colorbox.cboxElement::attr(src)")

            loader.add_css('reg_date', "ul li.year span::text")
            loader.add_css('mileage', "ul li.km span::text")
            loader.add_css('fuel_type', "ul li.engine span::text")
            loader.add_css('fuel_consumption', "ul li.fuel_efficiency span span::text")
            loader.add_css('fuel_consumption', "ul li.fuel_efficiency dfn::text")
            loader.add_css('co2_emission', "ul li.co2_emission span::text")
            loader.add_css('power', "ul li.hp span::text")

            loader.add_css('location', "ul li.location span::text")

            info = loader.get_collected_values("details_link")
            if info not in self.adverts:
                self.adverts.append(info)
                yield loader.load_item()
        url = response.css("div.pagination-container span.next a::attr(href)").extract_first()
        if url:
            try:
                url = url.replace(re.search('gebrauchtwagen' + '(/.*)\?', url).group(1), "")
            except AttributeError:
                pass
            yield response.follow(url, self.parse_car)

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

    def replace_HEX_to_character(self, line):
        return line.replace('%21', '!').replace('%E9', 'e').replace("%C3%AB", "e")

    def get_string_value_by_parameter(self, url, parameter):
        return unicode(re.search(parameter + '([^&]+)', url).group(1))

    def get_int_value_by_parameter(self, url, parameter):
        return int(self.get_string_value_by_parameter(url, parameter))
