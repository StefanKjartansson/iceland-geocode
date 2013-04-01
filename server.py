#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick geo-coding service for icelandic addresses
"""
from __future__ import unicode_literals, print_function, absolute_import

import codecs
import json
import urllib.parse
import time

import lxml.html
from lxml import objectify
from lxml.builder import E
from lxml.etree import tostring

from tornado import ioloop, gen, escape
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.web import asynchronous, RequestHandler, Application, HTTPError

from geo import isnet93_to_wgs84


url = 'http://geo.skra.is/geoserver/wfs'
postcodes = dict(i.split(';')[:2] for i in
    codecs.open('postnumer.txt', 'r',
    encoding='iso-8859-1').read().splitlines()[1:])


def build_geo_http_request(filters):
    params = {
        'service': 'wfs',
        'version': '1.1.0',
        'request': 'GetFeature',
        'typename': 'fasteignaskra:VSTADF',
        'outputformat': 'json',
        'filter': filters,
    }
    return HTTPRequest(url, method='POST',
        body=urllib.parse.urlencode(params))


def build_name(p):
    name = p['HEITI_NF']
    if p['HUSMERKING']:
        name += ' %s' % p['HUSMERKING']
    name += ', %d' % p['POSTNR']
    return name


def build_response_element(item):

    p = item['properties']
    return {
        'display_name': build_name(p),
        'street': p['HEITI_NF'],
        'number': p['HUSMERKING'],
        'postcode': p['POSTNR'],
        'coordinates': isnet93_to_wgs84(*item['geometry']['coordinates']),
    }


def build_filter(street, number, postcode):
    return tostring(E.Filter(
        E.And(
            E.PropertyIsEqualTo(
                E.PropertyName("fasteignaskra:HEITI_NF"),
                E.Literal(street)
            ),
            E.PropertyIsEqualTo(
                E.PropertyName("fasteignaskra:HUSNR"),
                E.Literal(number)
            ),
            E.PropertyIsEqualTo(
                E.PropertyName("fasteignaskra:POSTNR"),
                E.Literal(postcode)
            ),
    )))


class GeoHandler(RequestHandler):

    @asynchronous
    @gen.engine
    def get(self):
        q = self.get_argument('q', None)
        if not q:
            raise HTTPError(400, "Missing query parameter")

        try:
            street, postcode = (i.strip() for i in q.strip().split(','))
            street, number = street.split()
        except ValueError:
            raise HTTPError(400, "Unable to parse address")

        place = postcodes.get(postcode)
        if not place:
            raise HTTPError(400, "Invalid postcode")

        start = time.time()

        http_client = AsyncHTTPClient()
        f = build_filter(street, number, postcode)

        request = build_geo_http_request(f)
        response = yield gen.Task(http_client.fetch, request)
        response.rethrow()

        j = json.loads(response.body.decode('utf-8'))

        self.write({'results': [build_response_element(i) for i in j['features']]})
        self.add_header('X-REQUEST-TIME', str(time.time() - start))
        self.finish()


application = Application([
    (r"/", GeoHandler),
])


if __name__ == "__main__":
    application.listen(8888)
    ioloop.IOLoop.instance().start()
