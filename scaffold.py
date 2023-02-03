import requests
import json
from bs4 import BeautifulSoup, Tag
import pygsheets
from pygsheets import Worksheet, Cell, Address
import numpy as np
from data import product_list, Row
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from enum import Enum
import re
from html import unescape, escape


def error_bad_link(status_code: str, link: str):
    print(f'Error: {status_code} for {link}')


def build_scaffold():
    scaffold = {
        'abu': grab_abu_products(),
		'amazon': {},
		'awwsocute': {},
		'bambino': {},
		'ebay': {},
		'incontrol': {},
		'landofgenie': {},
		'littleforbig': {},
		'myinnerbaby': {},
		'northshore': {},
		'rearz': {},
		'tykables': {},
		'xpmedical': {},
    }

    with open('scaffold_products.json', 'w') as file:
        json.dump(scaffold, file, sort_keys=True,
                  indent=4, separators=(',', ': '))


def grab_abu_products() -> dict:
    scaffold = {}
    link = 'https://us.abuniverse.com/wp-json/wc/store/products?per_page=100&sku=AGZ-,BBV-,BNY-,BNY4-,CBC-,CUS-,DNO-,KDO-,LKG-,PWZ-,PAB-,PRP-,PRS-,WHI-,SIU-,SPC-,SDK-'
    with requests.get(link) as response:
        if response.status_code != 200:
            error_bad_link(response.status_code, link)
            return scaffold

        for product in response.json():
            name = unescape(product['name']).encode('ascii', 'ignore').decode()
            scaffold[name] = {
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
    return scaffold


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
            'id': str(variation['id']),
            'waist_high': '',
            'waist_low': '',
        }
    return result


build_scaffold()
