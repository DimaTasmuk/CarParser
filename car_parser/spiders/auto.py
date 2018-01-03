import logging

import scrapy
from car_parser.items.AutoItem import AutoItem
from car_parser.loaders.AutoLoader import AutoLoader


class AutoParser(scrapy.Spider):
    name = "auto_parser"

    start_urls = ["http://www.auto.de/search/findoffer?sci%5B%5D=&spra=&sma=&sg=&srdi=&sft=&sz=&src=1&"
                  "vt%5B%5D=1&vt%5B%5D=2&vt%5B%5D=3&vt%5B%5D=4&vt%5B%5D=5&vt%5B%5D=6&vt%5B%5D=7&"
                  "vt%5B%5D=8&vt%5B%5D=99&searchFast=Fahrzeug+suchen&srtcbd=0_asc"]

    custom_settings = {
        'ITEM_PIPELINES': {
            'car_parser.pipelines.AutoPipeline': 300
        }
    }

    PARAMETER_BRAND_NAME = "sci%5B%5D="

    specified_brand_keys = list()
    list_cars_info = list()

    def __init__(self, brand_key=None, **kwargs):
        logging.log(logging.INFO, brand_key)
        if brand_key:
            for key in brand_key.split(','):
                self.specified_brand_keys.append(key)
        super(AutoParser, self).__init__(brand_key, **kwargs)

    def parse(self, response):
        logging.log(logging.INFO, self.specified_brand_keys)
        yield response.follow("#brandModelLayer", self.parse_brands)

    def parse_brands(self, response):
        if self.specified_brand_keys:
            for key in self.specified_brand_keys:
                url = self.get_url_by_brand_key(response, key)
                yield response.follow(url, self.parse_cars)
        else:
            brand_keys = set(response.css("div.brandModelLayer div.autoForm ul.brandModel")
                             .xpath('//select[@id="sci"]')
                             .css("select.brandSearch option::attr(value)")
                             .extract())
            for key in brand_keys:
                url = self.get_url_by_brand_key(response, key)
                yield response.follow(url, self.parse_cars)

    def get_url_by_brand_key(self, response, key):
        return response.url.split(self.PARAMETER_BRAND_NAME)[0] + \
               self.PARAMETER_BRAND_NAME + \
               key + \
               response.url.split(self.PARAMETER_BRAND_NAME)[1]

    def parse_cars(self, response):
        cars = response.css("ul.vehicleList li.contentDesc a.vehicleOffersBox")

        for car in cars:
            loader = AutoLoader(item=AutoItem(), selector=car)
            loader.add_css('title', ".headline::text")

            vehicle_data_loader = loader.nested_css("div.technicalData p span")
            vehicle_data_loader.add_css('registrationDate', "span[data-content*=registrationDate]::text")
            vehicle_data_loader.add_css('mileage', "span[data-content*=mileage]::text")
            vehicle_data_loader.add_css('power', "span[data-content*=power]::text")
            vehicle_data_loader.add_css('fuelType', "span[data-content*=fuelType]::text")
            vehicle_data_loader.add_css('gearbox', "span[data-content*=gearbox]::text")

            loader.add_css('price', "span.priceBig::text")

            dealer_loader = loader.nested_css('div.vehicleOffersDealer div p:nth-child(2)')
            dealer_loader.add_css('seller', 'p:nth-child(2)::text')
            dealer_loader.add_css('seller_city', 'span[data-content*=city]::text')
            dealer_loader.add_css('seller_phone', "p:nth-child(2)::text")

            info = loader.load_item().__str__()
            if info not in self.list_cars_info:
                self.list_cars_info.append(info)
                yield loader.load_item()

        next_page = response.css("div.pagNext a.icon-right-dir::attr(href)").extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.parse_cars)
