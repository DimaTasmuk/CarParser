PARAMETERS = {
    'brand': '?s%5Bbrand%5D=',
    'min_price': '&s%5Bmin_price%5D=',
    'max_price': '&s%5Bmax_price%5D=',
    'model': '&s%5Bmodel_name%5D=',
    'body_type': '&s%5Bbody_types%5D%5B%5D=',
    'color': '&s%5Bcolors%5D%5B%5D=',
}

ORIGIN_LINK = u"www.autouncle.de"

MIN_PRICE = 0
MAX_PRICE = 10000000

MAX_CARS_PER_PAGE = 20
MAX_PAGES_NUMBER = 100
# Max number of cars which we can see with any filters
MAX_ACCESSIBLE_CARS_NUMBER = MAX_PAGES_NUMBER * MAX_CARS_PER_PAGE

TAGS = {
    'climate_control': ['Klimaanlage', 'Klimaautomatik'],
    'gearbox': ['Schaltgetriebe', 'Automatik'],
    'parking_sensors': ['Einparkhilfe']
}