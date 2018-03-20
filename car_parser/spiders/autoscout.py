# coding=utf-8
import decimal
from urlparse import urljoin

from math import ceil

from .literals.autoscout import *
from car_parser.utilities.uri import *

from re import search, findall
from scrapy import Spider, Request


# Spider call structure: scrapy crawl <name> -o <output file> -a <arguments>
# Spider call example: scrapy crawl autoscout24 -o brand.json -a deep=true
# Spider call example: scrapy crawl autoscout24 -o brand.json -a deep=false


class AutoScoutParser(Spider):
    table_name = "AutoScout"

    name = 'autoscout24'

    deep_parse_enabled = False

    brands = dict()
    models = dict()

    # Processing arguments from cmd
    def __init__(self, **kwargs):
        super(AutoScoutParser, self).__init__(**kwargs)

        if hasattr(self, 'deep') and self.deep.lower() == 'true':
            self.deep_parse_enabled = True

    # Initialize spider
    def start_requests(self):
        return [
            Request('https://www.autoscout24.de/ergebnisse',
                    self.filter_by_brand)
        ]

    # Tier 0
    # Initialize brand-specific requests
    def filter_by_brand(self, response):
        # Get all tags with brands
        brands = response.xpath(COMMON_XPATH['brands'])
        for brand in brands:
            # Get current brand key and value
            brand_key = brand.xpath('./@key').extract_first()
            brand_value = brand.xpath('./@value').extract_first()

            # Put brand to the dictionary
            self.brands[brand_key] = brand_value
            self.models[brand_key] = dict()

            # Skip the 'Others' section
            if OTHERS_ELEMENT_ID in brand_value:
                continue

            # Make new request with selected brand
            uri = set_parameter(response.url, PARAMETERS['brand'], brand_key)
            yield Request(uri, self.filter_by_model)

    # Tier 1
    # Initialize model-specific requests
    def filter_by_model(self, response):
        brand_key = get_parameter(response.url, PARAMETERS['brand'])
        self.models[brand_key] = self.get_models(response)

        for model_key, model_value in self.models[brand_key].items():
            url = response.url
            url = set_parameter(url, PARAMETERS['model'], model_key)
            url = self.set_price_limits(url, MIN_PRICE, MAX_PRICE)
            yield Request(url, self.filter_by_price)

    # Tier 2.1
    # Binary filtering by price
    def filter_by_price(self, response):
        price_from, price_to = self.get_price_limits(response.url)

        if self.is_filter_required(response):

            if price_from < price_to:
                median = price_from + (price_to - price_from) // 2

                url = self.set_price_limits(response.url, price_from, median)
                yield Request(url, self.filter_by_price)

                url = self.set_price_limits(response.url, median + 1, price_to)
                yield Request(url, self.filter_by_price)

            else:
                url = response.url
                url = self.set_mileage_limits(url, MIN_MILEAGE, MAX_MILEAGE)
                yield Request(url, self.filter_by_mileage)

        else:
            for request in self.init_parse(response):
                yield request

    # Tier 2.2
    # Binary filtering by mileage
    def filter_by_mileage(self, response):
        mileage_from, mileage_to = self.get_mileage_limits(response.url)

        if self.is_filter_required(response):

            if mileage_from < mileage_to:
                median = mileage_from + (mileage_to - mileage_from) // 2
                url = response.url

                url = self.set_mileage_limits(url, mileage_from, median)
                yield Request(url, self.filter_by_mileage)

                url = self.set_mileage_limits(url, median + 1, mileage_to)
                yield Request(url, self.filter_by_mileage)

            else:
                error_info = self.get_quantity_error_info(response)
                self.logger.error(error_info)

                for request in self.init_parse(response):
                    yield request

        else:
            for request in self.init_parse(response):
                yield request

    # Tier 3
    # Create page specific requests
    def init_parse(self, response):
        pages = self.get_quantity(response) / MAX_CARS_PER_PAGE
        pages = min(int(ceil(pages)), MAX_PAGES_NUMBER)

        url = response.url
        url = set_parameter(url, 'size', 20)
        for index in range(1, pages + 1):
            url = set_parameter(url, 'page', index)
            yield Request(url, self.parse)

    # Tier 4
    # Create car-specific requests
    def parse(self, response):
        try:
            if not self.deep_parse_enabled:
                for record in self.shallow_parse(response):
                    yield record
        except ValueError:
            self.logger.warning("Invalid data on %s" % response.url)
            yield Request(response.url, self.parse)

        if self.deep_parse_enabled:
            for url in response.xpath(COMMON_XPATH['car_link']):
                yield self.create_deep_parse_request(response.url, url.extract())

    # Create parse request
    def create_deep_parse_request(self, old_url, new_url):
        new_url = urljoin(old_url, new_url)
        for parameter in ['brand', 'model']:
            value = get_parameter(old_url, PARAMETERS[parameter])
            new_url = set_parameter(new_url, PARAMETERS[parameter], value)
        return Request(new_url, self.deep_parse)

    # Parse records from page
    def shallow_parse(self, response):
        records = []

        for car in response.xpath(COMMON_XPATH['car']):
            record = dict()

            brand_key = get_parameter(response.url, PARAMETERS['brand'])
            record['make'] = self.brands[brand_key]
            model_key = get_parameter(response.url, PARAMETERS['model'])
            record['model'] = self.models[brand_key][model_key]

            for field, xpath in SHALLOW_PARSE_FIELDS_XPATH.items():
                record[field] = car.xpath(xpath).extract_first()

            if not self.is_valid(record):
                raise ValueError

            records.append(self.shallow_normalization(record))

        return records

    # Parse page and initialize next request
    def deep_parse(self, response):
        # Record processing
        record = dict()
        record['origin_link'] = clear_parameters(response.url)

        brand_key = get_parameter(response.url, PARAMETERS['brand'])
        record['make'] = self.brands[brand_key]
        model_key = get_parameter(response.url, PARAMETERS['model'])
        record['model'] = self.models[brand_key][model_key]

        data = response.xpath('//main')
        for field, xpath in DEEP_PARSE_FIELDS_XPATH.items():
            record[field] = data.xpath(xpath.decode("utf-8")).extract_first()

        # Parking sensors
        parking_equipments = []
        for item, xpath in PARKING_SENSORS.items():
            if len(data.xpath(xpath.decode("utf-8"))) > 0:
                parking_equipments.append(item)
        if len(parking_equipments) > 0:
            record['parking_sensors'] = ', '.join(parking_equipments)
        else:
            record['parking_sensors'] = None

        # Airbags
        airbags = []
        for item, xpath in AIRBAGS.items():
            if len(data.xpath(xpath.decode("utf-8"))) > 0:
                airbags.append(item)
        if len(airbags) > 0:
            record['airbags'] = ', '.join(airbags)
        else:
            record['airbags'] = None

        if not self.is_valid(record):
            self.logger.info("Invalid response from %s" % response.url)
            return Request(response.url, self.parse)

        return self.deep_normalization(record)

    # Validate the response
    @staticmethod
    def is_valid(record):
        for field in REQUIRED_FIELDS:
            if record[field] is None:
                return False
        return True

    # Format the given record
    def shallow_normalization(self, record):

        # Origin link
        record['origin_link'] = ORIGIN_LINK + record['origin_link']

        # Convert to integer
        integer_values = {
            'sales_price_incl_vat': 0,
            'mileage': 0,
            'power_in_kw': 0,
            'power_in_ps': 1,
            'co2_emissions': 0,
            'number_of_previous_owners': 0
        }
        for field, index in integer_values.items():
            if record[field] is not None:
                record[field] = self.extract_nth_integer(record[field], index)

        # Convert to decimal
        decimal_values = {
            'fuel_consumption_comb': 0
        }
        for field, index in decimal_values.items():
            if record[field] is not None:
                record[field] = self.extract_nth_decimal(record[field], index)

        # Currency
        record['currency'] = search('\S', record['currency']).group(0)

        # Convert to date
        date_values = [
            'first_registration'
        ]
        for field in date_values:
            if record[field] is not None:
                record[field] = self.extract_date(record[field])

        # Remove leading and trailing blank lines
        for key in record:
            if type(record[key]) is str:
                record[key] = record[key].strip('\n')

        return record

    # Format the given record
    def deep_normalization(self, record):

        # Convert to integer
        integer_values = [
            'sales_price_incl_vat',
            'mileage',
            'cubic_capacity',
            'power_in_kw',
            'power_in_ps',
            'co2_emissions',
            'number_of_seats',
            'number_of_doors',
            'number_of_previous_owners'
        ]
        for field in integer_values:
            if record[field] is not None:
                record[field] = self.extract_nth_integer(record[field], 0)

        # Convert to decimal
        decimal_values = [
            'fuel_consumption_comb',
            'fuel_consumption_city',
            'fuel_consumption_country'
        ]
        for field in decimal_values:
            if record[field] is not None:
                record[field] = self.extract_nth_decimal(record[field], 0)

        # Currency
        record['currency'] = search('\S', record['currency']).group(0)

        # Convert to date
        date_values = [
            'first_registration',
            'service_maintenance'
        ]
        for field in date_values:
            if record[field] is not None:
                record[field] = self.extract_date(record[field])

        # Remove leading and trailing blank lines
        for key in record:
            if type(record[key]) is str:
                record[key] = record[key].strip('\n')

        # Normalize 'marketing_headline' field
        headline = record['marketing_headline']
        headline = headline.replace(record['make'], '', 1)
        headline = headline.replace(record['model'], '', 1)
        headline = headline.strip()
        record['marketing_headline'] = headline

        # Energy efficiency class
        co2_efficiency = record['energy_efficiency_class']
        if co2_efficiency is not None:
            co2_efficiency = search('envkv(\w+).svg$', co2_efficiency).group(1)
        record['energy_efficiency_class'] = co2_efficiency

        return record

    # Get the first number from input string
    @staticmethod
    def extract_nth_integer(value, index):
        value = findall('[\d.,]+', value)
        if len(value) == 0:
            return None
        value = value[index]
        value = value.replace(',', '')
        value = value.replace('.', '')
        return int(value)

    # Get the first number from input string
    @staticmethod
    def extract_nth_decimal(value, index):
        value = findall('[\d.,]+', value)
        if len(value) == 0:
            return None
        value = value[index]
        value = value.replace(',', '.')
        return decimal.Decimal(value)

    # Get the first date from input string
    @staticmethod
    def extract_date(value):
        value = search('\d{2}/\d{4}', value)
        if value is None:
            return None
        return value.group(0)

    # Get the phone number from input string
    @staticmethod
    def extract_phone_number(value):
        return value.replace('tel:', '')

    # Check if the given request matches more cars than can be accessed
    @staticmethod
    def is_filter_required(response):
        return AutoScoutParser.get_quantity(response) > MAX_ACCESSIBLE_CARS_NUMBER

    # Get price limits from URL
    @staticmethod
    def get_price_limits(url):
        price_from = int(get_parameter(url, PARAMETERS['price_from']))
        price_to = int(get_parameter(url, PARAMETERS['price_to']))
        return price_from, price_to

    # Add price limits to the given URL
    @staticmethod
    def set_price_limits(url, price_from, price_to):
        url = set_parameter(url, PARAMETERS['price_from'], price_from)
        url = set_parameter(url, PARAMETERS['price_to'], price_to)
        return url

    # Get mileage limits from URL
    @staticmethod
    def get_mileage_limits(url):
        mileage_from = int(get_parameter(url, PARAMETERS['mileage_from']))
        mileage_to = int(get_parameter(url, PARAMETERS['mileage_to']))
        return mileage_from, mileage_to

    # Add mileage limits to the given URL
    @staticmethod
    def set_mileage_limits(url, mileage_from, mileage_to):
        url = set_parameter(url, PARAMETERS['mileage_from'], mileage_from)
        url = set_parameter(url, PARAMETERS['mileage_to'], mileage_to)
        return url

    # Get models from response
    @staticmethod
    def get_models(response):
        models = list()
        for model in response.xpath(COMMON_XPATH['models']):
            model_key = model.xpath('./@key').extract_first()
            model_value = model.xpath('./@value').extract_first()
            if AutoScoutParser.is_sub_model(model_value):
                if not AutoScoutParser.is_sub_model(models[-1][1]):
                    del models[-1]
            models.append([model_key, model_value])
        for i in range(len(models)):
            models[i][1] = models[i][1].strip()
        return dict(models)

    # Check if the given model is the sub model
    @staticmethod
    def is_sub_model(model):
        return search("^\xa0{2}", model) is not None

    # Create dictionary which describes the following situation:
    # Some records cannot be reached without applying additional filters
    def get_quantity_error_info(self, response):
        brand_key = get_parameter(response.url, PARAMETERS['brand'])
        price = int(get_parameter(response.url, PARAMETERS['price_from']))
        model_key = get_parameter(response.url, PARAMETERS['model'])
        return {
            'error': 'Too many cars with such parameters.',
            'brand_key': brand_key,
            'brand': self.brands[brand_key],
            'model_key': model_key,
            'model': self.models[brand_key][model_key],
            'price': price,
            'quantity': self.get_quantity(response)
        }

    # Get the quantity of records matching the given filter
    @staticmethod
    def get_quantity(response):
        quantity = response.xpath(COMMON_XPATH['quantity']).extract_first()
        quantity = search("[\d.]+", quantity).group(0)
        quantity = quantity.replace(".", "")
        return int(quantity)
