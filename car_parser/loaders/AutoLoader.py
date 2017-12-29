from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose


class AutoLoader(ItemLoader):
    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()

    seller_phone_in = Compose(lambda v: v[-1], unicode.strip)