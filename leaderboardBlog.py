#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 18 14:12:32 2017
Using stravalib to access leaderboard database
@author: Gavin
"""
import matplotlib.pylab as plt
import pandas as pd
import numpy as np

#LB = pd.read_pickle('/Users/Gavin/Gavin/python/Strava/610040.pkl')

# working with the data   



# riders setting PB on the same day as rider position n in table
n=1
LB[['rank','athlete_name','elapsed_time','start_date_local']][LB.start_date_local.dt.date==LB.start_date_local.dt.date[n]]

# The month in which PBs are set
ax=LB.start_date_local.dt.month.value_counts().reindex(np.arange(1,13)).plot(kind='bar', xlim=(1,12), title='Month when PB set', width=1)
ax.set_xticklabels( ['J','F','M','A','M','J','J','A','S','O','N','D'],rotation='horizontal')
ax.set_ylabel('Frequency')
plt.savefig('MonthPlot.png')

# The times at which PBs are set
fig=plt.figure()
ax=LB.start_date_local.dt.hour.value_counts().reindex(np.arange(25)).plot(kind='bar',xlim=((0,24)),title='Hour of the day when PB set',width=1)
ax.set_xticklabels( ['00:00','','','','','','06:00','','','','','','12:00','','','','','','18:00','','','','',''],rotation='vertical')
ax.set_ylabel('Frequency')
plt.show()
fig.savefig('HourPlot.png')

# The day of the week on which PBs are set
fig=plt.figure(figsize=(6, 7))
ax=LB.start_date_local.dt.weekday_name.value_counts().reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).plot(kind='bar',title='Day of the week when PB set',width=1)
ax.set_ylabel('Frequency')
plt.show()
fig.savefig('WeekPlot.png')

# Most popular dates for PBs
LB.start_date_local.dt.date.value_counts()[:10]
