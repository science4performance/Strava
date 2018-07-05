
# coding: utf-8

# # Scrape British Cycling
# 
# First get rider ids from ranking lists
# https://www.britishcycling.org.uk/ranking/regional/?rank_type=regional&hc=&region=4&choice=rider&year=2017&gender=M&rider_cat=16&resultsperpage=100
# 
# regions up to 30 or more (some tables are missing)
# - SE: 4
# - Yorkshire: 12
# - South: 1
# - Scotland HQ: 15
# 
# categories
# - cat 2 - 16
# - cat 3 - 28

# In[19]:

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys



# In[20]:

def BCRankings(year=2017, gender = 'M'):
    regions = [1, 4, 7, 9, 11, 12, 13, 16, 17, 23, 24, 26, 27, 28, 29, 30]
    categories = [16, 28]
    dfRank = pd.DataFrame(columns=['Rank', 'Rider', 'Club Name', 'Points', 'RiderID', 'ClubID', 'Region',
           'Year', 'Sex', 'Cat','Page'])

    for category in categories:

        for region in regions:
            url = 'https://www.britishcycling.org.uk/ranking/regional/?rank_type=regional&hc=&region={}&choice=rider&year={}&gender={}&rider_cat={}&resultsperpage=999'.format(region, year, gender, category)
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "lxml")
            options = soup.find_all('option',selected='selected')
            selected = [o.text for o in options]
            info = [selected[s] for s in [1,3,4,5]]

            table = soup.find_all('tr', "events--desktop__row")
            if len(table) > 0:   
                headers = [t.text for t in table[0].find_all('th')]
                headers += ['RiderID', 'ClubID', 'Region','Year', 'Sex', 'Cat','Page']
                print(info)
                ranking = []
                for t in table[1:]:
                    recs = t.find_all('td') 
                    p = recs[1].a['href']
                    person_id = p[(1+p.find('=')):p.find('&')]
                    p = recs[2].a['href']
                    club_id = p[(1+p.find('=')):p.find('&')]
                    page = 'https://www.britishcycling.org.uk/points?person_id={}&year={}&d=4'.format(person_id,year)
                    ranking += [[r.text.replace(u'\xa0', u' ') for r in recs]+[person_id,club_id]+info+[page]]
                df = pd.DataFrame(ranking, columns=headers)
                dfRank = pd.concat([dfRank,df], ignore_index=True)

    dfRank.Points = dfRank.Points.astype('int')
    dfRank.Rank = dfRank.Rank.astype('int')
    dfRank.to_excel('/Users/Gavin/Dropbox/LondonDynamo/BCRankings'+str(year)+gender+'.xlsx',index=False)
    
if __name__ == "__main__":
    print('Scraping rankings for ',sys.argv[1])
    BCRankings(year=sys.argv[1])


