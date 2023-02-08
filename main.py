import requests
import re
import json
import yaml
import datetime
from enum import Enum
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from typing import Tuple

ABU_QUANTITIES = {
    10: 'abu_quantity_1',
    40: 'abu_quantity_2',
    80: 'abu_quantity_3',
}

SIZES = {
    'xs': 'XSmall',
    'XS': 'XSmall',
    'XS (Youth)': 'XSmall',
    'X-Small': 'XSMall',
    'Teen': 'XSmall',
    'XS - Teen': 'XSmall',
    's': 'Small',
    'S': 'Small',
    'Small': 'Small',
    's_m': 'SMedium',
    'm': 'Medium',
    'M': 'Medium',
    'Medium': 'Medium',
    'Medium (M)': 'Medium',
    'l': 'Large',
    'L': 'Large',
    'Large': 'Large',
    'Large (L)': 'Large',
    'xl': 'XLarge',
    'XL': 'XLarge',
    'X-Large': 'XLarge',
    'xl-plus': 'XXLarge',
    'XXL': 'XXLarge',
    'XXL - Bariatric': 'XXLarge',
    'Bariatric': 'XXLarge',
}

driver = None

def init_driver():
	global driver
	if driver == None:
		driver = webdriver.Firefox()

def driver_to(url):
	global driver
	init_driver()
	if driver.current_url != url:
		driver.get(url)

def driver_to_reset(url):
	global driver
	init_driver()
	driver.get(url)

def test_fetch(retailer, url):
	results = retailer(url, products[url])
	print(*results, sep='\n')

def get_response(url):
	with requests.get(url) as response:
		if response.status_code != 200:
			print(f'Error: {response.status_code} for {url}')
			return
		return response

def get_soup(url):
	return BeautifulSoup(get_page(url), 'html.parser')

def get_page(url):
	return get_response(url).text

def get_data(url):
	return get_response(url).json()

def await_price_data(old_price_data, get_price_data) -> Tuple[bool, float]:
		timeout = 0
		while timeout < 10:
			timeout += 1
			price_data = get_price_data()
			if price_data != old_price_data:
				return (False, price_data)
			sleep(0.1 * timeout)
		return (True, old_price_data)

def calculate_derived_info(info: dict) -> dict:
    unit_price: float = info['price'] / info['units']
    total_price: float = info['price'] + info['shipping']
    ml_per_unit_price: int = int(info['capacity'] / unit_price)
    return validate_info(info | {
        "ml_per_unit_price": ml_per_unit_price,
        "total_price": total_price,
        "unit_price": unit_price,
    })

def validate_info(info: dict) -> dict:
	if info['backing'] is None:
		print(f'[backing] is None for {info}')
	if info['brand'] is None:
		print(f'[brand] is None for {info}')
	if info['capacity'] is None:
		print(f'[capacity] is None for {info}')
	if info['in_stock'] is None:
		print(f'[in_stock] is None for {info}')
	if info['name'] is None:
		print(f'[name] is None for {info}')
	if info['notes'] is None:
		print(f'[notes] is None for {info}')
	if info['price'] is None:
		print(f'[price] is None for {info}')
	if info['retailer'] is None:
		print(f'[retailer] is None for {info}')
	if info['shipping'] is None:
		print(f'[shipping] is None for {info}')
	if info['size'] is None:
		print(f'[size] is None for {info}')
	if info['tapes'] is None:
		print(f'[tapes] is None for {info}')
	if info['units'] is None:
		print(f'[units] is None for {info}')
	if info['url'] is None:
		print(f'[url] is None for {info}')
	if info['waist_high'] is None:
		print(f'[waist_high] is None for {info}')
	if info['waist_low'] is None:
		print(f'[waist_low] is None for {info}')
	return info


def check_routine(url, product):
	for start, routine in DOMAINS.items():
		if url.startswith(f'https://{start}'):
			attempts = 0
			while attempts < 3:
				attempts += 1
				try:
					return routine(url, product)
				except Exception as e:
					print('error: ' + str(e))


