###############################################################################
## Name: icu.py
## Author: Beichen Liu
## Date: 3.17.2017
## Description:  
##              
## TODO: 1. find correct NORAD ID and calculation
##       
#!/usr/bin/env python

import argparse
import googlemaps
import urllib, urllib2, cookielib, requests
import datetime
import sys,time
import math
import ephem
import pygame
from twilio.rest import TwilioRestClient 


''' define global variable here'''
'''This is for space track'''
baseURL = 'https://www.space-track.org'
username = 'bcliu430@vt.edu'
password = 'BeichenL960430!'
'''this is for twilio'''
accountSID = "ACc8cb6ca47d0a8b36519bbd4180ab2a46"
authToken = "b58beb2a4fd808e24d3b38741f130f8c"


def argvparser(): # argument parser
    global arg
    parser = argparse.ArgumentParser()
    parser.add_argument('-z', nargs=1,dest='zipcode',\
                        help="indicates the zipcode of viewing area")
    parser.add_argument('-s', nargs=1, dest='NORAD',\
                        help= "indicates NORAD ID of satellite to view")
    arg = parser.parse_args()


def ziptocood(zipcode):
    google_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+zipcode
    response = requests.get(google_url)
    resp_json = response.json()
    global latitude, longitude 
    latitude = float( resp_json['results'][0]['geometry']['location']['lat'])
    longitude = float( resp_json['results'][0]['geometry']['location']['lng'])
    print "latitude: ", latitude,"longitude: ", longitude

def getTLE(NoradID):
    print "Connecting..."
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    parameters = urllib.urlencode({'identity': username ,'password': password})
    opener.open(baseURL + '/ajaxauth/login', parameters)
    queryString = baseURL +"/basicspacedata/query/class/tle/format/tle/NORAD_CAT_ID/"+NoradID+"\
                  EPOCH/"+'2017-03-16'+"%2000:00:00--"+'2017-03-17'+"%2000:00:00"
    resp = opener.open(queryString)

    TLE = resp.read()
    print "---------------------------------TLE---------------------------------\n"
#    print TLE
    TLE_List = TLE.split('\n')
    print(len(TLE_List))
    calc(TLE_List[0],TLE_List[1])
    opener.close()
    
def calc(TLE1,TLE2):
    iss = ephem.readtle("ISS (ZARYA)", TLE1, TLE2)
    obs = ephem.Observer()
    obs.lat  = latitude
    obs.long = longitude
    for p in range(3):
        tr, azr, tt, altt, ts, azs = obs.next_pass(iss)
        while tr < ts :
            obs.date = tr
            iss.compute(obs)
            print "%s %4.1f %5.1f" % (tr, math.degrees(iss.alt), math.degrees(iss.az))
            tr = ephem.Date(tr + 60.0 * ephem.second)
            print 
            obs.date = tr + ephem.minute

def send_SMS(_SMS_):
    client = TwilioRestClient(accountSID, authToken) 
    client.messages.create(to="+15407509285", from_="+16173000913", body=_SMS_)

def play_music():
    pygame.init()
    pygame.mixer.music.load("/usr/share/sounds/ubuntu/ringtones/Soul.ogg")
    pygame.mixer.music.play()
    time.sleep(10)


def main():
    argvparser()
    ziptocood(arg.zipcode[0])
    getTLE(arg.NORAD[0])

# main()
play_music()
