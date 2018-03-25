from string import join

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose, Join


def filter_empty(line):
    line = line.strip()
    if len(line) > 0 and line.lower() != "andere":
        return line


def capitalize_all_words(line):
    capitalized_words = []
    for word in line.split(", "):
        capitalized_words.append(word[0].upper() + word[1:])
    return join(capitalized_words, ', ')


def replace_dot(number):
    return number[0].replace(".", "")


class AutoLoader(ItemLoader):
    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()

    sales_price_incl_vat_out = Compose(replace_dot)
    sales_price_excl_vat_out = Compose(replace_dot)
    currency_out = Compose(lambda c: c[0][-1])
    mileage_out = Compose(replace_dot)
    cubic_capacity_in = TakeFirst()
    cubic_capacity_out = Compose(replace_dot)
    colour_in = MapCompose(filter_empty, capitalize_all_words)
    interior_in = MapCompose(filter_empty, capitalize_all_words)
    interior_out = Join(separator=', ')
