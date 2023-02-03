import requests
import json
from bs4 import BeautifulSoup
import pygsheets
from pygsheets import Worksheet, Cell, Address
import numpy as np
from data import product_list, Row, Link
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
import re
from html import unescape

parser = 'html.parser'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'
}
driver: WebDriver = None

with open('json/products.json') as file:
    products = json.load(file)


def error_bad_link(status_code: str, link: str):
    print(f'Error: {status_code} for {link}')


def init_driver():
    global driver
    if driver is None:
        print('Initializing web driver')
        driver = webdriver.Firefox()
        print('Web driver initialized')


def abu(soup: BeautifulSoup) -> list[Row]:
    rows = []
    title = soup.find('h1', {'class': 'product_title entry-title'}).string
    info = products['abu'][title]

    for size in info['size']:
        id = info['size'][size]['id']
        link = f'https://us.abuniverse.com/wp-json/wc/store/products/{id}'
        in_stock = False
        with requests.get(link) as response:
            if response.status_code != 200:
                error_bad_link(response.status_code, link)
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


def tykables(soup: BeautifulSoup) -> Row:
    row = row()
    row.price = soup.find('span', {'class': 'money'}).string
    return row


def xp_medical(soup: BeautifulSoup) -> Row:
    raise NotImplemented()


def from_link(link) -> Row:
    if link.startswith(Link.AMAZON.value):
        init_driver()
        driver.get(link)
        return amazon(BeautifulSoup(driver.page_source, parser))
    elif link.startswith(Link.REARZ.value):
        init_driver()
        driver.get(link)
        return rearz(BeautifulSoup(driver.page_source, parser))
    elif link.startswith(Link.INCONTROL.value):
        init_driver()
        driver.get(link)
        return incontrol(BeautifulSoup(driver.page_source, parser))

    with requests.get(link, headers=headers) as response:
        if response.status_code != 200:
            error_bad_link(response.status_code, link)
            return Row()

        soup = BeautifulSoup(response.text, parser)

        if link.startswith(Link.ABU.value):
            return abu(soup)
        elif link.startswith(Link.AWWSOCUTE.value):
            return aww_so_cute(soup)
        elif link.startswith(Link.TYKABLES.value):
            return tykables(soup)

        else:
            return 'Not found'


def update_sheet():
    print("Updating Google sheet.")

    gc = pygsheets.authorize()
    sh = gc.open('Automatic Padding Comparison Chart')
    wks: Worksheet = sh.worksheet('title', 'Diapers')

    links = wks.get_col(wks.find('Link')[0].col)[1:]

    resolved = {}
    prices = []

    for link in links:
        if link == '':
            continue

        if link in resolved:
            price = resolved[link]
        else:
            price = from_link(link)
            resolved[link] = price

        prices.append([price])

    wks.update_values(f'H2', prices)

# update_sheet()


def grab_abu_products():
    scaffold = {'abu': {}}
    link = 'https://us.abuniverse.com/wp-json/wc/store/products?per_page=100&sku=AGZ-,BBV-,BNY-,BNY4-,CBC-,CUS-,DNO-,KDO-,LKG-,PWZ-,PAB-,PRP-,PRS-,WHI-,SIU-,SPC-,SDK-'
    with requests.get(link) as response:
        if response.status_code != 200:
            error_bad_link(response.status_code, link)
            return

        for product in response.json():
            name = unescape(product['name']).encode('ascii', 'ignore').decode()
            scaffold['abu'][name] = {
                'id': str(product['id']),
                'size': grab_abu_variants(product['id']),
                'shipping': 0,
                'units_per_bag': 10,
                'capacity': 0,
                'tapes': '4',
                'backing': 'plastic',
                'notes': '',
                'url': product['permalink'],
            }

        with open('json/abu_products.json', 'w') as file:
            json.dump(scaffold, file, sort_keys=True,
                      indent=4, separators=(',', ': '))


def grab_abu_variants(key) -> dict:
    result = {}

    link = f'https://us.abuniverse.com/wp-json/wc/store/products/{key}'
    with requests.get(link) as response:
        if response.status_code != 200:
            error_bad_link(response.status_code, link)
            return result

    data = response.json()

    for variation in data['variations'][::2]:
        result[variation['attributes'][1]['value']] = {
            'id': variation['id'],
            'waist_high': '',
            'waist_low': '',
        }
    return result


def test():
    print(
        '{0:^16}'.format('Seller')
        + '{0:^16}'.format('Brand')
        + '{0:^16}'.format('Name')
        + '{0:^16}'.format('Size')
        + '{0:^16}'.format('Waist Low')
        + '{0:^16}'.format('Waist High')
        + '{0:^16}'.format('Price')
        + '{0:^16}'.format('Shipping')
        + '{0:^16}'.format('Units')
        + '{0:^16}'.format('Capacity')
        + '{0:^16}'.format('Unit Price')
        + '{0:^16}'.format('Total Price')
        + '{0:^16}'.format('ML Per Unit $')
        + '{0:^16}'.format('In Stock')
        + '{0:^16}'.format('Notes')
        + '{0:^16}'.format('URL')
    )
    for row in from_link('https://us.abuniverse.com/product/siu/'):
        print(row)


grab_abu_products()
# grab_abu_variants(106055)
# test()
