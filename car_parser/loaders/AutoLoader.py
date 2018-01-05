from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose, Join


class AutoLoader(ItemLoader):
    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()

    price_in = TakeFirst()
    price_out = Compose(lambda p: int(p[0].replace('.', '')))
    details_link_out = Join(separator='')
    fuel_consumption_out = TakeFirst()
    co2_emission_out = TakeFirst()
    seller_phone_in = Compose(lambda v: v[-1], unicode.strip)
