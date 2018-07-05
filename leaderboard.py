#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 18 14:12:32 2017
Using stravalib to access leaderboard database
@author: Gavin
"""
import matplotlib.pylab as plt
import pandas as pd
import stravalib

def get_strava_leaderboard(segment=610040, top=1000):
    try:
        f = open( 'mytoken.txt', 'r' )
        mytoken = f.read()
        f.close()
        client = stravalib.Client(access_token = mytoken) 
    except:
        print('access_token required')
        return
    
    client.get_athlete()
    
    # Download the first 5 pages of leaderboard with 200 entries per page
    lbPages = {}
    for n in range(int(top/200)):
        try:
            lbPages[n]=client.get_segment_leaderboard(segment, gender=None, age_group=None, \
                                      weight_class=None, following=None, club_id=None, \
                                      timeframe=None, top_results_limit=200, \
                                      page=n+1, context_entries=0)
        except:
            pass
    
    varList = ['rank', 'effort_id', 'athlete_id', 'athlete_name',\
                                'athlete_gender','athlete_profile', 'average_hr',\
                                'average_watts', 'distance', 'elapsed_time',\
                                'moving_time', 'start_date_local', 'activity_id']
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

# Tour de Richmond Park segment 610040 download and pickle
def pickle_strava_leaderboard(segment=610040):
    LB = get_strava_leaderboard(segment) 
    LB.to_pickle('/Users/Gavin/Gavin/python/Strava/'+str(segment)+'.pkl')
    return LB


