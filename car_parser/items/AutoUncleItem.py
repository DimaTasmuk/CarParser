import scrapy


class AutoUncleItem(scrapy.Item):
    origin_link = scrapy.Field()
    make = scrapy.Field()
    model = scrapy.Field()
    marketing_headline = scrapy.Field()
    sales_price_incl_vat = scrapy.Field()
    currency = scrapy.Field()
    mileage = scrapy.Field()
    cubic_capacity = scrapy.Field()
    power_in_ps = scrapy.Field()
    fuel = scrapy.Field()
    fuel_consumption_comb = scrapy.Field()
    co2_emission = scrapy.Field()
    energy_efficiency_class = scrapy.Field()
    emission_class = scrapy.Field()
    first_registration = scrapy.Field()
    climate_control = scrapy.Field()
    gearbox = scrapy.Field()
    parking_sensors = scrapy.Field()
