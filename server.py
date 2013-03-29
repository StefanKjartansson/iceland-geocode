import codecs
import urllib.parse
import json

import lxml.html

from tornado import ioloop, gen, escape
from tornado.web import asynchronous, RequestHandler, Application
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from geo import isnet93_to_wgs84


base_url = 'http://www.skra.is/default.aspx'


postcodes = dict(i.split(';')[:2] for i in
    codecs.open('postnumer.txt', 'r',
    encoding='iso-8859-1').read().splitlines()[1:])


def find_matches(body, place):
    root = lxml.html.fromstring(body)
    selector = '//table[@class="resulttable multifasteign"]//tbody/tr/.'

    for tr in root.xpath(selector):
        name = None

        for td in tr:
            header = td.get('header')
            if not header:
                continue

            text = td.text_content().strip()
            if header == 'heiti':
                name = td.find('a').text_content().strip()
            elif header == 'sveitarfelag':
                if not text == place:
                    break
            elif header == 'landnumer':
                yield (name, text)


def build_geo_http_request(landnr):
    url = 'http://geo.skra.is/geoserver/wfs'
    params = {
        'service': 'wfs',
        'version': '1.1.0',
        'request': 'GetFeature',
        'typename': 'fasteignaskra:VSTADF',
        'outputformat': 'json',
        'filter': '<Filter><PropertyIsLike wildCard="*" singleChar="#" escapeChar="!"><PropertyName>fasteignaskra:LANDNR</PropertyName><Literal>%s</Literal></PropertyIsLike></Filter>' % (landnr)
    }

    return HTTPRequest(url, method='POST',
        body=urllib.parse.urlencode(params))


def build_search_http_request(street):
    params = {
        'pageid': 1000,
        'selector': 'streetname',
        'lsvfn': -1,
        'streetname': street,
        'submitbutton': 'Leita'
    }

    return HTTPRequest(base_url +
        '?%s' % urllib.parse.urlencode(params))


def parse_geo_response(j):
    for i in j['features']:
        g = i.get('geometry')
        if g and g.get('coordinates'):
            return isnet93_to_wgs84(*g['coordinates'])


class GeoHandler(RequestHandler):

    @asynchronous
    @gen.engine
    def get(self):
        q = self.get_argument('q', None)
        if not q:
            self.write('missing query')
            self.finish()
            return

        try:
            street, postcode = (i.strip() for i in q.strip().split(','))
        except ValueError:
            self.write('format is "search string,postcode", "Laugavegur 1, 101"')
            self.finish()
            return

        place = postcodes.get(postcode)

        if not place:
            self.write('invalid postcode')
            self.finish()
            return

        http_client = AsyncHTTPClient()
        request = build_search_http_request(street)
        response = yield gen.Task(http_client.fetch, request)
        response.rethrow()

        # do the json by hand so we can stream the response
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write('{"response": [')
        has_many = False

        for name, landnumer in find_matches(response.body, place):
            request = build_geo_http_request(landnumer)
            response = yield gen.Task(http_client.fetch, request)
            response.rethrow()

            # since we're doing the json by hand.
            # gets toggled after the first element is written
            if has_many:
                self.write(',')

            self.write(escape.json_encode(({
                'name': name,
                'postcode': int(postcode),
                'coordinates': parse_geo_response(
                    json.loads(response.body.decode('utf-8')))
            })))

            if not has_many:
                has_many = True

        self.write(']}')
        self.finish()


application = Application([
    (r"/", GeoHandler),
], debug=True)


if __name__ == "__main__":
    application.listen(8888)
    ioloop.IOLoop.instance().start()
