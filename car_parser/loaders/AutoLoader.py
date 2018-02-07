from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose, Join


class AutoLoader(ItemLoader):
    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()

    price_brutto_out = Compose(lambda p: int(p[0].replace('.', '')))
    price_netto_out = Compose(lambda p: int(p[0].replace('.', '')))
    details_link_out = Join(separator='')
    seller_phone_out = Compose(lambda v: v[-1], unicode.strip)
