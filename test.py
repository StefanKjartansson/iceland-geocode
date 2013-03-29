import unittest
import json

import lxml.html

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

    def test_homepage(self):

        q = '/?q=Laugavegur+12,101'

        self.http_client.fetch(self.get_url(q), self.stop)
        response = self.wait(timeout=30)
        print(response.body)
        self.assertIsNotNone(json.loads(response.body.decode('utf-8')))


if __name__ == '__main__':
    unittest.main()
