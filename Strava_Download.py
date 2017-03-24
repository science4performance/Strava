
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

def get_strava_leaderboard( top=1000, segment_id=610040, gender=None, age_group=None,                                       weight_class=None, following=None, club_id=None, timeframe=None, top_results_limit=200, page=None, context_entries=0):
    """ segment_id is the integer identifier used by Strava
        top is the number of entries from the top of the leaderboard"""
    try:
        f = open( 'mytoken.txt', 'r' )
        mytoken = f.read()
        f.close()
        client = stravalib.Client(access_token = mytoken) 
    except:
        print('access_token required')
        return
    
    # Download the first 5 pages of leaderboard with 200 entries per page
    lbPages = {}
    for n in range(int(top/200)):
        try:
            lbPages[n]=client.get_segment_leaderboard(segment_id=segment_id, gender=gender, age_group=age_group, \
                                      weight_class=weight_class, following=following, club_id=club_id, \
                                      timeframe=timeframe, top_results_limit=200, \
                                      page=n+1, context_entries=context_entries)
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
    LB.index=range(1,top+1)
    
    return LB

# Get a segment's leaderboard and pickle it
def pickle_strava_leaderboard(segment=610040):
    LB = get_strava_leaderboard(segment) 
    LB.to_pickle('/Users/Gavin/Gavin/jupyter/Strava/'+str(segment)+'_LB.pkl')
    return LB


# Get geographic data about a segment 
def get_strava_segment(segment=610040):
    """ Returns dataframe of stream data for altitude, distance, latitude, longitude
        segment is the integer identifier used by Strava
        top is the number of entries from the top of the leaderboard"""
    try:
        f = open( 'mytoken.txt', 'r' )
        mytoken = f.read()
        f.close()
        client = stravalib.Client(access_token = mytoken) 
    except:
        print('access_token required')
        return

    segmentStream = client.get_segment_streams(segment,['distance', 'altitude','latlng'])

    segmentDict = {}
    [lat,lng] = list(zip(*segmentStream['latlng'].data))
    segmentDict['latitude'] = list(lat)
    segmentDict['longitude'] = list(lng)
    segmentDict['distance'] = segmentStream['distance'].data
    segmentDict['altitude'] = segmentStream['altitude'].data
    
    return pd.DataFrame(segmentDict)


def get_strava_activity(activity_id=76213561,types=['distance']):
    try:
        f = open( 'mytoken.txt', 'r' )
        mytoken = f.read()
        f.close()
        client = stravalib.Client(access_token = mytoken) 
    except:
        print('access_token required')
        return

    Stream = client.get_activity_streams(activity_id,types)
    Dictionary = {}
    for i in ['distance']+types:
        Dictionary[i] = Stream[i].data
    return pd.DataFrame(Dictionary)
        
def get_strava_effort(effort_id=1522793879,types=['distance']):
    try:
        f = open( 'mytoken.txt', 'r' )
        mytoken = f.read()
        f.close()
        client = stravalib.Client(access_token = mytoken) 
    except:
        print('access_token required')
        return

    Stream = client.get_effort_streams(effort_id,types)
    Dictionary = {}
    for i in ['distance']+types:
        Dictionary[i] = Stream[i].data
    return pd.DataFrame(Dictionary)
   



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

# In[ ]:

def get_strava_explore_segments(coords=[(50,-6),(56,2)]):
    try:
        f = open( 'mytoken.txt', 'r' )
        mytoken = f.read()
        f.close()
        client = stravalib.Client(access_token = mytoken) 
    except:
        print('access_token required')
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




