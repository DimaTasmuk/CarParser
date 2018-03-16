# coding=utf-8
import decimal

import scrapy
import re

from car_parser.items import AutoUncleItem
from car_parser.loaders import AutoUncleLoader
from .literals.autouncle import *

# Spider call structure: scrapy crawl <name> -o <output file> -a <arguments>
# Spider call example: scrapy crawl autouncle -o result_autouncle.json -a deep=true
# Spider call example: scrapy crawl autouncle -o result_autouncle.json -a deep=false


class AutoUncleParser(scrapy.Spider):
    table_name = "AutoUncle"

    name = "autouncle"
    start_urls = ["https://www.autouncle.de/de/gebrauchtwagen/"]

    deep_parse_enabled = False

    models = dict()
    adverts = set()

    tags = []
    body_types = []
    colors = []

    def __init__(self, **kwargs):
        super(AutoUncleParser, self).__init__(**kwargs)
        if hasattr(self, 'deep'):
            if self.deep.lower() == 'true':
                self.deep_parse_enabled = True

    def parse(self, response):
        self.load_tags(response)
        self.load_body_types(response)
        self.load_colors(response)

        # Get all brands and models from start page
        brands_models_response = response.css("body script") \
            .re(r"'search_brands_models'] = {(.*)};")[0]
        brands_models = brands_models_response.split("]]")

        # Split brands and their models
        for row in brands_models[:-1]:
            """
            last element in list is empty
            row - line with brand and models (
            "Hummer":[["H3 Alpha","H3 Alpha"],["H3T","H3T"],["H3X","H3X"]]
            )
            """
            brand = self.replace_symbols_in_line(row.split(":[[")[0])
            brand = self.replace_inconvenient_symbols(brand)

            self.models[brand] = [
                self.replace_symbols_in_line(model)
                for model in row.split(":[[")[1]
                                .replace("],[", ",")
                                .split(",")[1::2]
            ]

            # if brand == "Mitsubishi"
            # or brand == "Hyundai"
            # or brand == "Dacia":

            # if brand == 'Audi':

            for model in (self.models[brand]):
                for body_type in self.body_types:
                    for color in self.colors:
                        self.adverts.clear()
                        url = response.url \
                              + PARAMETERS['brand'] + brand \
                              + PARAMETERS['model'] + model \
                              + PARAMETERS['body_type'] + body_type \
                              + PARAMETERS['color'] + color
                        yield response.follow(url, self.parse_price)

    def parse_price(self, response):
        if self.is_filter_required(response):
            yield self.create_request_with_price_limit(response.url,
                                                       MIN_PRICE,
                                                       MAX_PRICE)
        elif self.get_cars_number(response) > 0:
            for car in self.parse_car(response):
                yield car

    def create_request_with_price_limit(self, url, min_value, max_value):
        return scrapy.Request(url +
                              PARAMETERS['min_price'] +
                              str(min_value) +
                              PARAMETERS['max_price'] +
                              str(max_value),
                              self.binary_filter_by_price)

    def binary_filter_by_price(self, response):
        min_price, max_price = self.get_price_arguments(response.url)

        if self.is_filter_required(response) and min_price != max_price:
            url = response.url \
                .replace(PARAMETERS['min_price'] + str(min_price), "") \
                .replace(PARAMETERS['max_price'] + str(max_price), "")

            # Create new price limits(from the left limit to the middle)
            left_min_price = min_price
            left_max_price = min_price + (max_price - min_price) // 2
            left_request = self.create_request_with_price_limit(url,
                                                                left_min_price,
                                                                left_max_price)
            yield left_request

            # Create new price limits(from the middle to the right)
            right_min_price = (min_price + (max_price - min_price) // 2) + 1
            right_max_price = max_price
            right_request = self.create_request_with_price_limit(
                url,
                right_min_price,
                right_max_price
            )
            yield right_request
        elif self.is_filter_required(response) and min_price == max_price:
            # return error
            self.generate_error_for_price(response)
            # show first 2000 cars with that parameters
            for car in self.parse_car(response):
                yield car
        else:
            for car in self.parse_car(response):
                yield car

    def generate_error_for_price(self, response):
        url = response.url
        return dict(
            error='Too many cars with such parameters. Show only first 2000',
            brand=self.get_string_value_by_parameter(url,
                                                     PARAMETERS['brand']),
            model=self.get_string_value_by_parameter(url,
                                                     PARAMETERS['model']),
            price=self.get_int_value_by_parameter(url,
                                                  PARAMETERS['min_price'])
        )

    def parse_car(self, response):
        for car in response.css("div.car-list-item div.car-details-wrapper"):
            origin_link = car.css("h3.car-title a::attr(href)").extract_first()
            if origin_link not in self.adverts:
                model = self.replace_inconvenient_symbols(
                    self.get_string_value_by_parameter(response.url,
                                                       PARAMETERS['model'])
                )
                if self.deep_parse_enabled:
                    request = scrapy.Request(response.urljoin(origin_link),
                                             self.parse_car_details)
                    request.meta['meta_model'] = model
                    yield request
                else:
                    loader = AutoUncleLoader(item=AutoUncleItem(), selector=car)
                    loader.add_value('model', unicode(model))
                    loader.add_value('origin_link', unicode(ORIGIN_LINK + origin_link))

                    self.fill_search_page_fields(loader, car)

                    yield loader.load_item()
                self.adverts.add(origin_link)

        url = response.css(
            "div.pagination-container span.next a::attr(href)"
        ).extract_first()
        if url:
            try:
                url = url.replace(
                    re.search('gebrauchtwagen' + '(/.*)\?', url).group(1),
                    ""
                )
            except AttributeError:
                pass
            yield response.follow(url, self.parse_car)

    def parse_car_details(self, response):
        model = response.meta['meta_model']
        car = response.css("div.car-list-item div.car-details-wrapper")

        loader = AutoUncleLoader(item=AutoUncleItem(), selector=car)
        loader.add_value('model', unicode(model))
        loader.add_value('origin_link', unicode(response.url))

        self.fill_search_page_fields(loader, car)

        car_tags = self.get_tags(response)
        for key in TAGS.keys():
            for tag in TAGS[key]:
                if tag in car_tags:
                    loader.add_value(key, tag)
        yield loader.load_item()

    def load_tags(self, response):
        top_tags = response.css(
            'div div.input-group '
            'div.car-search-filters-equipment-top '
            'label.label::text'
        ).extract()
        other_tags = response.css(
            'div div.input-group '
            'div.car-search-filters-equipment-other '
            'label.label::text'
        ).extract()
        for tag in top_tags + other_tags:
            self.tags.append(tag)

    def load_body_types(self, response):
        self.body_types = response.css(
            'div.input-group.body_types '
            'div.input input::attr(value)'
        ).extract()[1:]

    def load_colors(self, response):
        self.colors = response.css(
            'div.input.colors '
            'select option::attr(value)'
        ).extract()[1:]

    def is_filter_required(self, response):
        return self.get_cars_number(response) > MAX_ACCESSIBLE_CARS_NUMBER

    @staticmethod
    def replace_inconvenient_symbols(line):
        return line.replace('%21', '!') \
            .replace('%E9', 'e') \
            .replace("%C3%AB", "e")

    @staticmethod
    def replace_symbols_in_line(line):
        return line.replace('"', '') \
            .replace(',', '') \
            .replace(' ', '+')

    def fill_search_page_fields(self, loader, car):
        loader.add_css('make', "h3.car-title span b::text")
        loader.add_css('sales_price_incl_vat', "div.pricing span.price::attr(content)")
        loader.add_css('currency', "div.pricing span.price::text")
        loader.add_css('first_registration', "ul li.year span::text")
        loader.add_css('mileage', "ul li.km span::text")
        loader.add_value('cubic_capacity', unicode(self.get_cubic_capacity(car)))
        loader.add_value('fuel', self.get_fuel_type(car))
        loader.add_css('fuel_consumption_comb', 'ul li.fuel_efficiency span span::text')
        loader.add_css('co2_emission', 'ul li.co2_emission span::text')
        loader.add_css('energy_efficiency_class', 'ul li.co2_class span::text')
        loader.add_css('power_in_ps', 'ul li.hp span::text')
        loader.add_value('emission_class', car.css('ul li.euro_emission_class dfn::text').extract_first())
        loader.add_value('emission_class', car.css('ul li.euro_emission_class span::text').extract_first())

        try:
            headline = car.css('h3.car-title span span::text').extract_first()
            headline = headline.replace(loader.get_value('make'), '', 1)
            headline = headline.replace(loader.get_value('model'), '', 1)
            loader.add_value('marketing_headline', headline)
        except AttributeError:
            print(loader.get_value('origin_link'))

    def get_price_arguments(self, url):
        try:
            min_price = self.get_int_value_by_parameter(
                url,
                PARAMETERS['min_price']
            )
            max_price = self.get_int_value_by_parameter(
                url,
                PARAMETERS['max_price']
            )
        except:
            min_price = int(MIN_PRICE)
            max_price = int(MAX_PRICE)
        return min_price, max_price

    @staticmethod
    def get_tags(response):
        return response.css(
            'section.equipment ul.equipment_pills li span::text').extract()

    @staticmethod
    def get_cubic_capacity(response):
        engine_info = response.css("ul li.engine span::text").extract_first()
        value = re.search(r'\d+\.?\d*', engine_info)
        if value is None:
            return None
        value = value.group(0)
        return decimal.Decimal(value)

    @staticmethod
    def get_fuel_type(response):
        engine_info = response.css("ul li.engine span::text").extract_first()
        value = re.search(r'[a-zA-Z]+', engine_info)
        if value is None:
            return None
        value = value.group(0)
        return value

    @staticmethod
    def get_cars_number(response):
        count_line = response.css(
            "div.search-summary span h1::text").extract_first()
        try:
            return int(count_line.split(" ")[0].replace(".", ''))
        except AttributeError:
            return 0

    @staticmethod
    def get_string_value_by_parameter(url, parameter):
        return str(re.search(parameter + '([^&]+)', url).group(1))

    def get_int_value_by_parameter(self, url, parameter):
        return int(self.get_string_value_by_parameter(url, parameter))