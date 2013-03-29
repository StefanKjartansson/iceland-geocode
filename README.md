# Iceland-Geocode

Simple geocoding proxy server for Icelandic addresses using non-blocking calls to fasteignaskrá.

## caveat emptor

* Only tested on python 3.3
* Uses the search on fskra so performance depends on that.

## TODO:

Cache search results in redis, return the geocoded tuple from there if we have it.
