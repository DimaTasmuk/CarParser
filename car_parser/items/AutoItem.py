import scrapy


class AutoItem(scrapy.Item):
    id = scrapy.Field()
    marketing_headline = scrapy.Field()
    sales_price_incl_vat = scrapy.Field()
    sales_price_excl_vat = scrapy.Field()
    mileage = scrapy.Field()
    power_in_kw = scrapy.Field()
    power_in_ps = scrapy.Field()
    fuel = scrapy.Field()
    fuel_consumption_comb = scrapy.Field()
    co2_emission = scrapy.Field()
    gearbox = scrapy.Field()
    first_registration = scrapy.Field()
