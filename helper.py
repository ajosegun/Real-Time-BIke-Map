# Import necessary modules

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import datetime
import os

ACCESS_MAP_TOKEN = os.environ['ACCESS_MAP_TOKEN']

CITYBIK_URL = "http://api.citybik.es/v2/networks"

# city_bike_networks = requests.get(CITYBIK_URL).json()

def get_city_data(city):
    
  city_bike_networks = requests.get(CITYBIK_URL).json()

  list_of_dicts = []
  for city_bike_dict in city_bike_networks['networks']:
      new_city = city_bike_dict['location']['city']
      if new_city.lower() == city.lower():
          list_of_dicts.append(city_bike_dict)
          
  return list_of_dicts

def get_all_cities():
    response = requests.get(CITYBIK_URL)

    if response.status_code == 200:
        data = response.json()
        networks = data['networks']
        cities = [network['location']['city'] for network in networks]
        return sorted(cities)
    else:
        return 'Failed to retrieve data from the API'

def get_stations_info_in_city(city):
    
    station_dict = get_city_data(city)
    if not station_dict:
        print("Error: No bike company found for {}".format(city))
        return None

    network_address = station_dict[0]['href']
    url = "http://api.citybik.es/{}".format(network_address)
    return requests.get(url).json()['network']['stations']

def get_list_of_stations_names_in_city(city):
    all_station_info = get_stations_info_in_city(city)

    station_name = []
    for each_station in all_station_info:
        station_name.append(each_station['name'])

    return sorted(station_name)



def get_available_stations(city = "Paris"):
    '''
    Takes in the city name and returns a pandas dataframe containing information about the city
    Default city name is Paris
    '''
    station_info = get_stations_info_in_city(city)
    
    station_list = []
    for info in station_info:

        if 'banking' in info['extra']:
            banking_info = info['extra']['banking']
        else:
            banking_info = False

        a_dict = {
            'Station Name': info['name'],
            'empty_slots' : info['empty_slots'],
            'free_bikes' : info['free_bikes'],
            'ebikes' : info['extra']['ebikes'] if "ebikes" in info['extra'] else 0,
            'payment': ', '.join(info['extra']['payment'] if 'payment' in info['extra'] else "No") if banking_info else "No" ,
            'latitude' : info['latitude'],
            'longitude' : info['longitude'],
            'timestamp' : info['timestamp'],
            'Unique ID': info['extra']['uid'],
        }
        station_list.append(a_dict)
        
    return pd.DataFrame(station_list)


def get_location_data(station_name, live_station_data):
    '''
    This method requests input from the biker and returns either of the following 
    - Location data a single location is found for the input
    - No data if the entry is quit  
    
    It displays a list of locations if the input matches more than one location
    - It requests the biker to input the full name of the location from the displayed list
    '''
    
    requested_station_data = live_station_data[live_station_data["Station Name"].map(lambda name: station_name.lower() in name.lower())]

    if len(requested_station_data.index) == 1:
        return requested_station_data
    
    elif requested_station_data.empty:
        return None


def show_bar_chart(requested_station_data):

    '''
    Takes in the station data (Pandas dataframe ) and current data
    Shows a bar chart of the information
    Returns nothing
    '''
    
    if requested_station_data.empty:
        # print("Error: Station data is not available!")
        return None
    
    current_date = pd.to_datetime(requested_station_data['timestamp'].iloc[0]).strftime('%a %d %B, %Y at %H:%M')
    
    mylabels = ["Empty Slots", "Free Bikes", "ebikes"]
    
    data = [int(requested_station_data["empty_slots"]), 
            int(requested_station_data["free_bikes"]), 
            int(requested_station_data["ebikes"]),
             ]
    
    # Create a trace for the bar chart
    colors = ['blue', 'green', 'yellow']
    trace = go.Bar(x=mylabels, y=data, marker=dict(color=colors))

    # Create a layout for the chart
    title = "Bike information for: {0} - \nPayment type - {1} on \n{2}".format(
                    requested_station_data["Station Name"].to_string(index=False),
                    requested_station_data["payment"].to_string(index=False),
                    current_date)
    layout = go.Layout(title=title)

    # Create a figure and add the trace and layout
    fig = go.Figure(data=[trace], layout=layout)

    return fig


def get_user_city_from_ip():
    # Automatically get user IP address
    ip_url = "https://api.ipify.org"
    ip_address = requests.get(ip_url).text

    # Use an IP geolocation service to get the user's location information
    geolocation_url = f"https://ipapi.co/{ip_address}/json/"

    # geolocation_url = f'http://ip-api.com/json/{ip_address}?fields=16576'

    response = requests.get(geolocation_url)

    if response.status_code == 200:
        data = response.json()
        city = data.get('city', '')
        return city 
    else:
        return "Could not get your location."
    

def show_map(station_data, city):
    '''
    Takes in data of the station info in a dataframe format
    
    Shows a map
    '''

    ## Get the current date and time
    current_date = pd.to_datetime(station_data['timestamp'][0]).strftime('%a %d %B, %Y at %H:%M')
        
    map_title = 'Map Showing Number of Bikes in {} at {}'.format(city, current_date)

    # Get access token from ploty
    px.set_mapbox_access_token(ACCESS_MAP_TOKEN)

    fig = px.scatter_mapbox(station_data, lat="latitude", lon="longitude", hover_name="Station Name", color="free_bikes",
                            hover_data=["empty_slots", "free_bikes", "ebikes", "payment"],
                             title=map_title, 
                              color_continuous_scale=px.colors.sequential.Plasma, size_max=20,zoom=12)


    return fig
    # fig.show()
