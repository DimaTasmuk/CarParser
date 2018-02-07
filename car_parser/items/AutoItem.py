import scrapy


class AutoItem(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()
    price_brutto = scrapy.Field()
    price_netto = scrapy.Field()

    details_link = scrapy.Field()
    image_url = scrapy.Field()

    reg_date = scrapy.Field()
    mileage = scrapy.Field()
    fuel_type = scrapy.Field()
    fuel_consumption = scrapy.Field()
    co2_emission = scrapy.Field()
    power_kW = scrapy.Field()
    power_PS = scrapy.Field()
    gearbox_type = scrapy.Field()
    state = scrapy.Field()

    seller_company = scrapy.Field()
    seller_location = scrapy.Field()
    seller_phone = scrapy.Field()

    # don't have
    # engine_capacity = scrapy.Field()
    # electricity_consumption = scrapy.Field()
    # number_of_previous_owners = scrapy.Field()
    # seller_country = scrapy.Field()
    # seller = scrapy.Field()
