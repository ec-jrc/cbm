# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).

__author__ = ["Csaba Wirnhardt"]
__copyright__ = "Copyright 2021, European Commission Joint Research Centre"
__credits__ = ["GTCAP Team"]
__license__ = "3-Clause BSD"
__version__ = ""
__maintainer__ = [""]
__status__ = "Development"

import pandas as pd
import requests
import datetime
pd.options.mode.chained_assignment = None  # default='warn'

def create_list_of_tiles_to_be_downloaded_from_RESTful(MS, year, parcel_id, 
                                                        search_window_start_date, search_window_end_date,
                                                        cloud_categories, api_user, api_pass, tstype, ptype):
    
    was_error = False
    ms = MS.lower()
    if ms == "be-wa":
        ms = "bewa"


    url_base = "https://cap.users.creodias.eu"
    if ptype == "":
        url = url_base + "/query/parcelTimeSeries?aoi=" + ms + "&year=" + str(year) + "&pid=" + str(parcel_id) + "&tstype=" + tstype + "&scl=True&ref=True"
    else:
        url = url_base + "/query/parcelTimeSeries?aoi=" + ms + "&year=" + str(year) + "&pid=" + str(parcel_id) + "&ptype=" + ptype + "&tstype=" + tstype + "&scl=True&ref=True"
    print(url)
    
    try:
        response = requests.get(url, auth=(api_user, api_pass))
        print(response)
        if response.status_code == 404 or response.status_code == 500 or response.status_code == 401:
            was_error = True
            if response.status_code == 401:
                print("Please, provide valid credentials to access the RESTFul server")
            tiles_to_download = []
        else:
            df = pd.read_json(response.text)
            df = df[df['band']=='B04']
        
            if 'hist' in df.columns:
                df['cf'] = pd.Series(dtype='str')
                cloud_categories_str = str(list(map(str,cloud_categories)))
                for index, row in df.iterrows():
                    if any(x in cloud_categories_str for x in [*row['hist']]):
                        df.at[index, 'cf'] = 'False'
                    else:
                        df.at[index, 'cf'] = 'True'
                cloudfree = (df['cf'] == 'True')
                cloudfree = cloudfree[~cloudfree.index.duplicated()]
         
            df = df[cloudfree]
            df['date_part']=df['date_part'].map(lambda e: datetime.datetime.fromtimestamp(e))
            df['date_part'] = df['date_part'].apply(lambda s: s.date())  
        
            y=int(search_window_start_date.split('-')[0])
            m=int(search_window_start_date.split('-')[1])
            d=int(search_window_start_date.split('-')[2])
            search_window_start_date_date = datetime.date(y,m,d)
        
            y=int(search_window_end_date.split('-')[0])
            m=int(search_window_end_date.split('-')[1])
            d=int(search_window_end_date.split('-')[2])
            search_window_end_date_date = datetime.date(y,m,d)
        
            df=df[df['date_part']>=search_window_start_date_date]
            df=df[df['date_part']<=search_window_end_date_date]
        
            df = df.sort_values(by=['reference'])
            df.drop_duplicates(inplace=True,subset=['date_part'])
            df['tiles_to_download'] = df['reference'].apply(lambda s: s.split(".")[0])  
            tiles_to_download = df['tiles_to_download'].tolist()            
 
      
    except requests.exceptions.HTTPError as errh:
        was_error = True
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        was_error = True
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        was_error = True
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        was_error = True
        print ("OOps: Something Else",err)
        
    if was_error:
        tiles_to_download = []
        
    return tiles_to_download
