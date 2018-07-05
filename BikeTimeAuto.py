
# coding: utf-8

# # Bike Time Auto
# This is a streamlined version of BikeTime.ipynb that uploads a course and performs analysis for model riders.

# In[1]:

# Calculate constant velocity for set of parameters
import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from geopy.distance import vincenty


#get_ipython().magic('matplotlib inline')


import sys
sys.path.append('/Users/Gavin/Gavin/Jupyter/Weather')
from AirDensity import rhoCalc

# Parameters required for the physics model solveV accounting for wind
g = 9.81 # m / s
# Sample parameters for rider and bike
Power = 286 # Power Watts
Grade = 0.045 # rise over run
A = 0.5 # FrontalArea m^2
Cd = 0.48 # Coefficent of drag of rider + bike
rho = 1.25 # AirDensity kg/m^3 from Pressure=1020, Temp=15, DP=False, Humidity=False,
mr = 74 # Mass of Rider kg
mb = 8 # Mass of Bike (excluding wheels) kg
mfw = 1.264 # Mass of Front Wheel kg
mrw = 1.364 # Mass of Rear Wheel kg
If = 0.0885 # Inertia Front Wheel kg m / s^2
Ir = 0.1085 # Inertia Rear Wheelkg m / s^2
df = 0.337*2 # Diameter Front Wheel m
dr = 0.337*2 # Diameter Rear Wheel m
Cxf = 0.0491 # Wheel Drag Front
Cxr = 0.0491 # Wheel Drag Rear
RS = 0.25 # % Rear Shelter due to frame
Crr = 0.005 # Coefficient of Rolling Resistance
# Parameters accounting rider direction and wind
Br = 0 # Bearing rider is heading TOWARDS measured in degrees, clockwise from North, derived from delta long/lat
Vw = 4 # windspeed in m / s
Bw = 90 # Bearing wind is comring FROM measured in degrees, clockwise from North, N/E/S/W 0/90/180/270

# Public parameters required for VGrid calculations
Bearings = np.arange(0,360,15)
Grades = np.array([-8, -5, -3, -1.5, 0, 1.5, 3, 5, 8])/100
slopeNames = ['SteepDown', 'MajorDown', 'MediumDown', 'GentleDown', 'Flat', 'GentleUp', 'MediumUp', 'MajorUp', 'SteepUp']
gradeBins=np.array([-999,-6,-4,-2,-1,1,2,4,6])
# Parameter for smoothing course data
smoothing = 5


# In[2]:

# Sigmoid function for adjusting power on hills, a and b chose empirically
def sigmoid(x,a=0.8,b=0.5):
    """Returns sigmoid(x)"""
    return (1/(1+np.exp(-a*x)))+b


# Model of V accounting for wind
def solveV(Power=286, Grade=0.018, mr=74, Cd=0.5,  A=0.5, Br=0, Vw=4, Bw=90, Pressure=1020, Temp=15, DP=False, Humidity=False, Crr=0.005, Cxf=0.0491, df=0.337*2, Cxr=0.0491, dr=0.337*2, RS=0.25, mb=8, mfw=1.264, mrw=1.364, g=9.81, plotIt=False):
    """Returns calculated velocity for given set of parameters by solving cubic equation
    Accounts for rider direction as a bearing Br, wind velicity Vw and wind direction (from) Bw"""

    rho = rhoCalc(Pressure=Pressure, Temp=Temp, DP=DP, Humidity=Humidity)
    Drag = rho / 8 * (4 * A * Cd + np.pi * (Cxf * df**2 + Cxr * dr**2 * (1-RS) ))
    theta = np.arctan(Grade)
    Mech = (mr + mb + mfw + mrw) * g * (Crr * np.cos(theta) + np.sin(theta))
    Ahw = Vw * np.cos((Bw-Br)*np.pi/180) # Apparent headwind

    coef = [0,0,0,0]
    coef[0] = Drag
    coef[1] = 3 * Drag * Ahw
    coef[2] = (3 * Drag * Ahw **2) + Mech
    coef[3] = Drag * Ahw **3 - Power
    if plotIt:
        plt.plot(np.arange(-50,50,0.1),np.polyval(coef,np.arange(-50,50,0.1)))
        plt.axhline(linewidth=1, color='r')

    # Solve for velocity V by taking the real root
    roots = np.roots(coef)
    return max(roots[abs(roots.imag)<1e-3].real) # velocity an m / s




