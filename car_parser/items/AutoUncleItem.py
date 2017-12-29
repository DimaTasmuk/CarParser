import scrapy


class AutoUncleItem(scrapy.Item):
    brand = scrapy.Field()
    title = scrapy.Field()
    year = scrapy.Field()
    km = scrapy.Field()
    engine = scrapy.Field()
    fuel_efficiency = scrapy.Field()
    co2_emission = scrapy.Field()
    location = scrapy.Field()
    price = scrapy.Field()
    advert_link = scrapy.Field()