def abu(url, product) -> list[dict]:
    rows = []
    id = product['id']
    info = product['info']
    sizes = product['sizes']
    soup = get_soup(url)

    variations = get_data(
        f'https://us.abuniverse.com/wp-json/wc/store/products/{id}')['variations']
    for variation in variations:
        attributes = variation['attributes']

        # Skip samples and scented variations
        is_sample = attributes[0]['value'] == 'sample'
        is_scented = attributes[2]['value'] == 'no-scent'
        if is_sample or is_scented:
            continue

        size = SIZES[attributes[1]['value']]

        # Get stock data from variation json
        variation_id = variation['id']
        variation_data = get_data(
            f'https://us.abuniverse.com/wp-json/wc/store/products/{variation_id}'
        )

        for units, price_ident in ABU_QUANTITIES.items():
            rows.append(calculate_derived_info(info |sizes[size] | {
                'price': float(re.search('\d*\.\d*', soup.find('label', {'for': price_ident}).string).group()),
                'in_stock': 'Yes' if variation_data['is_in_stock'] else 'No',
                'size': size,
                'units': units,
            }))

    return rows


def amazon(url, product) -> list[dict]:
	info = product['info']
	driver_to(url)
	soup = BeautifulSoup(driver.page_source, 'html.parser')

	price: float = float(soup.find('span', {'class': 'apexPriceToPay'}).find('span', {'class': 'a-offscreen'}).string[1:])
	in_stock: str = 'Yes' if soup.find('span', {'class': 'a-color-success'}) else 'No'

	return [calculate_derived_info(info | {
		'price': price,
		'in_stock': in_stock
	})]


def bambino(url, product) -> list[dict]:
	rows = []
	info = product['info']
	data = get_data(url + '.json')['product']

	for variant in data['variants']:

		# Skip samples
		if variant['option2'].startswith('1 Sample'):
			continue

		size_data = variant['option1']
		size_options = re.search(f"([S|M|L|XL])+\/?([S|M|L|XL]+)?", size_data).groups()
		waist_options = re.search(f"(\d+)\\\"-(\d+)", size_data).groups()

		for size_tag in size_options:
			if size_tag is None:
				continue
			size = SIZES[size_tag]

			rows.append(calculate_derived_info(info | {
				'price': float(variant['price']),
				# TODO: Add in stock selection for Bambino
                'in_stock': 'Maybe',
                'size': size,
                'waist_high': waist_options[1],
                'waist_low': waist_options[0],
                'units': int(variant['option2'][-2:]),
			}))

	return rows


def incontrol(url, product) -> list[dict]:
	def get_price_data():
		return driver.find_element(By.CLASS_NAME, 'price--withoutTax').text

	info = product['info']
	sizes = product['sizes']
	quantities = product.get('units') or None
	rows = []
	driver_to_reset(url)
	soup = BeautifulSoup(driver.page_source, 'html.parser')

	# Setup buttons
	size_buttons = []
	quantity_buttons = []
	for button in driver.find_elements(By.CLASS_NAME, 'form-option'):
		if button.text.startswith('Sample'):
			continue
		elif button.text.startswith(('Bag', 'Case')):
			quantity_buttons.append(button)
		else:
			size_buttons.append(button) 
	
	for size_button in size_buttons:
		size = SIZES[size_button.text]

		price_data = get_price_data()
		size_button.click()
		err, _ = await_price_data(price_data, get_price_data)
		if err:
			print(f'Timed out: {size_button.text} {url}')
		
		for quantity_button in quantity_buttons:
			units = 0
			if quantities is None:
				units = int(re.search('\d+', quantity_button.text).group())
			else:
				units = quantities[size][quantity_button.text]

			price_data = get_price_data()
			quantity_button.click()
			err, price_data = await_price_data(price_data, get_price_data)
			if err:
				print(f'Timed out: {quantity_button.text} {url}')
			price = float(re.search('\d+\.\d+', price_data).group())

			# TODO: Add in stock selection for InControl
			in_stock = 'Maybe'

			rows.append(calculate_derived_info(info | sizes[size] | {
				'price': price,
                'in_stock': in_stock,
                'size': size,
                'units': units,
			}))

	return rows


