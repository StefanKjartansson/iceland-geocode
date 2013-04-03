# Iceland-Geocode

[![Build Status](https://secure.travis-ci.org/StefanKjartansson/iceland-geocode.png)](http://travis-ci.org/StefanKjartansson/iceland-geocode)

Simple geocoding proxy server for Icelandic addresses using non-blocking calls to fasteignaskrá. Returns results in gmaps friendly wgs84.

Proxies the query directly to fasteignaskrá's geoserver so it's generally quite quick.


## Installation

Clone and setup the requirements, the project has only been tested on python2.7 and python3.3.

    git clone git@github.com:StefanKjartansson/iceland-geocode.git
    virtualenv env
    . env/bin/activate
    pip install -r requirements.txt
    python server.py

Navigate your browser to **http://localhost:8888/?q=Laugavegur+1,101**
