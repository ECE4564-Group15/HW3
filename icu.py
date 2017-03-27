###############################################################################
## Name: icu.py
## Author: Beichen Liu
## Date: 3.17.2017
## Description:
##
# !/usr/bin/env python3

import argparse
import urllib, requests
import datetime
import sys, time, os
from math import *
import ephem
import pygame
import json
from gtts import gTTS

from twilio.rest import TwilioRestClient
from datetime import datetime, timedelta

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


def argvparser():  # argument parser
    global arg
    parser = argparse.ArgumentParser()
    parser.add_argument('-z', nargs=1, dest='zipcode', \
                        help="indicates the zipcode of viewing area")
    parser.add_argument('-s', nargs=1, dest='NORAD', \
                        help="indicates NORAD ID of satellite to view")
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
    latitude = float(resp_json['results'][0]['geometry']['location']['lat'])
    longitude = float(resp_json['results'][0]['geometry']['location']['lng'])
    return latitude, longitude


'''
' function: getTLE()
' parameter: None
' return: TLE list
'''


def getTLE(NORAD_ID=25544):

    if isinstance(NORAD_ID, list):
        NORAD_ID = NORAD_ID[0]

    param = {'identity' : 'xianze@vt.edu',
             'password' : 'space_track.org!',
             'query' : 'https://www.space-track.org/basicspacedata/query/class/tle_latest/format/json/NORAD_CAT_ID/'+ str(NORAD_ID) + '/ORDINAL/1/'
            }

    result = requests.post('https://www.space-track.org/ajaxauth/login', data=param).json()[0]

    try:
        result = [result['TLE_LINE0'], result['TLE_LINE1'], result['TLE_LINE2']]
    except KeyError:
        print("Unable to retrieve TLE data for the given NORAD ID")
        quit()

    return result

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

    sunrise = obs.previous_rising(m)
    sunset = obs.next_setting(m)

    return sunrise, sunset


def datetime_from_time(tr):
    year, month, day, hour, minute, second = tr.tuple()
    dt = datetime(year, month, day, hour, minute, int(second))
    return dt


'''
' function: getSAT()
' parameter: TLE0, TLE1, TLE2, date('2017-03-18'), latitude, longitude
' return: TR list, TS list
'         TR is appearing time
'         TS is disappearing time
'''

def getSAT(lon, lat, date, tle):
    L = []
    sat = ephem.readtle(str(tle[0]), str(tle[1]), str(tle[2]))

    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.long = str(lon)
    observer.pressure = 0
    observer.horizon = '-0:34'

    now = date
    end_time = now + timedelta(days=1)
    observer.date = now
    while end_time > now:
        tr, azr, tt, altt, ts, azs = observer.next_pass(sat)

        duration = int((ts - tr) *60*60*24)
        rise_time = datetime_from_time(tr)
        max_time = datetime_from_time(tt)
        set_time = datetime_from_time(ts)

        observer.date = max_time

        sun = ephem.Sun()
        sun.compute(observer)
        sat.compute(observer)

        sun_alt = degrees(sun.alt)
        visible = False
        ang = degrees(sat.az)
        oo = {'tr': tr,
                 'ts': ts,
                 'duration': duration,
                 'angle' : ang,
                 'lng': sat.sublong,
                 'lat': sat.sublat}
        # print(oo)
        if sat.eclipsed is False and  -18 < sun_alt < -6 :
            # print("visible, degree of sunalt is", degrees(sun_alt))
            visible = True
            # print(oo)
            if rise_time > datetime.utcnow() and rise_time < end_time:
                L.append(oo)
        observer.date = now
    return L

'''
' function: getWeather()
' parameter: coordinate latitude/longitude
' return: a list of weather in 15 days
'''


def getWeather(lati, lng):
    cloud_list = []
    url = (
    'http://api.openweathermap.org/data/2.5/forecast/daily?lat={0}&lon={1}&cnt=16&appid=8998a89b9499fc1c889f6f091304b984'.format(
        lati, lng))
    ret = requests.get(url).json()
    for i in range(0, 15):
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
    T0 = T0.strftime('%b %d %Y')
    T0 = datetime.strptime(T0, '%b %d %Y')
    vis = 0 # count clear sky day.
    latitude, longitude = zip2cood(arg.zipcode)
    TLE = getTLE(arg.NORAD)
    wea = getWeather(latitude,longitude)

    for i in range (0,15):
        # event = getSAT(TLE[0],TLE[1], TLE[2], T0+timedelta(days=i),latitude, longitude)
        event = getSAT(longitude, latitude, T0+timedelta(days=i), TLE)
        if len(event) > 0:
            print(i, event[0]['tr'])
        if wea[i] <20:
            for j in range(len(event)):
                vis +=1
                # print(event)
                List.append(event[j])
        if vis == 5:
            return List
            break

    return List

def LED():
    os.system("echo 21 > /sys/class/gpio/export || true")  # red
    os.system("echo out > /sys/class/gpio/gpio21/direction")
    os.system("echo 1 >/sys/class/gpio/gpio21/value")
    time.sleep(1)
    os.system("echo 0 >/sys/class/gpio/gpio21/value")
    time.sleep(1)


def audio_notification(sentence, filename):
    tts = gTTS(text=sentence, lang='en')
    tts.save(filename)
    # os.startfile(filename)
    play_music(filename)


def current_status(TLE):
    name = TLE[0]
    line1 = TLE[1]
    line2 = TLE[2]
    obs = ephem.Observer()
    obs.date = datetime.utcnow()
    curr = ephem.readtle(name, line1, line2)
    curr.compute(obs)

    return curr.sublong, curr.sublat, degrees(curr.az)


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
    for i in range(0,15):
        print(datetime.utcnow()+timedelta(days=i), "clouds", wea[i])
    if len(L) <5:
        print ("\n")
        print ("cannot find 5 viewable days")
    print ("\n")
    print ("=====================================SAT ephpem=======================================================\n")
    print ("longitude: {0}, latitude: {1}, travel direction: {2}".format(cur_lng, cur_lat, cur_ang))
    print("\n")
    print ("=====start====================stop=========Duration(min)===latitude=======longitude====direction======\n")
    for li in L:
        print (li['tr'],'\t', li['ts'], '\t', li['duration'],'\t', li['lat'],'    ', li['lng'], li['angle'])
    print ("\n")

    while len(L) > 0 :
        while (datetime.utcnow() + timedelta(minutes=15) <= L[0]['tr'].datetime()):
            print("waiting")
            print(datetime.utcnow())
            time.sleep(5)
        if (datetime.utcnow() + timedelta(minutes=15) > L[0]['tr'].datetime() and datetime.utcnow() <= L[0][
            'ts'].datetime()):
            SMS = "The sat will appear at {0}".format(L[0]['tr'])
            print(SMS)
            audio_notification(SMS, "notify1.mp3")
            send_SMS(SMS) # uncomment before submit and for final test
            LED()
        while (datetime.utcnow() + timedelta(minutes=15) > L[0]['tr'].datetime() and datetime.utcnow() <= L[0][
            'tr'].datetime()):
            LED()
        L.pop(0)


main()
