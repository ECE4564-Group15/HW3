###############################################################################
## Name: icu.py
## Author: Beichen Liu
## Date: 3.17.2017
## Description:
##
## TODO: 1. validate that getSAT() works, fix it if you can
##       2. fix the bug in main loop
##       3. display the sat's data to fit validation requirement 4
##       4. figure out if we need function sun_below()
#!/usr/bin/env python3

import argparse
import googlemaps
import urllib, requests
import datetime
import sys,time,os
import math
import ephem
import pygame
import json
from gtts import gTTS

from twilio.rest import TwilioRestClient
from datetime import datetime, timedelta
from spacetrack import SpaceTrackClient



''' define global variable here'''
'''This is for space track'''
baseURL = 'https://www.space-track.org'
username = 'bcliu430@vt.edu'
password = 'BeichenL960430!'
'''this is for twilio'''
accountSID = "ACc8cb6ca47d0a8b36519bbd4180ab2a46"
authToken = "b58beb2a4fd808e24d3b38741f130f8c"

'''
'   function: getUTCTime()
'   parameter: None
'   return: time now.
'''

def getUTCTime():
    return datetime.utcnow()

'''
'   function: argvparser()
'   parameter: None
'   return: arguments as arg.zipcode and arg.NORAD.
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
'   function: zip2cood()
'   parameter: zipcode ('24060')
'   return: latitude and longitude
'''

def zip2cood(zipcode):
    google_url = ('https://maps.googleapis.com/maps/api/geocode/json?address={0}'.format(zipcode))
    response = requests.get(google_url)
    resp_json = response.json()
    latitude = float( resp_json['results'][0]['geometry']['location']['lat'])
    longitude = float( resp_json['results'][0]['geometry']['location']['lng'])
    return latitude, longitude

'''
' function: getTLE()
' parameter: None
' return: TLE list
'''

def getTLE(Norad_ID=25544):
    param = {'identity' : 'xianze@vt.edu',
             'password' : 'space_track.org!',
             'query' : 'https://www.space-track.org/basicspacedata/query/class/tle_latest/format/json/NORAD_CAT_ID/'+ Norad_ID + '/ORDINAL/1/'
            }

    result = requests.post('https://www.space-track.org/ajaxauth/login', data=param).json()[0]
    try:
        result = [result['TLE_LINE0'], result['TLE_LINE1'], result['TLE_LINE2']]
    except KeyError:
        print("Unable to retrieve TLE data for the given NORAD ID")
        quit()

    return result
