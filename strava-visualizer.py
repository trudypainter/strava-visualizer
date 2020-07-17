#!/usr/bin/env python
# coding: utf-8

# In[1]:


import stravaio
from stravaio import strava_oauth2
import requests
from stravaio import StravaIO
import bs4 as bs
import google_streetview
import google_streetview.api
import math
import os
import shutil
import cv2
import numpy as np
import glob

output = strava_oauth2(client_id='', client_secret='')
# If the token is stored as an environment varible it is not neccessary
# to pass it as an input parameters


# ## Gathering user routes

# In[2]:


access_token = str(output["access_token"])
client = StravaIO(access_token=access_token)

athlete = client.get_logged_in_athlete().to_dict()
athlete_id = athlete["id"]

endpoint = "https://www.strava.com/api/v3/athletes/"+str(athlete_id)+"/routes"
headers = {"Authorization": "Bearer "+str(access_token)}

athlete_routes = requests.get(endpoint, headers=headers).json()
route_ids = []

for route in athlete_routes:
    route_ids.append(route["id"])
    
print(route_ids)


# In[3]:


def calculate_initial_compass_bearing(pointA, pointB):
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


# In[4]:


# [route name, [point pairs]]
info_list = []
lat = []
lon = []

#need to add {id} in url
for i in range(0,1):
    name = athlete_routes[i]["name"]
    
    endpoint = "https://www.strava.com/api/v3/routes/"+str(route_ids[i])+"/export_gpx"
    headers = {"Authorization": "Bearer "+str(access_token)}

    response = requests.get(endpoint, headers=headers)

    soup = bs.BeautifulSoup(response.content,'xml')
    
    for item in soup.find_all("trkpt"):
        lat.append(item.get('lat'))
        lon.append(item.get('lon'))

    point_pairs = []
    headings = []

    for index in range(len(lat)):
        #create list of tuples of coordinated
        point_pairs.append((float(lat[index]), float(lon[index])))
    
                           
    for i in range(1, len(point_pairs)):
        
        headings.append([point_pairs[i][0], point_pairs[i][1],
                         0])
        
    info_list.append([name, headings])
    
info_list


# ## Downloading Images to File from Google Street View

# In[5]:


for item in info_list:
    
    coords = item[1]
    count = 0
    
    for coord in coords[1:]:
        location = str(coord[0])+","+str(coord[1])
        # Define parameters for street view api
        params = [{
        'size': '600x300', # max 640x640 pixels
        'location': location,
        'heading': str(coord[2]),
        'pitch': '-0.76',
        'key': 'AIzaSyCNoMA5lceKVpRp5ZxASsSdGopZgBWt3yA'
        }]
        print(params)

        # Create a results object
        results = google_streetview.api.results(params)
        print(results.metadata)

        #download links to name of route
        results.download_links('downloads/'+ item[0] + "/" + str(count))
        try:
            os.rename('downloads/'+ item[0] + "/" + str(count) + "/gsv_0.jpg", 
                      'downloads/'+ item[0] + "/" + str(count) + ".jpg")
            shutil.rmtree('downloads/'+ item[0] + "/" + str(count))
        except:
            shutil.rmtree('downloads/'+ item[0] + "/" + str(count))
            
        count+=1
        
    img_array = []
    for filename in glob.glob('downloads/' + item[0] + "/*.jpg"):
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width,height)
        img_array.append(img)


    shutil.rmtree('downloads/'+ item[0])
    out = cv2.VideoWriter('downloads/' + item[0] +'.avi',cv2.VideoWriter_fourcc(*'DIVX'), 15, size)

    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()
        


# In[ ]:




