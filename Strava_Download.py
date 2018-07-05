
# coding: utf-8

# # Analysis of Strava data
# 
# This code library makes use of stravalib to access download data from Strava leaderboards and other useful information. It uses my developer's token which I need to keep private.
# 
# The first objective is to download the top entries from the <a href="https://www.strava.com/segments/610040" target="_blank">leaderboard</a>. Since Strava sets a limit of 200 entries per page, it is necessary to perform a number of calls in a loop to download more (if they exist).  This is performed by the function get_strava_leaderboard. The results can be pickled to avoid repeatedly downloading the same data.
# 

# In[1]:

"""
Created on Sat Feb 18 14:12:32 2017
Using stravalib to access leaderboard database
@author: Gavin
"""
import matplotlib.pylab as plt
import pandas as pd
import stravalib
import requests
import numpy as np

import sys
sys.path.append('/Users/Gavin/Gavin/Jupyter/Weather')
from AirDensity import rhoCalc
import HistoricWeather

def get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt'):
    """Retrieve API token from text file"""
    try:
        f = open( tokenFile, 'r' )
        mytoken = f.read()
        f.close()
    except:
        print('API access token not found')
        mytoken = None
    return mytoken


def get_strava_leaderboard( top=1000, segment_id=610040, gender=None, age_group=None,                                       weight_class=None, following=None, club_id=None,                                       timeframe=None, top_results_limit=200,                                       page=None, context_entries=0):
    """ segment is the integer identifier used by Strava
        top is the number of entries from the top of the leaderboard"""
    
    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return
    
    # Download the first 5 pages of leaderboard with 200 entries per page
    lbPages = {}
    for n in range(int(top/200)):
        try:
            lbPages[n]=client.get_segment_leaderboard(segment_id=segment_id, gender=gender, age_group=age_group,                                       weight_class=weight_class, following=following, club_id=club_id,                                       timeframe=timeframe, top_results_limit=200,                                       page=n+1, context_entries=context_entries)
        except:
            pass
    
    varList = ['rank', 'effort_id', 'athlete_id', 'athlete_name',                                'athlete_gender','athlete_profile', 'average_hr',                                'average_watts', 'distance', 'elapsed_time',                                'moving_time', 'start_date_local', 'activity_id']
    lbDict = {}
    for var in varList:
        lbDict[var] = [getattr(e,var) for page in lbPages for e in getattr(lbPages[page],'entries')]
        
    
    LB = pd.DataFrame(lbDict)
    
    # convert all distance Quantities into metres 
    # since they are all the same segment, they should all agree anyway
    # this has to be done before dropping duplicates as pandas can't deal with Quantity types
    LB.distance = [float(stravalib.unithelper.meters(d)) for d in LB.distance]

    # removes duplicates of client.athlete and reset index starting at 1
    LB.drop_duplicates(inplace=True)
    LB.index=range(1,len(LB)+1)
    
    return LB

def pickle_strava_leaderboard(segment=610040):
    """Get a segment's leaderboard and pickle it"""
    LB = get_strava_leaderboard(segment) 
    LB.to_pickle('/Users/Gavin/Gavin/jupyter/Strava/'+str(segment)+'_LB.pkl')
    return LB


def parseStream(stream):
    """Convert a Strava stream into a pandas DataFrame (converted to metric )"""
    Dict = {}
    for k in stream.keys():
        if k == 'latlng':                
            [lat,lng] = list(zip(*stream['latlng'].data))
            Dict['lat'] = list(lat)
            Dict['lon'] = list(lng)
        elif k in ['distance', 'altitude', 'velocity_smooth']:
            Dict[k] = [float(stravalib.unithelper.meters(d)) for d in stream[k].data]
        else:    
            Dict[k] = stream[k].data
    return pd.DataFrame(Dict)

    

# Get geographic data about a segment 
def get_strava_segment(segment_id=610040):
    """ Returns dataframe of segment stream data 
        segmentID is the integer identifier used by Strava"""

    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return

    types=['time', 'latlng', 'distance', 'altitude', 'velocity_smooth','heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']
    Stream = client.get_segment_streams(segment_id,types)
    return parseStream(Stream)
 

def get_strava_activity(activity_id=76213561):
    """ Returns dataframe of active stream data 
        activityID is the integer identifier used by Strava"""

    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return

    types=['time', 'latlng', 'distance', 'altitude', 'velocity_smooth','heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']
    Stream = client.get_activity_streams(activity_id,types)
    return parseStream(Stream)


def get_strava_effort(effort_id=1522793879):
    """ Returns dataframe of effort stream data 
        activityID is the integer identifier used by Strava"""

    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return

    types=['time', 'latlng', 'distance', 'altitude', 'velocity_smooth','heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']
    Stream = client.get_effort_streams(effort_id,types)
    return parseStream(Stream)
   


def get_route_stream(route_id = '7570312'):
    """Special function runs curl request as this does not seem to be available in stravalib"""
    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return

    data = requests.get('https://www.strava.com/api/v3/routes/{id}/streams'.format(id=route_id), headers = {'Authorization':'Bearer {token}'.format(token=mytoken)})
    df = pd.read_json(data.text)
    [lat,lon] = np.array(df.data[df.type=='latlng'].values[0]).T
    distance = df.data[df.type=='distance'].values[0]
    altitude = df.data[df.type=='altitude'].values[0]

    dfOut = pd.DataFrame({'distance':distance, 'altitude':altitude, 'lat': lat, 'lon': lon}) 
    dfOut.index.name = 'secs'
    return dfOut

