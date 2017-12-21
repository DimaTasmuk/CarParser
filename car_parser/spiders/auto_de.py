import scrapy
from car_parser.items.AutoDeCarItem import AutoDeCarItem
from car_parser.loaders.AutoDeLoader import AutoDeLoader


class AutoDeParser(scrapy.Spider):
    name = "autode_parser"
    start_urls = ["http://www.auto.de/search/findoffer?sci%5B%5D=&spra=&sma=&sg=&srdi=&sft=&sz=&src=1&"
                  "vt%5B%5D=1&vt%5B%5D=2&vt%5B%5D=3&vt%5B%5D=4&vt%5B%5D=5&vt%5B%5D=6&vt%5B%5D=7&"
                  "vt%5B%5D=8&vt%5B%5D=99&searchFast=Fahrzeug+suchen&srtcbd=0_asc"]
    brand_id = ['11149', '51', '11220']

    list_cars_info = list()

    def __init__(self, brand_id, **kwargs):
        self.brand_id = brand_id
        super(AutoDeParser, self).__init__(brand_id, **kwargs)

    def parse(self, response):
        yield response.follow("#brandModelLayer", self.parse_brands)

    def parse_brands(self, response):
        # try:
        #     brand_id = [response.url.split("brand_id=")[1].split("&")[0]]
        # except:
        #     brand_id = ['11149', '51', '11220']
        print(self.brand_id)
        model_keys = set(response.css("div.brandModelLayer div.autoForm ul.brandModel").xpath('//select[@id="sci"]').css("select.brandSearch option::attr(value)").extract())
        for model_key in model_keys:
            if model_key in [self.brand_id]:
                url = response.url.split("sci%5B%5D=")[0] + "sci%5B%5D=" + model_key + response.url.split("sci%5B%5D=")[1]
                yield response.follow(url, self.parse_cars)

    def parse_cars(self, response):
        cars = response.css("ul.vehicleList li.contentDesc a.vehicleOffersBox")
        for car in cars:
            loader = AutoDeLoader(item=AutoDeCarItem(), selector=car)
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
