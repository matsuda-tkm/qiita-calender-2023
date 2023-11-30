import requests
from datetime import datetime
import numpy as np
import pandas as pd
import json
from tqdm import tqdm


with open('appid.json') as f:
    APPID = json.load(f)['ClientID']

def get_json(lat_list:list[int], lon_list:list[int], date:str):
    """
    Retrieves weather data in JSON format from the Yahoo! Weather API based on the given latitude, longitude, and date.

    Args:
        lat_list (list[int]): A list of latitude values.
        lon_list (list[int]): A list of longitude values.
        date (str): The date for which weather data is requested in the format 'YYYYMMDDHHMI'.

    Returns:
        dict: A dictionary containing the weather data in JSON format.

    Example:
        lat_list = [35.6895, 37.7749]
        lon_list = [139.6917, -122.4194]
        date = '202303011200'
        weather_data = get_json(lat_list, lon_list, date)
    """
    # check length of lat_list and lon_list (more than 10 is not allowed)
    if len(lat_list) > 10 or len(lon_list) > 10:
        print(f'**ERROR** Please specify less than 10 coordinates: {len(lat_list)}, {len(lon_list)}')
        exit()

    # check date (more than 2hour ago is not allowed)
    now = datetime.now()
    date_formatted = datetime.strptime(date, '%Y%m%d%H%M')
    if (now - date_formatted).total_seconds() >= 7200:
        print(f'**ERROR** Please specify a date_formattedwithin 2 hours: {date_formatted}')
        exit()

    # create URL
    pos_list = [f'{lon:.6f},{lat:.6f}' for lat,lon in zip(lat_list,lon_list)]
    pos_str = ' '.join(pos_list)
    URL = f'https://map.yahooapis.jp/weather/V1/place?coordinates={pos_str}&appid={APPID}&output=json&date={date}&interval=5&past=0'

    # check length of URL (more than 2048Byte is not allowed)
    if len(URL.encode('utf-8')) > 2048:
        print(f'**ERROR** URL is too long: {len(URL.encode("utf-8"))} Byte')

    # get data
    response = requests.get(URL)
    data = response.json()

    # check response
    if response.status_code != 200:
        print(f'**ERROR** Response Error : {data}\n{URL}')
        exit()

    # check coordinates
    for i in range(data['ResultInfo']['Count']):
        get_coord = data['Feature'][i]['Geometry']['Coordinates']
        org_coord = pos_list[i]
        if get_coord != org_coord:
            print(f'**ERROR** The specified latitude and longitude are invalid: {get_coord}, {org_coord}')
            exit()

    return data

def ext_data(data: dict):
    """
    Extracts rainfall values from the given data dictionary.

    Args:
        data (dict): The data dictionary containing weather information from the Yahoo! Weather API.

    Returns:
        np.ndarray: A two-dimensional array containing the rainfall values. The shape is (len(lat_list), 60//interval).
        list[str]: A list of dates corresponding to the rainfall values.
    """
    values,dates = [],[]
    dates = [time['Date'] for time in data['Feature'][0]['Property']['WeatherList']['Weather'] if time['Type']=='observation']
    for i in range(data['ResultInfo']['Count']):
        weather = data['Feature'][i]['Property']['WeatherList']['Weather']
        value = [time['Rainfall'] for time in weather if time['Type']=='observation']
        values.append(value)
    values = np.array(values)
    return values,dates

if __name__ == '__main__':
    DATE = '202311291100'
    LAT_RANGE = (36.0, 38.0)
    LON_RANGE = (136.5, 139.5)
    GRID_SIZE = 0.01
    
    # create lat_list and lon_list
    lat_list = np.arange(LAT_RANGE[0], LAT_RANGE[1], GRID_SIZE)
    lon_list = np.arange(LON_RANGE[0], LON_RANGE[1], GRID_SIZE)
    lat_list, lon_list = np.meshgrid(lat_list, lon_list)
    lat_list = lat_list.flatten()
    lon_list = lon_list.flatten()

    # get data
    try:
        for i in tqdm(range(0, len(lat_list), 10)):
            data = get_json(lat_list[i:i+10], lon_list[i:i+10], DATE)
            if i == 0:
                values,dates = ext_data(data)
            else:
                values = np.concatenate([values, ext_data(data)[0]], axis=0)
    except Exception as e:
        print('**Error**:', e)
        
    # save data to csv
    df = pd.DataFrame({'lat':lat_list, 'lon':lon_list})
    df_values = pd.DataFrame(values, columns=dates)
    df = pd.concat([df, df_values], axis=1)
    df.to_csv('data.csv', index=False)

    print('Success!')