def land_of_genie(url, product) -> list[dict]:
	rows = []
	info = product['info']
	sizes = product['sizes']
	data = get_data(url)['product']

	for variant in data['variants']:
		if 'Sample' in variant['option2']:
			continue
			
		size = variant['option1']

		rows.append(calculate_derived_info( info | sizes[size] | {
			'price': float(variant['price']),
			'in_stock': 'Maybe',
			'size': size,
			'units': int(variant['option2'][:1]) * 10
		}))

	return rows


LITTLE_FOR_BIG_SIZES = {
	'Large': {
		'waist_high': 46,
		'waist_low': 36,
	},
    'Medium': {
		'waist_high': 38,
		'waist_low': 28,
	},
}

def little_for_big(url, product) -> list[dict]:
	rows = []
	info = product['info']
	data = get_data(url)

	for variant in data['variations']:
		size, units = re.search('([M|L])(?:[a-zA-z ]*)?(\d*)', variant['attributes'][0]['value']).groups()
		size = SIZES[size]

		variant_data = get_data(
			'https://www.littleforbig.com/wp-json/wc/store/products/{0}'.format(variant['id'])
		)

		price = variant_data['prices']['price']
		price = float('{0}.{1}'.format(price[:-2], price[-2:]))

		info = info | product.get('sizes')[size] or LITTLE_FOR_BIG_SIZES(size)

		rows.append(calculate_derived_info(info | {
			'price': price,
            'in_stock': variant_data['is_in_stock'],
            'size': size,
            'units': int(units),
		}))

	return rows


def my_inner_baby(url, product) -> list[dict]:
	rows = []
	info = product['info']
	sizes = product['sizes']
	data = get_data(url)['product']

	for variant in data['variants']:
		if variant['option2'].endswith('Sample'):
			continue

		size = SIZES[variant['option1']]

		rows.append(calculate_derived_info(info | sizes[size] | {
			'price': float(variant['price']),
			# TODO: Add in stock selection for MyInnerBaby
            'in_stock': 'Maybe',
            'size': size,
            'units': int(re.search('\d+', variant['option2']).group()),
		}))
		
	return rows


def northshore(url, product) -> list[dict]:
	info = product['info']
	driver_to(url)
	soup = BeautifulSoup(driver.page_source, 'html.parser')

	size_info, units_info = list(map(lambda el: el.text, soup.find_all('span', {'class': 'value'})))[0:3:2]
	
	size, waist_low, waist_high = re.search('(.*), (\d+) - (\d+)', size_info).groups()
	size = SIZES[size]
	units = int(re.search('(?:Case|Pack)\/(\d+)', units_info).groups()[0])
	return [calculate_derived_info(info | {
		'price': float(soup.find('span', {'class', 'product-details__price_highlight'}).string[1:]),
		'in_stock': 'Yes' if soup.find('span', {'class', 'icon icon-check'}) else 'No',
		'size': size,
		'waist_high': waist_high,
		'waist_low': waist_low,
		'units': units,
	})]


