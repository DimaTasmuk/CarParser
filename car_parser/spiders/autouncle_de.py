import scrapy


class AutouncleDe(scrapy.Spider):
    name = "autounclede_parser"
    start_urls = ["https://www.autouncle.de/"]

    parsed_cars = int

    def parse(self, response):
        brands = response.css("select#s_brand option::text").extract()
        for brand in brands:
            if brand == "Toyota":
                yield response.follow(response.url + "de/gebrauchtwagen?s%5Bbrand%5D=" + brand, self.parse_models)

    def parse_models(self, response):
        models = response.css("body script").re(r"'search_brands_models'] = {(\".*)};")[0]

        # models = response.css("select#s_model_name option::text").extract()
        # for model in models:
        #     if model == "RAV4":
        #         yield response.follow(response.url + "&model_name%5D=" + model, self.parse_price)

    def parse_price(self, response):
        self.parsed_cars = 0
        count = self.get_count(response)
        if count > 2000:
            for price in range(0, 200000, 100):
                if self.parsed_cars == count:
                    break
                yield response.follow("s%5Bmin_price%5D=" + str(price) + "s%5Bmax_price%5D=" + str(price + 100), self.parse_car)
        else:
            for car in self.parse_car(response):
                yield car

    def parse_car(self, response):
        for car in response.css("div.car-list-item div.car-details-wrapper"):
            brand = car.css("h3.car-title span b::text").extract_first()
            model = car.css("h3.car-title span span::text").extract_first()
            year = car.css("ul li.year span::text").extract_first()
            km = car.css("ul li.km span::text").extract_first()
            engine = car.css("ul li.engine span::text").extract_first()
            self.parsed_cars += 1
            yield {
                'brand': brand.strip(),
                'model': model.strip(),
                'year': year.strip(),
                'km': km.strip(),
                'engine': engine.strip()
            }

    def get_count(self, response):
        count_line = response.css("div.search-summary span h1::text").extract_first()
        return int(count_line.split(" ")[0])

