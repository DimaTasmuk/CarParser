# coding=utf-8
import scrapy
from scrapy import Request
import requests
from scrapy.http import Response
from twisted.internet import defer

from car_parser.items.AutoItem import AutoItem
from car_parser.loaders.AutoLoader import AutoLoader


# Spider call structure: scrapy crawl <name> -o <output file> -a <arguments>
# Spider call: scrapy crawl auto_parser -o xml_files\auto_parser.xml -a deep=true -a deep_links=http:,http:,http:
# Spider call: scrapy crawl auto_parser -o xml_files\auto_parser.xml -a deep=false


class AutoParser(scrapy.Spider):
    table_name = "Auto"

    name = "auto_parser"

    start_url = 'http://www.auto.de/search/findoffer'

    ORIGIN_LINK = u"http://www.auto.de"

    custom_settings = {
        "RETRY_TIMES": 10,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 400],
    }

    deep_parse_enabled = False

    parsed_cars_links = set()

    def __init__(self, **kwargs):
        super(AutoParser, self).__init__(**kwargs)
        # Set as argument
        if hasattr(self, 'deep') and self.deep.lower() == 'true':
            self.deep_parse_enabled = True

    def start_requests(self):
        if self.deep_parse_enabled:
            # print("Deep parse")
            self.settings.attributes["DUPEFILTER_CLASS"].value = 'scrapy.dupefilters.BaseDupeFilter'
            return [Request(self.start_url, self.create_deep_parse_requests)]
        else:
            # print("Shallow parse")
            return [Request(self.start_url, self.shallow_parse)]

    # Just need to implement
    def parse(self, response):
        pass

    # Start shallow parse
    def shallow_parse(self, response):
        cars = response.css("ul.vehicleOffers.vehicleList li.offers.size1of1.contentDesc")
        for car in cars:
            origin_link = self.ORIGIN_LINK + car.css("a.vehicleOffersBox::attr(href)").extract_first()
            if origin_link not in self.parsed_cars_links:
                loader = AutoLoader(item=AutoItem(), selector=car)
                loader.add_value('origin_link', unicode(origin_link))
                # loader.add_css('id', "li::attr(data-id)")
                # loader.add_css('marketing_headline', "*.headline.ellipsisText::text")
                loader.add_css('sales_price_incl_vat', "span.priceBig::text", re='\S+')
                # loader.add_css('sales_price_excl_vat', "div.priceBox::text", re='\S+')
                # loader.add_css('currency', "span.priceBig::text")
                #
                # vehicle_data_loader = loader.nested_css("div.technicalData")
                # vehicle_data_loader.add_css('mileage', "span[data-content*=mileage]::text", re="(?P<extract>.*) km")
                # vehicle_data_loader.add_css('power_in_kw', "span[data-content*=power]::text", re="(?P<extract>\d+) kW")
                # vehicle_data_loader.add_css('power_in_ps', "span[data-content*=power]::text", re="(?P<extract>\d+) PS")
                # vehicle_data_loader.add_css('fuel', "span[data-content*=fuelType]::text")
                # vehicle_data_loader.add_css('fuel_consumption_comb', "div::text", re='(?P<extract>\S+) l/100km')
                # vehicle_data_loader.add_css('co2_emission', "div::text", re='(?P<extract>\d+)g CO2/km')
                # vehicle_data_loader.add_css('gearbox', "span[data-content*=gearbox]::text")
                # vehicle_data_loader.add_css('first_registration', "span[data-content*=registrationDate]::text",
                #                             re="EZ (?P<extract>.*)")

                # self.parsed_cars_links.add(origin_link)
                yield loader.load_item()

        next_page = response.css("div.pagNext a.icon-right-dir::attr(href)").extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.shallow_parse)

    # Start deep parse for all items
    def create_deep_parse_requests(self, response):
        for item in response.css('ul.vehicleOffers.vehicleList li.offers.size1of1.contentDesc'):
            yield self.create_one_deep_request(self.ORIGIN_LINK + item.css('a.vehicleOffersBox::attr(href)').extract_first())

        next_page = response.css("div.pagNext a.icon-right-dir::attr(href)").extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.create_deep_parse_requests)

    def create_one_deep_request(self, link):
        r = requests.get(link)
        r.encoding = 'utf-8'
        return self.deep_parse_one_car(r)

    # Parse single car for deep_parse
    def deep_parse_one_car(self, response):
        # Check that this item was parsed
        if response.url not in self.parsed_cars_links:
            loader = AutoLoader(item=AutoItem(), response=response)

            loader.add_value('origin_link', unicode(response.url))
            loader.add_xpath('make', "//dt[@data-content='brand']/following-sibling::dd[1]/text()")
            loader.add_xpath('model', "//dt[@data-content='model']/following-sibling::dd[1]/text()")
            loader.add_xpath('marketing_headline', "//dt[@data-content='modelVariant']/following-sibling::dd[1]/text()")
            loader.add_css('sales_price_incl_vat', "span.priceBig::text", re="(\d+(?:\.)?(?:\d+)?)+")
            loader.add_css('sales_price_excl_vat', "td.priceInfo::text", re="(\d+(?:\.)?(?:\d+)?)+")
            loader.add_css('currency', "span.priceBig::text")
            loader.add_xpath('body_type', "//dt[@data-content='bodyType']/following-sibling::dd[1]/text()")
            loader.add_xpath('mileage', "//td[@data-content='mileage']/text()", re="\S+")
            loader.add_xpath('cubic_capacity', "//dt[@data-content='cubicCapacity']/following-sibling::dd[1]/text()",
                             re="\S+")
            loader.add_xpath('power_in_kw', "//td[@data-content='power']/text()", re="(?P<extract>\d+) kW")
            loader.add_xpath('power_in_ps', "//td[@data-content='power']/text()", re="(?P<extract>\d+) PS")
            loader.add_xpath('fuel', "//td[@data-content='fuelType']/text()")
            loader.add_xpath('fuel_consumption_comb',
                             "//dt[@data-content='consumption']/following-sibling::dd[1]/text()",
                             re="kombiniert: (?P<extract>\S+)")
            loader.add_xpath('fuel_consumption_city',
                             "//dt[@data-content='consumption']/following-sibling::dd[1]/text()",
                             re="innerorts: (?P<extract>\S+)")
            loader.add_xpath('fuel_consumption_country',
                             "//dt[@data-content='consumption']/following-sibling::dd[1]/text()",
                             re="ausserorts: (?P<extract>\S+)")
            loader.add_xpath('co2_emission', "//dt[@data-content='co2']/following-sibling::dd[1]/text()", re="\d+")
            loader.add_css('energy_efficiency_class', "span.contentSprite.coClass::text")
            loader.add_xpath('number_of_seats', "//dt[@data-content='seatCount']/following-sibling::dd[1]/text()")
            loader.add_xpath('number_of_doors', "//dt[@data-content='doorCount']/following-sibling::dd[1]/text()", re='\d+')
            loader.add_xpath('gearbox', "//td[@data-content='gearbox']/text()", re="\S+")
            loader.add_xpath('emission_class', "//dt[@data-content='contaminantType']/following-sibling::dd[1]/text()")
            loader.add_xpath('first_registration', "//td[@data-content='registrationDate']/text()",
                             re="EZ (?P<extract>.*)")
            loader.add_xpath('number_of_previous_owners',
                             "//dt[@data-content='previousOwnerCount']/following-sibling::dd[1]/text()")
            loader.add_xpath('service_maintenance', "//td[@data-content='huDate']/text()", re="HU (?P<extract>.*)")
            loader.add_xpath('climate_control', "//span[@data-content='hasAirCon']/text()")
            loader.add_xpath('climate_control', "//span[@data-content='hasAirConAutomatic']/text()")
            loader.add_xpath('parking_sensors', "//span[@data-content='hasParkingAssist']/text()")
            loader.add_xpath('airbags', "//span[@data-content='hasAirbags']/text()")
            loader.add_xpath('colour', "//dt[@data-content='exteriorColor']/following-sibling::dd[1]/text()")
            loader.add_xpath('interior', "//dt[@data-content='intType']/following-sibling::dd[1]/text()")
            loader.add_xpath('interior', "//dt[@data-content='intColor']/following-sibling::dd[1]/text()")

            self.parsed_cars_links.add(response.url)
            return loader.load_item()
