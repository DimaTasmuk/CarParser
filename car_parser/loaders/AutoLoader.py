from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose, Join


def replace_dot(number):
    return number[0].replace(".", "")


class AutoLoader(ItemLoader):
    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()

    sales_price_incl_vat_out = Compose(replace_dot)
    sales_price_excl_vat_out = Compose(replace_dot)
    mileage_out = Compose(replace_dot)
