#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lxml.html
from humble_downloader.humble_api.humble_api import HumbleApi
import requests

humble_trove_url = "https://www.humblebundle.com/monthly/trove"

trove_login_cookie = 'put_your_login_cookie_here'

trove_page = requests.get(humble_trove_url)

tree = lxml.html.fromstring(trove_page.text)

elements = tree.find_class("trove-product-detail")


list_trove = []
for e in elements:
#    if len(e.find_class('js-download-button')) == 0: # will be uncommented when the page is fetched after authentication
#        continue
    platforms = e.find_class("trove-platform-selector")
    game = {'human_name': e.find_class('product-human-name')[0].text,
            'machine_name': e.attrib['data-machine-name'],
            'downloads': {}
            }
    for p in platforms:
        pp = dict()
        pp['filename'] = p.attrib['data-url']
        pp['machine-name'] = p.attrib['data-machine-name']
        game['downloads'][p.attrib['data-platform']] = pp
    list_trove.append(game)

hapi = HumbleApi(trove_login_cookie)

print('download urls:')
for game in list_trove:
    for d in game['downloads']:
        dl = game['downloads'][d]
        signed = hapi.get_trove_item(dl['machine-name'], dl['filename'])
        print(signed['signed_url'])  # NOTE: replace 'signed-url' by 'signed_torrent_url' to get the torrent URL
