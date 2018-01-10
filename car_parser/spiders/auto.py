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

    custom_settings = {
        'ITEM_PIPELINES': {
            'car_parser.pipelines.AutoPipeline': 300
        }
    }

    PARAMETER_BRAND_NAME = "sci%5B%5D="
    PARAMETER_MODEL_NAME = "&spi%5B%5D="

    ORIGIN_LINK = u"www.auto.de"

    # list of keys that specified by user as argument
    specified_brand_keys = list()

    parsed_cars_links = list()

    # key - key of brand or model, value - name of brand or model
    brands = dict()
    models = dict()

    def __init__(self, brand_key=None, **kwargs):
        if brand_key:
            for key in brand_key.split(','):
                self.specified_brand_keys.append(key)
        super(AutoParser, self).__init__(brand_key, **kwargs)

    def parse(self, response):
        """ Follow to form with brands """
        url = self.get_brand_model_form_url(response.url)
        yield response.follow(url, self.parse_brands)

    def parse_brands(self, response):
        """ Parse brand keys and follow to parse models """
        brands = response.css("div.brandModelLayer div.autoForm ul.brandModel")\
            .css("select#sci option")\
            .extract()
        for brand in brands[1:]:  # first element is empty
            key = re.search(r'value="(\d+)"', brand).group(1)
            name = re.search(r'>(.*)<', brand).group(1)
            self.brands[key] = name

            #  parse cars if key is not empty. If brand specified by user - verify that key in that list of brand keys
            if key != "" and \
                    ((self.specified_brand_keys and key in self.specified_brand_keys) or not self.specified_brand_keys):
                # get url for car filtered by brand
                page_url = self.get_url_with_parameter_key(response, self.PARAMETER_BRAND_NAME, key)

                # get url for parse models
                url = self.get_brand_model_form_url(page_url)
                yield response.follow(url, self.parse_model)

    def parse_model(self, response):
        """ Parse model keys and follow to parse cars """
        models = response.css("div.brandModelLayer div.autoForm ul.brandModel")\
            .css("select#spi-for-sci option")\
            .extract()
        for model in models[1:]:  # first element is empty
            key = re.search(r'value="((\d\|?)+-\d+)"', model).group(1)
            name = re.search(r'>(.*)<', model).group(1)
            self.models[key] = name
            if key != "":
                url = response.url + self.PARAMETER_MODEL_NAME + key
                yield response.follow(url, self.parse_cars)

    def parse_cars(self, response):
        brand_key, model_key = self.get_brand_model_key_from_url(response.url)
        brand = self.brands[brand_key]
        model = self.models[model_key]

        cars = response.css("ul.vehicleOffers.vehicleList li.contentDesc")\
            .xpath("a[contains(@title, '" + brand + ' ' + model + "')]")
        for car in cars:
            headline = car.css("*.headline.ellipsisText::text").extract_first()

            loader = AutoLoader(item=AutoItem(), selector=car)
            loader.add_value('brand', brand)
            loader.add_value('model', model)
            loader.add_value('title', self.get_title(brand, model, headline))
            loader.add_css('price', "span.priceBig::text", re='\S+')

            loader.add_value('details_link', self.ORIGIN_LINK)
            loader.add_css('details_link', "a.vehicleOffersBox::attr(href)")

            loader.add_css('image_url', "div.iconView img.image::attr(src)")

            vehicle_data_loader = loader.nested_css("div.technicalData")
            vehicle_data_loader.add_css('reg_date', "span[data-content*=registrationDate]::text")
            vehicle_data_loader.add_css('mileage', "span[data-content*=mileage]::text")
            vehicle_data_loader.add_css('fuel_type', "span[data-content*=fuelType]::text")
            vehicle_data_loader.add_css('fuel_consumption', "div::text", re='\S+ l/100km')
            vehicle_data_loader.add_css('co2_emission', "div::text", re='\S+ CO2/km')
            vehicle_data_loader.add_css('power', "span[data-content*=power]::text")
            vehicle_data_loader.add_css('gearbox_type', "span[data-content*=gearbox]::text")
            vehicle_data_loader.add_css('state', "span[data-content*=vehicleType]::text")

            seller_loader = loader.nested_css('div.vehicleOffersDealer div p:nth-child(2)')
            seller_loader.add_css('seller_company', 'p:nth-child(2)::text')
            seller_loader.add_css('seller_location', 'span[data-content*=city]::text')
            seller_loader.add_css('seller_phone', "p:nth-child(2)::text")

            link = loader.get_collected_values("details_link")
            if link not in self.parsed_cars_links:
                self.parsed_cars_links.append(link)
                yield loader.load_item()

        next_page = response.css("div.pagNext a.icon-right-dir::attr(href)").extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.parse_cars)

    def get_url_with_parameter_key(self, response, parameter, key):
        return response.url.split(parameter)[0] + \
               parameter + \
               key + \
               response.url.split(parameter)[1]

    def get_brand_model_form_url(self, url):
        return url + "#brandModelLayer"

    def get_brand_model_key_from_url(self, url):
        match_obj = re.search('%5D=((\d(?:%7C|\|)?)+-(\d+))', url)
        return match_obj.group(3), match_obj.group(1).replace("%7C", "|")

    def get_title(self, brand, model, headline):
        try:
            return re.search(brand + " " + model + "(.*)", headline).group(1).strip()
        except:
            return ""