def rearz(url, product) -> list[dict]:
	def get_price_data():
		soup = BeautifulSoup(driver.page_source, 'html.parser')
		return soup.find('span', {'class': 'price price--withoutTax'}).text

	rows = []
	info = product['info']
	sizes = product.get('sizes') or None
	quantities = product.get('units') or None
	driver_to_reset(url)
	

	size_buttons = []
	units_buttons = []
	for button in driver.find_elements(By.CLASS_NAME, 'form-option'):
		if button.get_attribute('for').startswith('st'):
			continue
		elif button.text.strip().startswith('Trial') or button.text.strip().startswith('Sample'):
			continue
		elif button.text.strip() == '':
			continue
		elif button.text.startswith(('Bag', 'Case')):
			units_buttons.append(button)
		else:
			size_buttons.append(button)
	
	for size_button in size_buttons:
		size, waist_low, waist_high = re.search('(?:NEW )?([a-zA-Z-]+) \((\d+\.?\d?)(?:\"|\”) ?- ?(\d+\.?\d?)', size_button.text).groups()
		size = SIZES[size]

		price_data = get_price_data()
		size_button.click()
		err, _ = await_price_data(price_data, get_price_data)
		if err:
			print(f'Timed out: {url}')

		for units_button in units_buttons:
			units = 0
			if quantities is None:
				units = int(re.search('\d+', units_button.text).group())
			else:
				units = quantities[size][units_button.text]

			price_data = get_price_data()
			units_button.click()
			err, price_data = await_price_data(price_data, get_price_data)
			if err:
				print(f'Timed out: {url}')

			if sizes is not None:
				info = info | sizes[size]

			rows.append(calculate_derived_info(info | {
				'price': float(re.search('\d+\.\d+', price_data).group()),
				# TODO: add stock for Rearz
                'in_stock': 'Maybe',
                'size': size,
                'waist_high': waist_high,
                'waist_low': waist_low,
                'units': units,
			}))
	
	return rows


def tykables(url, product) -> list[dict]:
    rows = []
    info = product['info']
    sizes = product['sizes']
    data = get_data(url)['product']

    for variant in data['variants']:
        if variant['option3'] != 'None' or variant['option2'].endswith('Sample'):
            continue

        size = SIZES[variant['option1']]

        rows.append(calculate_derived_info(info | sizes[size] | {
            'price': float(variant['price']),
            'in_stock': 'Yes' if variant['inventory_quantity'] > 0 else 'No',
            'size': size,
            'units': int(variant['option2'][:2]),
        }))

    return rows


def xp_medical(url, product) -> list[dict]:
    rows = []
    info = product['info']
    sizes = product.get('sizes') or None
    soup = get_soup(url)

    matches = re.findall(
        '(Small|Medium|Large|X-Large)[a-zA-Z\d\-\n]+(\d\d)-(\d\d)[a-zA-Z \n]+(\d+)[a-zA-Z ,\d\/\n]+\$(\d+.\d\d)', soup.find('table', {'class': 'sizeInfo'}).text.strip())

    for match in matches:
        size, waist_low, waist_high, units, price = match
        size = SIZES[size]

        if sizes is not None:
            info = info | sizes[size]

        row = calculate_derived_info(info | {
            'price': float(price),
            'in_stock': 'Maybe',
            'size': size,
            'waist_high': waist_high,
            'waist_low': waist_low,
            'units': int(units),
        })
        rows.append(row)

    return rows


DOMAINS = {
	'us.abu': abu,
	'www.amazon': amazon,
	'bambino': bambino,
	'incontrol': incontrol,
	'www.littleforbig': little_for_big,
	'myinnerbaby': my_inner_baby,
	'www.northshore': northshore,
	'rearz': rearz,
	'tykables': tykables,
	'www.xpmedical': xp_medical,
}

def main():
	file_name = datetime.date.today().strftime('%d-%m-%Y.json')
	products = yaml.safe_load(open('products.yml', 'r'))
	start_index = 0
	index = 0
	rows = []
	for url, product in products.items():
		index += 1
		if index < start_index:
			continue
		print(index, url)
		new_rows = check_routine(url, product)
		rows.extend(new_rows)
	
	print(f'Writing to {file_name}')
	with open(file_name, 'w') as file:
		json.dump(rows, file, sort_keys=True, indent=4, separators=(',', ': '))
	print('Done!')

products = yaml.safe_load(open('products.yml', 'r'))
test_fetch(little_for_big, 'https://www.littleforbig.com/wp-json/wc/store/products/150610')
# main()