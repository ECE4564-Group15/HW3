#!/usr/bin/python

import sys
import math
import ephem
from datetime import datetime
import urllib2
import json

def getSAT(TLE1, TLE2, Date, latitude, longitude):
    TR = []
    TS = []
    iss = ephem.readtle("ISS (ZARYA)", TLE1, TLE2)
    obs = ephem.Observer()
    obs.date = Date
    obs.lat = latitude
    obs.long = longitude
    tr = obs.date
    while tr != obs.next_pass(iss)[0]:
        tr, azr, tt, altt, ts, azs = obs.next_pass(iss)
        sun = ephem.Sun()
        sun.compute(obs)
        iss.compute(obs)
        sun_alt = math.degrees(sun.alt)
        obs.date = ts
        if math.degrees(sun_alt) < 0 : ## to be fixed
            TR.append(tr)
            TS.append(ts)

    return TR, TS
'''
print getSAT("1     5U 58002B   17076.91076897 -.00000003 +00000-0 +22459-4 0  9998",\
       "2     5 034.2432 286.0553 1842581 049.0594 325.5511 10.84699960076281",\
       '2017-03-18', '37.2724841', '-80.4326521')
'''

def get_Weather(lat, lng):
    now = datetime.utcnow()
    url = 'http://forecast.weather.gov/MapClick.php?lat='+lat+'&lon='+lng+'&FcstType=json'
    json_read = urllib2.urlopen(url).read()
    read = json.loads(json_read)
    print len(read['data']['weather'])

get_Weather('37.2724841', '-80.4326521')
