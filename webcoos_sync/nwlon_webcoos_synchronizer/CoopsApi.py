## Note: This file is a slgithly modified copy of the GitHub repo: https://github.com/NOAA-CO-OPS/Dev_Tools_Python
## Copy/modifications occured in Sept 2024
## 
# FILENAME: CoopsApi.py
# CREATED:  2020/05/18
    
import datetime as dt
import requests
import csv as csvy
import time as time
import pandas as pd
import numpy as np
import json


# Class of data retrieval functions for CO-OPS APIs
class CoopsApi:

    def __init__(self):
        # URL information
        self.server = 'https://tidesandcurrents.noaa.gov/api/datagetter'
  
    def get_data(self, stationID,
                dateRange = None,
                product   = 'water_level',
                datum     = 'STND',
                units     = 'metric',
                timeZone  = 'gmt',
                interval  = [],
                binNum    = []):

        if dateRange is None:
            dateRange = [dt.datetime.now() - dt.timedelta(days=31), dt.datetime.now()]
        
        # define the time steps of the data
        if (product == 'one_minute_water_level'):
            step = dt.timedelta(days = 5)
        elif (product == 'hourly_height') or (product == 'high_low'):
            step = dt.timedelta(days = 365)
        elif (product == 'predictions') or (product == 'daily_mean') or (product == 'monthly_mean'):
            step = dt.timedelta(days = 10 * 365)
        else:
            step = dt.timedelta(days=31)

        # make the dictionary fields
        data = {'date_time':[],'value':[]}
        
        startDate = [dateRange[0]]

        while (startDate[-1] < dateRange[1]):
            startDate.append(startDate[-1] + step)

        if startDate[-1]>dateRange[1]:
            startDate.remove(startDate[-1])

        errorsFound = ['No errors were found']

        aDict =dict()

        server = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'
        
        # Standard user agent header to prevent government server throttling
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        # call the API recursivly
        for d in startDate:
            d2 = d + step - dt.timedelta(minutes=6)
            if d2 > dateRange[1]:
                d2 = dateRange[1]

            urlRequest = ( server   +
                        '?begin_date='  + d.strftime('%Y%m%d')    +
                        '&end_date='    + d2.strftime('%Y%m%d')   +
                        '&station='     + stationID                     +
                        '&product='     + product                       +
                        '&datum='       + datum                         +
                        '&units='       + units                         +
                        '&time_zone='   + timeZone                      +
                        '&application=OD_python&format=json' )
            
            print("Querying the data API via " + urlRequest)
            print("   -> Waiting for NOAA server response...") # --- DEBUG PRINT ---
            
            if (product=='currents') and (len(binNum)):    
                urlRequest = ( urlRequest  + '&bin=' + binNum)
                
            elif len(interval) > 0:
                urlRequest = ( urlRequest + '&interval=' + interval )

            # Read the url response with a strict 15-second timeout
            try:
                urlResponse = requests.get(urlRequest, headers=headers, timeout=15)
                print("   -> Response received. Parsing JSON...") # --- DEBUG PRINT ---
                urlResponse.raise_for_status()
                content = urlResponse.json()
            except requests.exceptions.Timeout:
                raise TimeoutError("The NOAA CO-OPS API timed out after 15 seconds. Please try again.")
            except requests.exceptions.RequestException as e:
                raise ConnectionError(f"Failed to connect to NOAA CO-OPS API: {e}")
            except json.JSONDecodeError:
                raise ValueError('Requested NWLON data product is not available or the API returned invalid JSON.')
            
            if 'error' in content:
                print(content['error'],['message'])
                raise ValueError('Requested station ID is not a valid NWLON statation.')
            else:
                k = content.keys()
                for aDict in content[list(k)[-1]]:
                    try:
                        date_time = pd.to_datetime(aDict['t'])
                    except ValueError:
                        date_time = pd.NaT
                    try:
                        value = float(aDict['v'])
                    except ValueError:
                        value = np.NaN
                    data['date_time'].append(date_time)
                    data['value'].append(value)

            output = pd.DataFrame(data)
                        
            time.sleep(3)
            
        if len(errorsFound)>1:
            errorsFound.remove(errorsFound[0])

        return output, errorsFound