# ## Setting up a grid
# Rather than recalculating the velocity for every data point, it would be more efficient to create a grid as a lookup table.
# So create a (Grade by Bearing) grid of velocities for a given power and wind velocity.
# Grades [-8, -5, -3, -1.5, 0, 1.5, 3, 5, 8]
# [SteepDown, MajorDown, MediumDown, MinorDown, Flat, MinorUp, MediumUp, MajorUp, SteepUp]
# Bearings by 15 degrees

# In[3]:

def vGridCalc(Power=250, mr =75, Cd=0.5, A=0.5, Vw=0, Bw=180, Pressure=1020, Temp=15, DP=False, Humidity=False):
    """Creates a grid of velocities over Bearings and Grades
    for given set of parameters. This saves calculating velocity for every step in course file"""
    vGrid=pd.DataFrame(index=Bearings,columns=slopeNames)

    for i,b in enumerate(Bearings):
        for j,gr in enumerate(Grades):
            vGrid.iloc[i,j] = solveV(Power=Power*sigmoid(gr*100), mr=mr, Cd=Cd, Pressure=Pressure, Temp=Temp, DP=DP, Humidity=Humidity, Grade=gr, Br=b, Vw=Vw, Bw=Bw) 
    return vGrid



# First load the Tour De Richmond Park lap and set things up.

# In[4]:

def loadCourse(courseFile = 'TourDeRichmondPark.csv'):
    """ Loads a course from a csv of an activity file and calculates grade and heading bins
    to correspond with vGridCalc
    The calculation uses the lat, lon and altitude fields only"""
    course=pd.read_csv(courseFile,skipinitialspace=True) # Tour de Richmond Park
    
    course['step'] = 0
    course['step'] = [0]+[vincenty((course.lat[i],course.lon[i]), (course.lat[i+1],course.lon[i+1])).m for i in range(len(course)-1)]
    # Set up model distance as index
    course['modelD'] = course.step.cumsum()/1000

    course['modelSlope'] = course.altitude.rolling(smoothing).mean().diff()/course.step.rolling(smoothing).mean()*100 
    course.loc[course.step.rolling(smoothing).mean() < 1,'modelSlope'] = 0
    course.modelSlope = course.modelSlope.fillna(method='backfill')
    
    course['gradeBin']= np.ones(len(course))*5
        
    for i,gr in enumerate(gradeBins):
        course.ix[course['modelSlope']>gr,'gradeBin'] = Grades[i]*100
    
    course['heading']=np.mod(90-np.angle(course.lon.rolling(smoothing).mean().diff()+course.lat.rolling(smoothing).mean().diff()*1j,deg=True),360)
    course.heading = course.heading.fillna(method='backfill')   # Backfill initial missing values due to smoothing

    gradeTable=pd.DataFrame({'slopeBin':slopeNames, 'gradeBin':Grades*100})
    course = pd.merge(course,gradeTable,how='left',on=['gradeBin'])
    course['headingBin'] = course.heading // 15 * 15

    return course


def modelCourseV(course = loadCourse(courseFile = 'TourDeRichmondPark.csv'), Power=250, mr=75, Cd=0.5, A=0.5, Vw=0, Bw=0, Pressure=1020, Temp=15, Humidity=False, DP=False):
    """Calculates grid for the course and adds model velocity and time to course DataFrame
    based on the rider and weather conditions provided"""
    vGrid = vGridCalc(Power=Power, mr=mr, Cd=Cd, A=A, Vw=Vw, Bw=Bw, Pressure=Pressure, Temp=Temp, DP=DP, Humidity=Humidity)
    course['modelV'] = [vGrid.loc[course.headingBin[a],course.slopeBin[a]]*3.6 for a in range(len(course))]
    course['modelT'] = course.step/course.modelV*3.6
    return course

  
    
    


