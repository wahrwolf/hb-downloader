#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .order import Order
from .subproduct import Subproduct
from .product import Product
from sys import stderr


class TroveOrder(Order):

    TROVE_GAMEKEY = "Humble-trove-games"

    def __init__(self, trove_page_html_text, hapi):
        """
            Parameterized constructor for the Order object.

            :param trove_page_html_text: The plain text/html page of the humble trove
            :param hapi: humble bundle api handle. Used to read the trove dummy gamekey and signing URL.
        """

        super(Order, self).__init__(trove_page_html_text)

        try:  # TODO: maybe move this check elsewhere to disable trove
            import lxml.html
        except ModuleNotFoundError:
            print("Warning: lxml is necessary for humble trove support", file=stderr)
            return

        tree = lxml.html.fromstring(trove_page_html_text)
        trove_products = tree.find_class("trove-product-detail")

        subproducts = []
        for product_lxml in trove_products:
            if len(product_lxml.find_class('js-download-button')) == 0:  # Download button means valid product
                continue
            platforms = product_lxml.find_class("trove-platform-selector")
            product = {'human_name': product_lxml.find_class('product-human-name')[0].text,
                       'machine_name': product_lxml.attrib['data-machine-name'],
                       'downloads': [],
                       'payee': {}  # TODO: put something better here
                       }
            for p in platforms:
                pp = dict()
                pp['platform'] = p.attrib['data-platform']
                pp['download_identifier'] = p.attrib['data-url']
                pp['machine_name'] = p.attrib['data-machine-name']
                signed = hapi.get_signed_trove_url(pp['machine_name'], pp['download_identifier'])
                pp['download_struct'] = [{
                    'url_dictionary': {
                        'web': signed.get('signed_url', None),
                        'bittorrent': signed.get('signed_torrent_url', None)
                    }
                }]
                pp['options_dict'] = None  # TODO: What is this?
                product['downloads'].append(pp)
            subproducts.append(Subproduct(product))  # TODO: check that the data formats actually match

        self.subscriptions = None
        self.created = None
        self.amount_to_charge = None
        self.gamekey = TroveOrder.TROVE_GAMEKEY
        self.subproducts = subproducts

        product_data = {
            'human_name': 'Humble Trove Games',
            'machine_name': 'trove_games',
            'category': 'trove'
        }
        self.product = Product(product_data)
