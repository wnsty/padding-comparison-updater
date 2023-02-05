import requests
import json
from bs4 import BeautifulSoup
import pygsheets
from pygsheets import Worksheet, Cell, Address
import numpy as np
from old_src.data import product_list, Row, URL
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
import re
from html import unescape

parser = 'html.parser'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'
}
driver: WebDriver = None

display_sizes = {
	'm': 'Medium',
	'l': 'Large',
	'xl': 'X-Large',
}

with open('json/product_info.json') as file:
    product_info = json.load(file)

with open('json/product_templates.json') as file:
    product_templates = json.load(file)


def sanitize(text) -> str:
    return text.encode('ascii', 'ignore').decode()


def error_bad_url(status_code: str, url: str):
    print(f'Error: {status_code} for {url}')


def init_driver():
    global driver
    if driver is None:
        print('Initializing web driver')
        driver = webdriver.Firefox()
        print('Web driver initialized')


def abu(soup: BeautifulSoup) -> list[Row]:
    rows = []
    title = soup.find('h1', {'class': 'product_title entry-title'}
                      ).string.encode('ascii', 'ignore').decode()
    info = product_templates['abu'][title]

    for size in info['size']:
        id = info['size'][size]['id']
        url = f'https://us.abuniverse.com/wp-json/wc/store/products/{id}'
        in_stock = False
        with requests.get(url) as response:
            if response.status_code != 200:
                error_bad_url(response.status_code, url)
                continue
            if response.json()['is_in_stock']:
                in_stock = True
        for packs, ident in {1: '1', 4: '2', 8: '3'}.items():
            data = soup.find('label', {'for': f'abu_quantity_{ident}'}).string

            price: float = float(re.search('\d*\.\d*', data).group())
            units: float = info['units_per_bag'] * packs
            unit_price: float = price / units
            capacity = info['capacity']
            ml_per_price = capacity / unit_price

            rows.append(Row(
                retailer='ABU',
                brand='ABU',
                name=title,
                size=size,
                waist_low=info['size'][size]['waist_low'],
                waist_high=info['size'][size]['waist_high'],
                price=price,
                shipping=info['shipping'],
                units=units,
                capacity=capacity,
                unit_price=unit_price,
                total_price=price + info['shipping'],
                ml_per_price=ml_per_price,
                in_stock=in_stock,
                notes=info['notes'],
                url=info['url'],
            ))
    return rows


def amazon(soup: BeautifulSoup) -> Row:
    price_to_pay = soup.find('span', {'class': 'apexPriceToPay'})
    # row.price = price_to_pay.find('span', {'class': 'a-offscreen'}).string[1:]
    # print(soup)
    return Row(

    )


def aww_so_cute(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def bambino(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def ebay(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def incontrol(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def land_of_genie(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def little_for_big(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def my_inner_baby(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def northshore(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def rearz(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def tykables(data) -> list[dict]:
    result = []
    product = data['product']
    name = sanitize(product['title'])
    for variant in product['variants']:
        product_template = product_templates[name]
        variant_info = product_info[name]['variants'][variant['id']]
        price = float(variant['price'])
        units = int(variant_info['units'])
        unit_price = price / units
        size = product_info['sizes'][variant_info['size']]

        result.append(product_template | {
            'in_stock': 'Yes' if variant['inventory_quantity'] != 0 else 'No',
            'ml_per_unit_price': product_template['capacity'] / unit_price,
            'price': price,
            'size': display_sizes[variant_info['size']],
            'total_price': price + product_template['shipping'],
            'units': units,
            'unit_price': price / units,
            'waist_high': size['waist_high'],
            'waist_low': size['waist_low']
        })

        print(list)


def xp_medical(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def from_url(url) -> Row:
    if url.startswith(URL.AMAZON.value):
        init_driver()
        driver.get(url)
        return amazon(BeautifulSoup(driver.page_source, parser))
    elif url.startswith(URL.REARZ.value):
        init_driver()
        driver.get(url)
        return rearz(BeautifulSoup(driver.page_source, parser))
    elif url.startswith(URL.INCONTROL.value):
        init_driver()
        driver.get(url)
        return incontrol(BeautifulSoup(driver.page_source, parser))

    with requests.get(url, headers=headers) as response:
        if response.status_code != 200:
            error_bad_url(response.status_code, url)
            return Row()

        soup = BeautifulSoup(response.text, parser)

        if url.startswith(URL.ABU.value):
            return abu(soup)
        elif url.startswith(URL.AWWSOCUTE.value):
            return aww_so_cute(soup)
        elif url.startswith(URL.TYKABLES.value):
            return tykables(soup)

        else:
            return 'Not found'


def update_sheet():
    print("Updating Google sheet.")

    gc = pygsheets.authorize()
    sh = gc.open('Automatic Padding Comparison Chart')
    wks: Worksheet = sh.worksheet('title', 'Diapers')

    urls = wks.get_col(wks.find('Link')[0].col)[1:]

    resolved = {}
    prices = []

    for url in urls:
        if url == '':
            continue

        if url in resolved:
            price = resolved[url]
        else:
            price = from_url(url)
            resolved[url] = price

        prices.append([price])

    wks.update_values(f'H2', prices)


def test():
    with requests.get('https://tykables.com/products/str8up-pink.json') as response:
        tykables(response.json())

    # print(
    #     '{0:^8}'.format('Seller')
    #     + '{0:^7}'.format('Brand')
    #     + '{0:^24}'.format('Name')
    #     + '{0:^8}'.format('Size')
    #     + '{0:^15}'.format('Waist')
    #     + '{0:^10}'.format('Price')
    #     + '{0:^10}'.format('Shipping')
    #     + '{0:^17}'.format('Units')
    #     + '{0:^14}'.format('Capacity')
    #     + '{0:^16}'.format('Unit Price')
    #     + '{0:^16}'.format('Total Price')
    #     + '{0:^16}'.format('ML Per Unit $')
    #     + '{0:^16}'.format('In Stock')
    #     + '{0:^16}'.format('Notes')
    #     + '{0:^16}'.format('URL')
    # )

    # for name, product in product_templates['abu'].items():
    #     url = product['url']
    #     for row in from_url(url):
    #         print(row)


test()