# In[5]:

import Strava_Download as strava
# If you need to create a file from a segment, then create it
courseFile = strava.createCSVofStravaSegment(segment_id=662750)

# If you need to create a file from a route, then create it
#courseFile = strava.createCSVofStravaRoute(route_id=7542997)


# Otherwise just read in a previously created CSV file
#courseFile = '2016_10_30_02_10_44.csv'   # Ottershaw
#courseFile = 'Dunsfold.csv'   # Ottershaw


#[Power,mr,Cd,A,Vw,Bw,P,T,Humidity]=[302,78,0.5,0.5,0,180,1034,0,90]
# Rob Sharland
[Power,mr,Cd,A,Vw,Bw,P,T,H]=[320,73,0.50,0.5,0/1.6,180,1015,15,60]

course = loadCourse(courseFile)

# *********** Adjust start end of course*************
#course.index = np.mod(course.index + len(course) - 800, len(course))
#course.sort_index(inplace=True)
#course.modelD = np.mod(course.modelD - course.modelD[0], max(course.modelD)+0.00001)

# *****************************************************

course = modelCourseV(course,Power,mr,Cd,A,Vw,Bw,P,T,H)

API_KEY = 'AIzaSyCnlzBJisUSq9KsUyO3uMWXswvKLDmL2jo'
# Draw map does not seem to work inside a function??
import gmplot
gmap = gmplot.GoogleMapPlotter(course.lat.mean(), course.lon.mean(), 13, API_KEY)
gmap.plot(course.lat, course.lon, 'cornflowerblue', edge_width=8)
#gmap.circle(course.lat.iloc[-1], course.lon.iloc[-1], 60, color='red',title='Finish')
gmap.marker(course.lat.iloc[-1], course.lon.iloc[-1],title='Finish')
gmap.draw('mymap.html')
#from IPython.display import IFrame, display
#IFrame('mymap.html', width=700, height=500)


# Now define corner solutions to account for changing parameters up or down. This takes a while to run. We allow Power, Mass and Drag to vary plus or minus 50% and consider a 5m/s wind blowing from 8 compass points

# In[6]:

# Define corners, where parameters are moved up or down to limiting values
# Pd for power down 10%, Pu for power up 10%, Md/Mu for mass, Dd/Du for drag 
# plus 5 m/s wind from 8 directions and a range of air densities
# then allow for changes in pressure, temperature and humidity
corners =  [['Pd',0.9,1,1,0,0,1,0,1],['Pu',1.1,1,1,0,0,1,0,1],            ['Md',1,0.9,1,0,0,1,0,1],['Mu',1,1.1,1,0,0,1,0,1],            ['Dd',1,1,0.9,0,0,1,0,1],['Du',1,1,1.1,0,0,1,0,1],            ['W0',1,1,1,5,0,1,0,1],['W45',1,1,1,5,45,1,0,1],            ['W90',1,1,1,5,90,1,0,1],['W135',1,1,1,5,135,1,0,1],            ['W180',1,1,1,5,180,1,0,1],['W225',1,1,1,5,225,1,0,1],            ['W270',1,1,1,5,270,1,0,1],['W315',1,1,1,5,315,1,0,1],            ['Prd',1,1,1,0,0,0.9,0,1],['Pru',1,1,1,0,0,1.1,0,1],            ['Td',1,1,1,0,0,1,-5,1],['Tu',1,1,1,0,0,1,5,1],            ['Hd',1,1,1,0,0,1,0,0.9],['Hu',1,1,1,0,0,1,0,1.1]           ]

for name, scaleP, scaleM, scaleD, Vw, Bw, scalePr, shiftT, scaleH  in corners:
    vG = vGridCalc(Power=Power*scaleP, mr=mr*scaleM, Cd=Cd*scaleD, Vw=Vw, Bw=Bw, Pressure=P*scalePr, Temp=T+shiftT, Humidity=H*scaleH)
    course[name] = [vG.loc[course.headingBin[a],course.slopeBin[a]]*3.6 for a in range(len(course))]