def createCSVofStravaSegment(segment_id=1158972):
    segment = get_strava_segment(segment_id)
    segment.index.name = 'secs'
    segment.columns=['altitude','distance','lat','lon']
    file = 'Segment' + str(segment_id) + '.csv'
    segment.to_csv(file)
    return file

def createCSVofStravaRoute(route_id=6243168):
    route = get_route_stream(route_id)
    file = 'Route' + str(route_id) + '.csv'
    route.to_csv(file)
    return file
    
def createCSVofStravaActivity(activity_id=971178783):
    activity = get_strava_activity(activity_id)
    file = 'Activity' + str(activity_id) + '.csv'
    activity.to_csv(file)
    return file

def createCSVofStravaEffort(effort_id=1522793879):
    effort = get_strava_effort(effort_id)
    file = 'Effort' + str(effort_id) + '.csv'
    effort.to_csv(file)
    return file


def get_effort_info(effort_id=1522793879):
    """Returns name, average start/end lat and lon, elevation, mid-point time"""
    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return
    
    effort = client.get_segment_effort(effort_id)
    name = effort.name
    lat = (effort.segment.start_latitude + effort.segment.end_latitude) / 2
    lon = (effort.segment.start_longitude + effort.segment.end_longitude) / 2
    elevation = float(stravalib.unithelper.meters(
        (effort.segment.elevation_low + effort.segment.elevation_high) / 2))
    t = effort.start_date_local + effort.elapsed_time / 2
    return name, lat, lon, elevation, t

def get_effort_weather(effort_id=1522793879):
    """Returns a series of weather stats, with segment info, Name of series is datetime"""
    name, lat, lon, elevation, t = get_effort_info(effort_id)
    weather = HistoricWeather.weatherObs(t.day, t.month, t.year, 
                                         t.hour, t.minute, t.second, 
                                         lat=lat, lon=lon)
    weather['AirDensity'] = rhoCalc(weather.Pressure, weather.Temp, weather.Humidity, elevation)
    weather['Name'] = name
    weather['ID'] = effort_id
    weather['Longitude'] = lon
    weather['Latitude'] = lat
    weather['Elevation'] = elevation
    return weather

def get_activity_info(activity_id=1567745926):
    """Returns name, average start/end lat and lon, elevation, mid-point time"""
    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return
    
    activity = client.get_activity(activity_id)
    name = activity.name
    elat,elon = activity.end_latlng
    lat = (activity.start_latitude + elat) / 2
    lon = (activity.start_longitude + elon) / 2
    elevation = float(stravalib.unithelper.meters(
        (activity.elev_low + activity.elev_high) / 2))
    t = activity.start_date_local + activity.elapsed_time / 2
    return name, lat, lon, elevation, t


def get_activity_weather(activity_id=1567745926):
    """Returns a series of weather stats, with segment info, Name of series is datetime"""
    name, lat, lon, elevation, t = get_activity_info(activity_id)
    weather = HistoricWeather.weatherObs(t.day, t.month, t.year, 
                                         t.hour, t.minute, t.second, 
                                         lat=lat, lon=lon)
    weather['AirDensity'] = rhoCalc(weather.Pressure, weather.Temp, weather.Humidity, elevation)
    weather['Name'] = name
    weather['ID'] = activity_id
    weather['Longitude'] = lon
    weather['Latitude'] = lat
    weather['Elevation'] = elevation
    return weather



# ## Experiment with explore_segments
# This is a list of the attributes of an explore segment
# id, name,climb_category,climb_category_desc,avg_grade, start_latlng,end_latlng,elev_difference,distance,points,starred,segment
# 
# 
# ID of the segment.
# Name of the segment
# Climb category for the segment (0 is higher)
# Climb category text
# Average grade for segment.
# Start lat/lon for segment
# End lat/lon for segment
# Total elevation difference over segment.
# Distance of segment.
# Encoded Google polyline of points in segment
# Whether this segment is starred by authenticated athlete
# Associated (full) stravalib.model.Segment object.

# In[22]:

def get_strava_explore_segments(coords=[(50,-6),(56,2)]):
    """Returns a list of segments inside the box defined by lower left and upper right corners in coords"""
    mytoken = get_token(tokenFile = '/Users/Gavin/Gavin/Tokens/stravaToken.txt')
    if mytoken:
        client = stravalib.Client(access_token = mytoken) 
    else:
        return

    segments = client.explore_segments(coords)
    # Choose attributes standard ones and and quantities 
    attributes1 = ['id', 'name', 'climb_category','climb_category_desc','avg_grade']
    attributesq = ['elev_difference','distance']
    attributes = attributes1 + attributesq
    d = []
    for s in segments:
            d += [[getattr(s,a) for a in attributes1]+[float(stravalib.unithelper.meters(getattr(s,q))) for q in attributesq]]

    return pd.DataFrame(d, columns = attributes)

