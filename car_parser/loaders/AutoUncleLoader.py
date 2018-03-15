from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose, Join


def get_first_splitted(line):
    return line.split(" ")[0]


def get_first_item(list):
    return list[0].strip()


class AutoUncleLoader(ItemLoader):
    default_output_processor = TakeFirst()

    currency_out = Compose(get_first_item, get_first_splitted)
    mileage_out = Compose(get_first_item, lambda v: v.replace('.', ''))
    co2_emission_out = Compose(get_first_item, get_first_splitted)
    power_in_ps_out = Compose(get_first_item, get_first_splitted)
    emission_class_out = Join(separator=' ')
    marketing_headline_out = Compose(get_first_item)
