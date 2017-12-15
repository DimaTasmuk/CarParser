import scrapy


class AutoDeParser(scrapy.Spider):
    name = "autode_parser"
    start_urls = ["http://www.auto.de/search/findoffer?sci%5B%5D=&spra=&sma=&sg=&srdi=&sft=&sz=&src=1&"
                  "vt%5B%5D=1&vt%5B%5D=2&vt%5B%5D=3&vt%5B%5D=4&vt%5B%5D=5&vt%5B%5D=6&vt%5B%5D=7&"
                  "vt%5B%5D=8&vt%5B%5D=99&searchFast=Fahrzeug+suchen&srtcbd=0_asc"]

    def parse(self, response):
        yield response.follow("#brandModelLayer", self.parse_brands)

    def parse_brands(self, response):
        model_keys = set(response.css("div.brandModelLayer div.autoForm ul.brandModel").xpath('//select[@id="sci"]').css("select.brandSearch option::attr(value)").extract())
        for model_key in model_keys:
            if model_key in ['11149', '51', '11220']:
                url = response.url.split("sci%5B%5D=")[0] + "sci%5B%5D=" + model_key + response.url.split("sci%5B%5D=")[1]
                yield response.follow(url, self.parse_cars)

    def parse_cars(self, response):
        cars = response.css("ul.vehicleList li.offers")
        for car in cars:
            #TODO: problem with title. Sometimes not found headline
            title = car.css(".headline::text").extract_first().strip()
            vehicle_data = car.css("technicalData p")
            try:
                registrationDate = vehicle_data.xpath("//span[@data-content=registrationDate]").extract_first()
            except AttributeError:
                registrationDate = ''
            try:
                mileage = vehicle_data.xpath("//span[@data-content=mileage]").extract_first()
            except AttributeError:
                mileage = ''
            try:
                power = vehicle_data.xpath("//span[@data-content=power]").extract_first()
            except AttributeError:
                power = ''
            try:
                fuelType = vehicle_data.xpath("//span[@data-content=fuelType]").extract_first()
            except AttributeError:
                fuelType = ''
            try:
                gearbox = vehicle_data.xpath("//span[@data-content=gearbox]").extract_first()
            except AttributeError:
                gearbox = ''

            yield {
                'title': title,
                "registrationDate": registrationDate,
                "mileage": mileage,
                "power": power,
                "fuelType": fuelType,
                "gearbox": gearbox
            }
