###############################################################################
## Name: icu.py
## Author: Beichen Liu
## Date: 3.17.2017
## Description:  
##              
## TODO: 
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
from datetime import datetime


''' define global variable here'''
'''This is for space track'''
baseURL = 'https://www.space-track.org'
username = 'bcliu430@vt.edu'
password = 'BeichenL960430!'
'''this is for twilio'''
accountSID = "ACc8cb6ca47d0a8b36519bbd4180ab2a46"
authToken = "b58beb2a4fd808e24d3b38741f130f8c"

'''
' function: getUTCTime()
' parameter: None
' return: time now.
'''

def getUTCTime():
    return datetime.utcnow()

'''
' function: argvparser()
' parameter: None
' return: arguments as arg.zipcode and arg.NORAD.
'''

def argvparser(): # argument parser
    global arg
    parser = argparse.ArgumentParser()
    parser.add_argument('-z', nargs=1,dest='zipcode',\
                        help="indicates the zipcode of viewing area")
    parser.add_argument('-s', nargs=1, dest='NORAD',\
                        help= "indicates NORAD ID of satellite to view")
    arg = parser.parse_args()

'''
' function: zip2cood()
' parameter: zipcode ('24060')
' return: latitude and longitude
'''

def zip2cood(zipcode):
    google_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+zipcode
    response = requests.get(google_url)
    resp_json = response.json()
    latitude = float( resp_json['results'][0]['geometry']['location']['lat'])
    longitude = float( resp_json['results'][0]['geometry']['location']['lng'])
    print "latitude: ", latitude,"longitude: ", longitude
    return latitude, longitude 

'''
' function: getTLE()
' parameter: None
' return: TLE list
'''

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
# uncomment when submit
    TLE_List = TLE.split('\n')
    print "--------------------------------Finsh-------------------------------\n"
    opener.close()
#    return TLE_List
    for i in xrange(0,len(TLE_List),2):
        try: 
            getSAT(TLE_List[i],TLE_List[i+1],'2017-03-18', '37','-80')
        except:
            print str(i)+' '+'Error'
            continue



'''
' function: sun_below()
' parameter: date('2017-03-18'), latitude, longitude
' return: sunrise, sunset
'''

def sun_below(day, lati, longi):
    obs = ephem.Observer()
    obs.date = day
    obs.lat = lati
    obs.long = longi
    m = ephem.Sun()

    sunrise  = obs.previous_rising(m)
    sunset = obs.next_setting(m)

    return sunrise,sunset 

'''
' function: getSAT()
' parameter: TLE1, TLE2, date('2017-03-18'), latitude, longitude
' return: TR list, TS list
'         TR is appearing time
'         TS is disappearing time
'''
    
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
        TR.append(tr)
        TS.append(ts)
        obs.date = ts
    return TR, TS
'''
' function: send_SMS()
' parameter: _SMS_ (the content of the msg)
' return: None
'''

def send_SMS(_SMS_):
    client = TwilioRestClient(accountSID, authToken) 
    client.messages.create(to="+15407509285", from_="+16173000913", body=_SMS_)

'''
' function: play_music()
' parameter: None
' return: None
' Note: needs to configure continuous music playing 
'       and music dir 
'''

def play_music():
    pygame.init()
    pygame.mixer.music.load("/usr/share/sounds/ubuntu/ringtones/Soul.ogg")
    pygame.mixer.music.play()
    time.sleep(10)


def main():
    argvparser()
    latitude,longitude = zip2cood(arg.zipcode[0])
    getTLE(arg.NORAD[0])
    

main()