'''
    st = SpaceTrackClient(username,password)
    TLE = st.tle_latest(norad_cat_id=[NoradID], ordinal=1, format='tle')
    TLE_List = TLE.split('\n')
    return TLE_List

'''


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
' parameter: TLE0, TLE1, TLE2, date('2017-03-18'), latitude, longitude
' return: TR list, TS list
'         TR is appearing time
'         TS is disappearing time
'''

def getSAT(TLE0, TLE1, TLE2, Date, latitude, longitude):
    iss = ephem.readtle(TLE0, TLE1, TLE2)
    obs = ephem.Observer()
    obs.date = Date
    obs.lat = latitude
    obs.long = longitude
    tr = obs.date
    while tr != obs.next_pass(iss)[0]:
        event = []
        tr, azr, tt, altt, ts, azs = obs.next_pass(iss)
        sun = ephem.Sun()
        sun.compute(obs)
        iss.compute(obs)
        sun_alt = math.degrees(sun.alt)
        ang = math.degrees(iss.az)
        obs.date = ts
        duration = int((tr-ts)*24*60)
        if math.degrees(sun_alt) < 0 and iss.eclipsed is False: 
            entry = {'tr': tr,
                     'ts': ts,
                     'duration': duration,
                     'angle': ang, 
                     'lng': iss.sublong,
                     'lat': iss.sublat}
            event.append(entry)
    return event
'''
' function: getWeather()
' parameter: coordinate latitude/longitude
' return: a list of weather in 15 days
'''

def getWeather(lati, lng):
    cloud_list = []
    url = ('http://api.openweathermap.org/data/2.5/forecast/daily?lat={0}&lon={1}&cnt=16&appid=8998a89b9499fc1c889f6f091304b984'.format(lati,lng))
    ret = requests.get(url).json()
    for i in range (0,14):
        cloud_list.append(ret['list'][i]['clouds'])
    return cloud_list


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

def play_music(filename):
    pygame.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    time.sleep(10)
'''
'   function: viewable_Event()
'   parameter: None
'   return: viewable event list
'''

def viewable_Event():
    TLE = []
    List = []
    T0 = getUTCTime()
    vis = 0 # count clear sky day.
    latitude, longitude = zip2cood(arg.zipcode)
    norad = arg.NORAD[0]
    TLE = getTLE(norad)
    wea = getWeather(latitude,longitude)

    for i in range (0,14):
        event = getSAT(TLE[0],TLE[1],TLE[2],T0+timedelta(days=i),latitude, longitude)
        if wea[i] <20:
            for j in range(len(event)):
                vis +=1
                List.append(event[j])
        if vis == 5:
            return List
            break

    return List
  
def LED():
    os.system("echo 21 > /sys/class/gpio/export || true") # red
    os.system("echo out > /sys/class/gpio/gpio21/direction")
    os.system("echo 1 >/sys/class/gpio/gpio21/value")
    time.sleep(1)
    os.system("echo 0 >/sys/class/gpio/gpio21/value")
    time.sleep(1)


def audio_notification(sentence, filename):
    tts = gTTS(text=sentence, lang='en')
    tts.save(filename)
    play_music(filename)

def current_status(TLE):
    name = TLE[0]
    line1 = TLE[1]
    line2 = TLE[2]
    obs = ephem.Observer()
    obs.date = datetime.utcnow()
    curr  = ephem.readtle(name, line1, line2)
    curr.compute(obs)

    return curr.sublong, curr.sublat, math.degrees(curr.az)

def main():
    argvparser()
    L = []
    print ("starting...")
    L = viewable_Event()
    latitude, longitude = zip2cood(arg.zipcode)
    TLE = getTLE(arg.NORAD[0])
    wea = getWeather(latitude,longitude)
    cur_lng, cur_lat, cur_ang = current_status(TLE)
    print ("---------------------------------TLE---------------------------------\n")
    print(TLE[0])
    print(TLE[1],)
    print(TLE[2], "\n")
    print ("------------------------------coordinate-----------------------------\n")
    print ("latitude: ", latitude, "longitude: ", longitude, "\n")
    print ("----------------------------sky condition----------------------------\n") 
    for i in range(0,14):
        print(datetime.utcnow()+timedelta(days=i), "clouds", wea[i])   
    if len(L) <5:
        print ("\n")
        print ("cannot find 5 viewable days")
    print ("\n")
    print ("=====================================SAT ephpem=======================================================\n")
    print ("longitude: {0}, latitude: {1}, travel direction: {2}".format(cur_lng, cur_lat, cur_ang))
    print ("=====start====================stop=========Duration(min)===latitude=======longitude====direction======\n")
    for li in L:
        print (li['ts'],'\t', li['tr'], '\t', li['duration'],'\t', li['lat'],'    ', li['lng'], li['angle'])
    print ("\n")


    while (datetime.utcnow()+timedelta(minutes=15) <= L[0]['ts'].datetime()):
        print("waiting")
        print( datetime.utcnow())
        time.sleep(5)
    if(datetime.utcnow()+timedelta(minutes=15)>L[0]['ts'].datetime() and datetime.utcnow() <= L[0]['ts'].datetime()):
        SMS = "The sat will appear at {0}".format(L[0]['ts'])
        print (SMS)
        audio_notification(SMS, "notify1.mp3")
        # send_SMS(SMS) # uncomment before submit and for final test
        LED()
    while(datetime.utcnow()+timedelta(minutes=15)>L[0]['ts'].datetime() and datetime.utcnow() <= L[0]['ts'].datetime()):
        LED()



main()
