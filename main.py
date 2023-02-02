import requests
import json
from bs4 import BeautifulSoup, Tag
import pygsheets
from pygsheets import Worksheet, Cell, Address
import numpy as np
from data import product_list, Column, Row
from selenium import webdriver
from enum import Enum


parser = 'html.parser'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'
}

class Link(Enum):
    ABU = 'https://us.abuniverse.com'
    AMAZON = 'https://www.amazon.com',
    AWWSOCUTE = 'https://www.awwsocute.com'
    BAMBINO = 'https://bambinodiapers.com'
    EBAY = 'https://ebay.com'
    INCONTROL = 'https://incontroldiapers.com'
    LANDOFGENIE = 'https://landofgenie.com'
    LITTLEFORBIG = 'https://littleforbig.com'
    MYINNERBABY = 'https://myinnerbaby.com'
    NORTHSHORE = 'https://northshorecare.com'
    REARZ = 'https://rearz.ca'
    TYKABLES = 'https://tykables.com'


print("Initializing web driver")
driver = webdriver.Firefox()
print("Web driver initialized")

def abu(data) -> Row:
    row = Row()
    price = data['prices']['price']
    currency_minor_unit = data['prices']['currency_minor_unit']
    row.price = price[:-currency_minor_unit] + \
        '.' + price[-currency_minor_unit:]
    return row


def amazon(soup: BeautifulSoup) -> Row:
    row = Row()  
    price_to_pay = soup.find('span', {'class': 'apexPriceToPay'})
    # row.price = price_to_pay.find('span', {'class': 'a-offscreen'}).string[1:]
    print(soup)
    return row


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



def error_bad_link(status_code: str, link: str):
    print(f'Error: {status_code} for {link}')


def from_link(link) -> Row:
    if link.startswith(Link.AMAZON):
        driver.get(link)
        return amazon(BeautifulSoup(driver.page_source, parser))
    elif link.startswith(Link.REARZ):
        driver.get(link)
        return rearz(BeautifulSoup(driver.page_source, parser))
    elif link.startswith(Link.INCONTROL):
        driver.get(link)
        return incontrol(BeautifulSoup(driver.page_source, parser))

    with requests.get(link, headers=headers) as response:
        if response.status_code != 200:
            error_bad_link(response.status_code, link)
            return Row()

        soup = BeautifulSoup(response.text, parser)

        if link.startswith(Link.ABU):
            return abu(response.json())
        elif link.startswith(Link.AWWSOCUTE):
            return aww_so_cute(soup)
        elif link.startswith(Link.TYKABLES):
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


def test():
    from_link('https://us.abuniverse.com/wp-json/wc/store/products/114045')
    # from_link('https://www.amazon.com/dp/B08GL7M5YY')

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