# In[7]:

def formatTime(seconds,pos=0):
    sn = ''
    if seconds<0: sn = '-'
    m, s = divmod(int(abs(seconds)), 60)
    h, m = divmod(m, 60)
    return "{:s} {:d}:{:02d}:{:02d}".format(sn,h, m, s)

def adjT(dPower=0, dMass=0, dDrag=0, Wmph=0, Wdirn=0, Temperature=T, Pressure=P, Humidity=H):
    """ Set Time Model chart with sliders""" 
    import matplotlib.ticker as tkr 
    deltaP = 10*min(dPower,0)*(course.modelV-course.Pd) + 10*max(dPower,0)*(course.Pu-course.modelV)
    deltaM = 10*min(dMass,0)*(course.modelV-course.Md) + 10*max(dMass,0)*(course.Mu-course.modelV)
    deltaD = 10*min(dDrag,0)*(course.modelV-course.Dd) + 10*max(dDrag,0)*(course.Du-course.modelV)
    # Wmph is windspeed in mph, so need to convert to m/s
    deltaW = Wmph*(1609/3600)/5*(course['W'+str(Wdirn)]-course.modelV)
    deltaPr = 10*min((Pressure-P)/P,0)*(course.modelV-course.Prd) + 10*max((Pressure-P)/P,0)*(course.Pru-course.modelV)
    deltaT = min((Temperature-T)/5,0)*(course.modelV-course.Td) + max((Temperature-T)/5,0)*(course.Tu-course.modelV)
    deltaH = 10*min((Humidity-H)/H,0)*(course.modelV-course.Hd) + 10*max((Humidity-H)/H,0)*(course.Hu-course.modelV)
    interpV = course.modelV + deltaP + deltaM + deltaD + deltaW + deltaPr + deltaT + deltaH
    adjT = course.step/interpV*3.6
    diffT = adjT - course.modelT
    plt.rcParams['figure.figsize'] = 10, 6
    ax1=course.plot.area(x='modelD',y='altitude',color='skyblue',legend=False)
    ax1.set_xlabel('Distance (km)')
    ax1.set_ylabel('Elevation (m)')
    ax2=ax1.twinx()
    ax2.plot(course.modelD,diffT.cumsum())
    ax2.set_ylabel('TimeDelta')
    ax2.yaxis.set_major_formatter(tkr.FuncFormatter(formatTime))  
    plt.title('Power {:.0f}  Mass {:.0f}  CdA {:.2f}  Distance {:.1f}km  Speed {:.1f}km/h  Time {:s}  DeltaT {:s}'.format(Power*(1+dPower),mr*(1+dMass),A*Cd*(1+dDrag),course.distance.max()/1000,course.distance.max()/sum(adjT)*3.6,formatTime(sum(adjT)),formatTime(sum(diffT))))
    plt.show()
    return

    
from ipywidgets import interact
g=interact(adjT, dPower=(-0.5,0.5,0.01), dMass=(-0.5,0.5,0.01), dDrag=(-0.5,0.5,0.01), Wmph=(0,20,1), Wdirn=(0,315,45), Temperature=(-10,40,1), Pressure=(950,1080,1), Humidity=(10,100,1))



# # Potential next steps
# 1. Cosmetic changes to the interface. Button to reset to base settings.
# 2. Currently running needs to run with wind set to zero and then adjust - perhas needs changing.
# 3. Access historic weather datasets
# 4. Work from a GPX file rather than CSV
# 5. Create a clean version of the code without all the intermediate steps
# 6. Find historic weather conditions for Srava leader boards!!!
# 7. Run analysis for Strava segments
# 

# In[ ]:

print(course.modelV.mean())


# In[ ]:

print(course.modelT.sum())


# In[ ]:

course.modelV.plot()
course.modelSlope.multiply(10).plot()


# In[ ]:

course[['modelT','modelV','modelSlope','slopeBin','headingBin']]


# In[ ]:

print((22*60+14)/1393)


# In[ ]:

course.columns


# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:



