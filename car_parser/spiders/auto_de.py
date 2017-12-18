import scrapy


class AutoDeParser(scrapy.Spider):
    name = "autode_parser"
    start_urls = ["http://www.auto.de/search/findoffer?sci%5B%5D=&spra=&sma=&sg=&srdi=&sft=&sz=&src=1&"
                  "vt%5B%5D=1&vt%5B%5D=2&vt%5B%5D=3&vt%5B%5D=4&vt%5B%5D=5&vt%5B%5D=6&vt%5B%5D=7&"
                  "vt%5B%5D=8&vt%5B%5D=99&searchFast=Fahrzeug+suchen&srtcbd=0_asc"]

    list_cars_info = list()

    def parse(self, response):
        yield response.follow("#brandModelLayer", self.parse_brands)

    def parse_brands(self, response):
        model_keys = set(response.css("div.brandModelLayer div.autoForm ul.brandModel").xpath('//select[@id="sci"]').css("select.brandSearch option::attr(value)").extract())
        for model_key in model_keys:
            if model_key in ['11149', '51', '11220']:
                url = response.url.split("sci%5B%5D=")[0] + "sci%5B%5D=" + model_key + response.url.split("sci%5B%5D=")[1]
                yield response.follow(url, self.parse_cars)

    def parse_cars(self, response):
        cars = response.css("ul.vehicleList li.contentDesc a.vehicleOffersBox")
        for car in cars:
            try:
                title = car.css(".headline::text").extract_first().strip()
            except:
                print "adgadg"
            vehicle_data = car.css("div.technicalData p span")
            try:
                registrationDate = vehicle_data.css("span[data-content*=registrationDate]::text").extract_first().strip()
            except AttributeError:
                registrationDate = ''
            try:
                mileage = vehicle_data.css("span[data-content*=mileage]::text").extract_first().strip()
            except AttributeError:
                mileage = ''
            try:
                power = vehicle_data.css("span[data-content*=power]::text").extract_first().strip()
            except AttributeError:
                power = ''
            try:
                fuelType = vehicle_data.css("span[data-content*=fuelType]::text").extract_first().strip()
            except AttributeError:
                fuelType = ''
            try:
                gearbox = vehicle_data.css("span[data-content*=gearbox]::text").extract_first().strip()
            except AttributeError:
                gearbox = ''
            price = response.css("span.priceBig::text").extract_first().strip()

            vehicleOffersDealer = car.css("div.vehicleOffersDealer div p")
            seller = vehicleOffersDealer[1].css("p::text").extract_first().strip()
            seller_city = vehicleOffersDealer[1].css("span[data-content*=city]::text").extract_first().strip()
            seller_phone = vehicleOffersDealer[1].css("p::text").extract()[-1].strip()

            info = 'title:{}, registrationDate:{}, mileage:{}, power:{}, fuelType:{}, gearbox:{}, price:{},' \
                   'seller:{}, seller_city:{}, seller_phone:{}'. \
                format(title.encode('utf-8'), registrationDate.encode('utf-8'), mileage.encode('utf-8'),
                       power.encode('utf-8'), fuelType.encode('utf-8'), gearbox.encode('utf-8'), price.encode('utf-8'),
                       seller.encode('utf-8'), seller_city.encode('utf-8'), seller_phone.encode('utf-8'))
            if info not in self.list_cars_info:
                self.list_cars_info.append(info)
                yield {
                    'title': title,
                    "registrationDate": registrationDate,
                    "mileage": mileage,
                    "power": power,
                    "fuelType": fuelType,
                    "gearbox": gearbox,
                    "price": price,
                    "seller": seller,
                    "seller_city": seller_city,
                    "seller_phone": seller_phone
                }

        next_page = response.css("div.pagNext a.icon-right-dir::attr(href)").extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.parse_cars)
