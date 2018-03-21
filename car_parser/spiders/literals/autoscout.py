# coding=utf-8

MAX_CARS_PER_PAGE = 20.0
MAX_PAGES_NUMBER = 20
MAX_ACCESSIBLE_CARS_NUMBER = MAX_PAGES_NUMBER * MAX_CARS_PER_PAGE

MAX_PRICE = 1000000000
MIN_PRICE = 0

MAX_MILEAGE = 10000000
MIN_MILEAGE = 0

ORIGIN_LINK = 'https://www.autoscout24.de'

PARAMETERS = {
    'brand':
        'mmvmk0',

    'model':
        'mmvmd0',

    'price_from':
        'pricefrom',

    'price_to':
        'priceto',

    'mileage_from':
        'kmfrom',

    'mileage_to':
        'kmto'
}

OTHERS_ELEMENT_ID = 'Sonstige'

COMMON_XPATH = {
    'brands':
        "//as24-grouped-items-data-source"
        "//item",

    'models':
        "//as24-autocomplete[@data-role='model-selector']"
        "/as24-plain-data-source"
        "/item",

    'car_link':
        "//div[@class='cl-list-element cl-list-element-gap']"
        "//div[@class='cldt-summary-titles']"
        "//a"
        "/@href",

    'quantity':
        "//span[@id='resultsSummary']"
        "/text()",

    'car':
        "//div[@data-item-name='listing-summary-container']"
}


DEEP_PARSE_FIELDS_XPATH = {
    'marketing_headline':
        "./div[@class='cldt-headline']"
        "/div"
        "/div"
        "/h1"
        "/text()",

    'sales_price_incl_vat':
        "./div[contains(@class, 'cldt-stage')]"
        "/div[@class='cldt-stage-data']"
        "/div[@class='cldt-stage-headline']"
        "/div[@class='cldt-price']"
        "/h2"
        "/text()",

    'currency':
        "./div[contains(@class, 'cldt-stage')]"
        "/div[@class='cldt-stage-data']"
        "/div[@class='cldt-stage-headline']"
        "/div[@class='cldt-price']"
        "/h2"
        "/text()",

    'body_type':
        "./div[@class='cldt-headline']"
        "/div"
        "/div"
        "/h4"
        "/text()",

    'mileage':
        "./div[contains(@class, 'cldt-stage')]"
        "/div[@class='cldt-stage-data']"
        "/div[@class='cldt-stage-basic-data-and-highlights']"
        "/div[@class='cldt-stage-basic-data']"
        "/div[1]"
        "/span[1]"
        "/text()",

    'cubic_capacity':
        ".//dt[text()='Hubraum']"
        "/following-sibling::dd[1]"
        "/text()",

    'power_in_kw':
        "./div[contains(@class, 'cldt-stage')]"
        "/div[@class='cldt-stage-data']"
        "/div[@class='cldt-stage-basic-data-and-highlights']"
        "/div[@class='cldt-stage-basic-data']"
        "/div[3]"
        "/span[1]"
        "/text()",

    'power_in_ps':
        "./div[contains(@class, 'cldt-stage')]"
        "/div[@class='cldt-stage-data']"
        "/div[@class='cldt-stage-basic-data-and-highlights']"
        "/div[@class='cldt-stage-basic-data']"
        "/div[3]"
        "/span[2]"
        "/text()",

    'fuel':
        ".//dt[text()='Kraftstoff']"
        "/following-sibling::dd[1]"
        "/text()",

    'fuel_consumption_comb':
        ".//dt[text()='Kraftstoffverbrauch']"
        "/following-sibling::dd[1]"
        "/div[contains(text(), 'komb')]"
        "/text()",

    'fuel_consumption_city':
        ".//dt[text()='Kraftstoffverbrauch']"
        "/following-sibling::dd[1]"
        "/div[contains(text(), 'innerorts')]"
        "/text()",

    'fuel_consumption_country':
        ".//dt[text()='Kraftstoffverbrauch']"
        "/following-sibling::dd[1]"
        "/div[contains(text(), 'außerorts')]"
        "/text()",

    'co2_emissions':
        ".//dt[text()='CO2-Emissionen']"
        "/following-sibling::dd[1]"
        "/text()",

    'energy_efficiency_class':
        ".//div[@class='cldt-co2-efficiency']"
        "//img"
        "/@src",

    'number_of_seats':
        ".//dt[text()='Sitzplätze']"
        "/following-sibling::dd[1]"
        "/text()",

    'number_of_doors':
        ".//dt[text()='Anzahl Türen']"
        "/following-sibling::dd[1]"
        "/text()",

    'gearbox':
        ".//dt[text()='Getriebeart']"
        "/following-sibling::dd[1]"
        "/text()",

    'emission_class':
        ".//dt[text()='Schadstoffklasse']"
        "/following-sibling::dd[1]"
        "/text()",

    'emission_sticker':
        ".//dt[text()='Feinstaubplakette']"
        "/following-sibling::dd[1]"
        "/text()",

    'first_registration':
        "./div[contains(@class, 'cldt-stage')]"
        "/div[@class='cldt-stage-data']"
        "/div[@class='cldt-stage-basic-data-and-highlights']"
        "/div[@class='cldt-stage-basic-data']"
        "/div[2]"
        "/span[1]"
        "/text()",

    'number_of_previous_owners':
        "./div[contains(@class, 'cldt-stage')]"
        "/div[@class='cldt-stage-data']"
        "/div[@class='cldt-stage-basic-data-and-highlights']"
        "/div[@class='cldt-stage-basic-data']"
        "/div[2]"
        "/span[2]"
        "/text()",

    'service_maintenance':
        ".//dt[text()='HU Prüfung']"
        "/following-sibling::dd[1]"
        "/text()",

    'climate_control':
        ".//span[text()='Klimaautomatik']"
        "/text()",

    'colour_manufacturer':
        ".//dt[text()='Farbe laut Hersteller']"
        "/following-sibling::dd[1]"
        "/text()",

    'colour':
        ".//dt[text()='Außenfarbe']"
        "/following-sibling::dd[1]"
        "/text()",

    'interior':
        ".//dt[text()='Innenausstattung']"
        "/following-sibling::dd[1]"
        "/text()"
}

