# coding=utf-8
import re
import scrapy
from car_parser.items.AutoItem import AutoItem
from car_parser.loaders.AutoLoader import AutoLoader


# Spider call structure: scrapy crawl <name> -o <output file> -a <arguments>
# Spider call example: scrapy crawl auto_parser -o xml_files\auto_parser.xml -a brand_key=870
class AutoParser(scrapy.Spider):
    name = "auto_parser"
    start_urls = ["http://www.auto.de/search/findoffer?sci%5B%5D=&spra=&sma=&sg=&srdi=&sft=&sz=&src=1&"
                  "vt%5B%5D=1&vt%5B%5D=2&vt%5B%5D=3&vt%5B%5D=4&vt%5B%5D=5&vt%5B%5D=6&vt%5B%5D=7&"
                  "vt%5B%5D=8&vt%5B%5D=99&searchFast=Fahrzeug+suchen&srtcbd=0_asc"]

    collection_name = 'auto_collection'

    parsed_cars_links = set()

    def parse(self, response):
        cars = response.css("ul.vehicleOffers.vehicleList li.contentDesc")
        for car in cars:
            details_link = car.css("a.vehicleOffersBox::attr(href)").extract_first()
            if details_link not in self.parsed_cars_links:
                loader = AutoLoader(item=AutoItem(), selector=car)
                loader.add_css('id', "li::attr(data-id)")
                loader.add_css('marketing_headline', "*.headline.ellipsisText::text")
                loader.add_css('sales_price_incl_vat', "span.priceBig::text", re='\S+')
                loader.add_css('sales_price_excl_vat', "div.priceBox::text", re='\S+')

                vehicle_data_loader = loader.nested_css("div.technicalData")
                vehicle_data_loader.add_css('mileage', "span[data-content*=mileage]::text", re="(?P<extract>.*) km")
                vehicle_data_loader.add_css('power_in_kw', "span[data-content*=power]::text", re="(?P<extract>\d+) kW")
                vehicle_data_loader.add_css('power_in_ps', "span[data-content*=power]::text", re="(?P<extract>\d+) PS")
                vehicle_data_loader.add_css('fuel', "span[data-content*=fuelType]::text")
                vehicle_data_loader.add_css('fuel_consumption_comb', "div::text", re='(?P<extract>\S+) l/100km')
                vehicle_data_loader.add_css('co2_emission', "div::text", re='(?P<extract>\d+)g CO2/km')
                vehicle_data_loader.add_css('gearbox', "span[data-content*=gearbox]::text")
                vehicle_data_loader.add_css('first_registration', "span[data-content*=registrationDate]::text", re="EZ (?P<extract>.*)")

                self.parsed_cars_links.add(details_link)
                yield loader.load_item()

        next_page = response.css("div.pagNext a.icon-right-dir::attr(href)").extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.parse)