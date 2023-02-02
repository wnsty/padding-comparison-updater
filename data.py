class Row():
    def __init__(
        self,
        retailer: str = None,
        brand: str = None,
        name: str = None,
        size: str = None,
        waist_low: str = None,
        waist_high: str = None,
        price: str = None,
        shipping: str = None,
        bulk_discount: str = None,
        units_per_bag: str = None,
        bags_per_case: str = None,
        ml_per_unit: str = None,
        unit_price: str = None,
        total_price: str = None,
        in_stock: str = None,
        notes: str = None,
        url: str = None,
    ) -> None:
        self.retailer = retailer
        self.brand = brand
        self.name = name
        self.size = size
        self.waist_low = waist_low
        self.waist_high = waist_high
        self.price = price
        self.shipping = shipping
        self.bulk_discount = bulk_discount
        self.units_per_bag = units_per_bag
        self.bags_per_case = bags_per_case
        self.ml_per_unit = ml_per_unit
        self.unit_price = unit_price
        self.total_price = total_price
        self.in_stock = in_stock
        self.notes = notes
        self.url = url


class Column:
    def __init__(self, price: str = None, in_stock: str = None, waist_low: str = None, waist_high: str = None, units: str = None) -> None:
        self.price = price
        self.in_stock = in_stock
        self.waist_low = waist_low
        self.waist_high = waist_high
        self.units = units


# tykeables => product url, variant id
# myinnerbaby => product url, variant id
# bambino => product url, variant id

# abu => variant url
# lfb => variant url

# northshore => store url
# xpmedical => store url, sku

# rearz = selenium
# amazon => selenium?

product_list = {
	'abu': {
		'prefix': 'https://us.abuniverse.com/wp-json/wc/store/products/',
		'key': [
			'357662',
			'114049',
		],
	},
	'amazon': {

	},
	'awwsocute': {},
	'bambino': {
		'prefix': 'https://bambinodiapers.com/products/',
		'key': {
			'endpoint': 'magnifico.json',
			'variants': [
				35161377996956,
				41894915899571,
			]
		},
	},
	'ebay': {},
	'incontrol': {},
	'landofgenie': {},
	'littleforbig': {
		'prefix': 'https://www.littleforbig.com/wp-json/wc/store/products/',
		'key': [
			'155309',
		],
	},
	'myinnerbaby': {
		'prefix': 'https://myinnerbaby.com/products/',
		'key': {
			'endpoint': 'cc-fairyland-adult-diaper.json',
			'variants': [
				7789315096793,
				7789315096793,
			]
		},
	},
	'northshore': {
		'prefix': 'https://www.northshorecare.com/adult-diapers/adult-diapers-with-tabs/northshore-megamax-tab-style-briefs/',
		'key': [
			'northshore-megamax-tab-style-briefs-small-case40-410s',
			'northshore-megamax-tab-style-briefs-medium-case40-410s',
		],
	},
	'rearz': {

	},
	'tykables': {
		'prefix': 'https://tykables.com/products/',
		'key': {
			'endpoint': 'waddler-diapers.json',
			'variants': [
				39877711036489,
				39399105036361,
			]
		},
	},
	'xpmedical': {

	},
}