PARKING_SENSORS = {
    'Einparkhilfe':
        ".//span[text()='Einparkhilfe']"
        "/text()",

    'hinten':
        ".//span[text()='Einparkhilfe Sensoren hinten']"
        "/text()",

    'vorne':
        ".//span[text()='Einparkhilfe Sensoren vorne']"
        "/text()",

    'kamera':
        ".//span[text()='Einparkhilfe Kamera']"
        "/text()",

    'selbstlenkendes System':
        ".//span[text()='Einparkhilfe selbstlenkendes System']"
        "/text()"
}

AIRBAGS = {
    'Beifahrerairbag':
        ".//span[text()='Beifahrerairbag']"
        "/text()",

    'Fahrerairbag':
        ".//span[text()='Fahrerairbag']"
        "/text()",

    'hinten':
        ".//span[text()='Airbag hinten']"
        "/text()",

    'Kopfairbag':
        ".//span[text()='Kopfairbag']"
        "/text()",

    'Seitenairbag':
        ".//span[text()='Seitenairbag']"
        "/text()"
}

SHALLOW_PARSE_FIELDS_XPATH = {
    'origin_link':
        "./div[1]"
        "/div[1]"
        "/div[1]"
        "/a[@data-item-name='detail-page-link']"
        "/@href",

    'marketing_headline':
        ".//h2[contains(@class, 'cldt-summary-version')]"
        "/text()",

    'sales_price_incl_vat':
        "./div[1]"
        "/div[3]"  
        "/div[1]"
        "/span[@data-item-name='price']"
        "/text()[1]",

    'currency':
        "./div[1]"
        "/div[3]"
        "/div[1]"
        "/span[@data-item-name='price']"
        "/text()[1]",

    'mileage':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[1][not(@data-placeholder)]"
        "/text()",

    'power_in_kw':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[3][not(@data-placeholder)]"
        "/text()",

    'power_in_ps':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[3][not(@data-placeholder)]"
        "/text()",

    'fuel':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[7][not(@data-placeholder)]"
        "/text()",

    'fuel_consumption_comb':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[8][not(@data-placeholder)]"
        "/text()",

    'co2_emissions':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[9][not(@data-placeholder)]"
        "/text()",

    'gearbox':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[6][not(@data-placeholder)]"
        "/text()",

    'first_registration':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[2][not(@data-placeholder)]"
        "/text()",

    'number_of_previous_owners':
        "./div[1]"
        "/div[3]"
        "/div[2]"
        "/ul"
        "/li[5][not(@data-placeholder)]"
        "/text()"
}

# TODO: add fields
REQUIRED_FIELDS = [
    'make',
    'model',
    'sales_price_incl_vat',
    'currency'
]