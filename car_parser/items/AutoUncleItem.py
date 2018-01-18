import scrapy


class AutoUncleItem(scrapy.Item):
    brand = scrapy.Field()
    model = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    details_link = scrapy.Field()
    image_url = scrapy.Field()
    reg_date = scrapy.Field()
    mileage = scrapy.Field()
    fuel_type = scrapy.Field()
    fuel_consumption = scrapy.Field()
    co2_emission = scrapy.Field()
    power = scrapy.Field()
    location = scrapy.Field()
