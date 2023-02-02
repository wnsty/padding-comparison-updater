import requests
import json
from bs4 import BeautifulSoup, Tag
import pygsheets
from pygsheets import Worksheet, Cell, Address
import numpy as np
from info import data


# https://rearz.ca/remote/v1/product-attributes/5845
# https://tykables.com/products/waddler-diapers.json
# https://us.abuniverse.com/wp-json/wc/store/products/356371


# tykeables => product url, variant id
# myinnerbaby => product url, variant id
# bambino => product url, variant id

# abu => variant url
# lfb => variant url

# northshore => store url
# xpmedical => store url, sku

# rearz = selenium
# amazon => selenium?


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


def from_link(link) -> Column:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'}
    with requests.get(link, headers=headers) as response:
        if response.status_code != 200:
            print(f'Error: {response.status_code} for {link}')
            return Column()
        soup = BeautifulSoup(response.text, 'html.parser')
        if link.startswith('https://tykables.com'):
            return tykables(link)
        elif link.startswith('https://us.abuniverse.com'):
            return abu(response.json())
        elif link.startswith('https://www.amazon.com'):
            print('amazon')
            return amazon(soup)
        else:
            return 'Not found'


def bambino(soup: BeautifulSoup) -> Column:
    pass


def lfb(soup: BeautifulSoup) -> Column:
    pass


def my_inner_baby(soup: BeautifulSoup) -> Column:
    pass


def northshore(soup: BeautifulSoup) -> Column:
    pass


def xp_medical(soup: BeautifulSoup) -> Column:
    pass


def amazon(soup: BeautifulSoup) -> Column:
    columns = Column()
    price_to_pay = soup.find('span', {'class': 'apexPriceToPay'})
    # columns.price = price_to_pay.find('span', {'class': 'a-offscreen'}).string[1:]
    print(soup)
    return columns


def tykables(soup: BeautifulSoup) -> Column:
    columns = Column()
    columns.price = soup.find('span', {'class': 'money'}).string
    return columns


def abu(data) -> Column:
    columns = Column()
    price = data['prices']['price']
    currency_minor_unit = data['prices']['currency_minor_unit']
    columns.price = price[:-currency_minor_unit] + \
        '.' + price[-currency_minor_unit:]
    return columns


def columns_from_tykables_local(link) -> Column:
    with open('tykables_local.json') as file:
        return Column(price=json.load(file)[link])


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
        print(f'Checking {link}')

        if link in resolved:
            price = resolved[link]
        else:
            price = from_link(link)
            resolved[link] = price

        prices.append([price])

    wks.update_values(f'H2', prices)

# update_sheet()


def test():
    # from_link('https://us.abuniverse.com/wp-json/wc/store/products/114045')
    from_link('https://www.amazon.com/dp/B08GL7M5YY')

    # c = Columns(price=30)
    # print(c.price)
    # print(c.waist_high)

    # session = requests.Session()
    # response = session.get('https://rearz.ca/rearz-lil-bella-adult-diapers/')
    # print(response.text)

    # response = session.post('https://rearz.ca/remote/v1/product-attributes/5841')
    # print(response.text)
    # with session.get('https://rearz.ca/rearz-lil-bella-adult-diapers/') as page_response:
    # 	print(page_response.cookies.add_cookie_header)
    #     headers = {
    #         'Content-Type': 'application/x-www-form-urlencoded',
    #         'X-XSRF-TOKEN': page_response.cookies,
    #     }
    #     with requests.post('https://rearz.ca/remote/v1/product-attributes/5841', headers=headers, cookies=page_response.cookies) as data_response:
    #         print(data_response)


test()
