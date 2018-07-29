## Import Statements
import json
import pandas as pd #for Reddit Visualization
from mpl_toolkits.basemap import Basemap #Visualization, importing map (using Miller Project world map)
import numpy as np #Visualization
import matplotlib.pyplot as plt #Visualization
import urllib.request, urllib.parse, urllib.error
import requests
import sys
import datetime
import re 
import sqlite3
# Facebook API library
import facebook

# Adam Benson
# Facebook API --- scraping facebook events to gain insights into location



#####################################################################################
#CREATING BASE MAP FOR FB VISUALIZATION#
wmap = Basemap(projection='mill',llcrnrlat=-90,urcrnrlat=90,\
            llcrnrlon=-180,urcrnrlon=180,resolution='c')
# resolution set to crude
# lat/lon values *llcrnrlat = lower left corner lat, set up values for lower left and upper right corners
wmap.drawcoastlines() #draws coastlines
#wmap.drawcountries() #draws countries
wmap.drawcountries(color='beige')
wmap.fillcontinents(lake_color='cyan')
wmap.drawmapboundary(fill_color='cyan')

######## PRINTING FUNCTION FOR CODEC ISSUES #########################################
def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file) 
#####################################################################################
######## SET UP CACHING ################
########################################
FB_CACHE = "fbAPIResearch_cache.json"


try:
    fb_cache_file = open(FB_CACHE, 'r') # Try to read the data from the file
    fb_cache_contents = fb_cache_file.read()  # If it's there, get it into a string
    fb_cache_file.close() # Close the file, we're good, we got the data in a string.
    FB_CACHE_DICTION = json.loads(fb_cache_contents) # And then load it into a dictionary
except:
    FB_CACHE_DICTION = {}
###################################################################################
###################################################################################

# Facebook
# This portion requires that the USER generates an access token from facebook
# Enter token when prompted
# When prompted, type in search query for Events that you are interested in.
# Again, I was interested in ' Big Data', however, I wrote the function so that it matches events to any search queries
# This function will return data, including lat and longitude, of up to  facebook 100 events
# Note that not all search queries will yield 100 events

print("Welcome to the Facebook Analysis Portion of the project")

access_token = None
if access_token is None: #get token from fb user in order to run this script
    access_token = input("\nCopy and paste token from https://developers.facebook.com/tools/explorer\n>  ")
graph = facebook.GraphAPI(access_token)

def get_fb_events(topic):
    if topic in FB_CACHE_DICTION:
        print("Data Was Cached")
        events = FB_CACHE_DICTION[topic]
        return events
    else:
        print("making new request")
        params = { 'q': topic, 'type': 'Event', 'limit': '100', 'time_format': 'U'}
        events = graph.request("/search?", params) #matching fb events with user input words.  'Big Data' was the original goal in this project
        FB_CACHE_DICTION[topic] = events
        x = json.dumps(FB_CACHE_DICTION)
        fb_cache_file = open(FB_CACHE, 'w')
        fb_cache_file.write(x)
        fb_cache_file.close()
        return FB_CACHE_DICTION[topic]

t = input("Enter Topic 'ex: Big Data' : ")
eventsl = get_fb_events(t) #dictionary of facebook events results for query
#print(type(eventsl)) #type dict
eventslist = eventsl['data']
#eventlist = json.dumps(eventslist, indent= 4)
#uprint(eventlist)

###################################################################################
conn = sqlite3.connect('FB_APIandDB.sqlite')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS Events')
cur.execute('CREATE TABLE Events (event_date DATETIME, description TEXT, attending INTEGER, city TEXT, country TEXT, declined INTEGER, interested INTEGER, eventid INTEGER PRIMARY KEY, latitude REAL, longitude REAL)')
###################################################################################

for x in eventslist: #For all the events that match the search query
    eventid = x['id'] #event id = unique identifier to access more information on the event
    #uprint(eventid)
    eventname = x['name']
    uprint(eventname)
    #try:
    starttime = (x['start_time']) # example 2017-12-19T14:30:00+0100 
    uprint('start time: ', starttime) #time of event in formation YYYY-MM-DD + Time
    #print(type(starttime))
    #except:
    #    starttime = 'None'
    #    print("No Time Specified")
    try:                    
        place = x['place']
        uprint('location: ', place['location']) #printing event location information if avaliable
        city = place['location']['city']
        country = place['location']['country']
        lat = place['location']['latitude']
        longitude = place['location']['longitude']
    except:
        place = 'None'
        print("no location avaliable")
    try:
        description = x['description']
    except:
        description = 'No Description Avaliable'
    detailz = graph.get_object(id=eventid, fields = 'attending_count, declined_count, interested_count')
    #print(type(detailz['attending_count']))  type = 'int'
    num_attending = detailz['attending_count']
    num_interested = detailz['interested_count']
    num_declined = detailz['declined_count']
    #print('attending: ', num_attending)
    #print('interested: ', num_interested)
    #print('declined: ', num_declined, '\n')
    events_info = (starttime, description, num_attending, city, country, num_declined, num_interested, eventid, lat, longitude)
    cur.execute('INSERT or IGNORE INTO Events VALUES (?,?,?,?,?,?,?,?,?,?)', events_info)
    print('\n')
conn.commit() 

###Fb Visualization component
## Creating a Map of events listed for search query
try:
    cur.execute('SELECT latitude from EVENTS')
    k= cur.fetchall()
    lats = [int(x[0]) for x in k]
    cur.execute('SELECT longitude from EVENTS')
    w = cur.fetchall()
    longs = [int(x[0]) for x in w]

    l=0

    while l < len(lats):
        xpt,ypt = wmap(longs[l], lats[l])
        wmap.plot(xpt, ypt, "d", markersize=15)
        l += 1


    plt.title('Facebook Events')
    plt.show()
    print('Facebook Visualization Success')

except: print('Something went wrong')

cur.close()
conn.close()