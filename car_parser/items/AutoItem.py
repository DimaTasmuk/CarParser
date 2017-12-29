import scrapy


class AutoItem(scrapy.Item):
    title = scrapy.Field()
    registrationDate = scrapy.Field()
    mileage = scrapy.Field()
    power = scrapy.Field()
    fuelType = scrapy.Field()
    gearbox = scrapy.Field()
    price = scrapy.Field()
    seller = scrapy.Field()
    seller_city = scrapy.Field()
    seller_phone = scrapy.Field()
