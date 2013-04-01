#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick geo-coding service for icelandic addresses
"""
from __future__ import unicode_literals, print_function, absolute_import

import json
import unittest

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.testing import AsyncHTTPTestCase
from tornado.httpclient import AsyncHTTPClient

from server import GeoHandler


class GeoTest(AsyncHTTPTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def get_app(self):
        return Application([('/', GeoHandler)], debug=True)

    def test_queries(self):

        q = '/?q=Laugavegur+12,101'

        self.http_client.fetch(self.get_url(q), self.stop)
        response = self.wait(timeout=30)
        j = json.loads(response.body.decode('utf-8'))
        self.assertIsNotNone(j)
        self.assertDictEqual(j['results'][0]['coordinates'],
            {"lng": -21.9311738, "lat": 64.1460249})


if __name__ == '__main__':
    unittest.main()
