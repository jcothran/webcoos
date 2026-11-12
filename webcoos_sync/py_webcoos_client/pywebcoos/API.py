# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 15:32:29 2024

@author: Matthew.Conlin
"""

import datetime
import logging 
import numpy as np
import os
import pandas as pd
import requests
import pytz

from . import timezones


class API():

    def __init__(self, token, verbose=False):
        if verbose:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)

        self.api_base_url = 'https://app.webcoos.org/webcoos/api/v1'
        self.HEADERS = {
            'Authorization': 'Token '+token,
            'Accept': 'application/json'
        }      
        self.assets_json = self._make_api_request(self.api_base_url, self.HEADERS)
        if self.assets_json is not None:
            df_cams = self._get_camera_list(self.assets_json)
            self.cameras = df_cams
        else:
            raise ValueError('API access token is not valid.')
               
    def get_cameras(self):
        return self.cameras
    
    def get_products(self, camera_name):
        self._check_camera_name(camera_name)
        
        feeds = self._get_camera_feeds(camera_name, self.assets_json)
        feed_name = 'raw-video-data'
        products = self._get_camera_products(feed_name, feeds, camera_name)
        product_labels = []
        for product in products:
            product_labels.append(product['data']['common']['label'])     
        return product_labels
    
    def get_inventory(self, camera_name, product_name):
        self._check_camera_name(camera_name)
        self._check_product_name(camera_name, product_name)
        
        feeds = self._get_camera_feeds(camera_name, self.assets_json)
        feed_name = 'raw-video-data'
        products = self._get_camera_products(feed_name, feeds, camera_name)
        service_slug, df_inv = self._get_service_slug(product_name, products, feed_name, camera_name, self.api_base_url, self.HEADERS)
        min_date = df_inv['Bin Start'].min()
        max_date = df_inv['Bin End'].max()
        return [min_date, max_date]
        
    def download(self, camera_name, product_name, start, stop, interval, save_dir):
        start = str(start)
        stop = str(stop)
        
        self._check_camera_name(camera_name)
        self._check_product_name(camera_name, product_name)
        self._check_date_format(start, 'start')
        self._check_date_format(stop, 'stop')
        self._check_date_range(camera_name, product_name, start, stop)

        start = self._local2ISO(start, camera_name)
        stop = self._local2ISO(stop, camera_name)
        feeds = self._get_camera_feeds(camera_name, self.assets_json)
        feed_name = 'raw-video-data'
        products = self._get_camera_products(feed_name, feeds, camera_name)
        service_slug, df_inv = self._get_service_slug(product_name, products, feed_name, camera_name, self.api_base_url, self.HEADERS)
        filtered_elements = self._get_elements(service_slug, start, stop, interval, self.api_base_url, self.HEADERS)
        filenames = self._download_imagery(filtered_elements, save_dir)
        return filenames
    
    def _check_camera_name(self, camera_name):
        if camera_name not in self.get_cameras()['Camera Name'].values:
            raise ValueError('Camera is not an available WebCOOS camera.')
    
    def _check_product_name(self, camera_name, product_name):
        if product_name not in self.get_products(camera_name):
            raise ValueError('Requested product is not available at this camera.')
            
    def _check_date_format(self, date, date_name):
        if len(date) != 12:
            raise ValueError('Requested '+date_name+' date is of improper format. Format should be yyyymmddHHMM.')
        else:
            try:
                datetime.datetime(int(date[0:4]), int(date[4:6]), int(date[6:8]), int(date[8:10]), int(date[10:12]))
            except ValueError:
                raise ValueError('Requested '+date_name+' date is of improper format. Format should be yyyymmddHHMM.')        
    
    def _check_date_range(self, camera_name, product_name, start, stop):
        starts = self._local2ISO(start, camera_name)
        stops = self._local2ISO(stop, camera_name)
        ss = []
        for s in [starts, stops]:
            ss.append(datetime.datetime(int(s[0:4]), int(s[5:7]), int(s[8:10]), int(s[11:13]), int(s[14:16])))
            
        dr = self.get_inventory(camera_name, product_name)
        dtr = []
        for d in dr:
            dtr.append(datetime.datetime(int(d[0:4]), int(d[5:7]), int(d[8:10]), int(d[11:13]), int(d[14:16])))
        
        if dtr[0] <= ss[0] <= dtr[1] and dtr[0] <= ss[1] <= dtr[1]:
            pass
        else:
            raise ValueError('At least one requested date bound is outside the range of available data for this product at this camera.')  
            
    def _make_api_request(self, api_base_url, HEADERS):
        response = requests.get(f"{api_base_url}/assets/", headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to retrieve assets: {response.status_code} {response.text}")
            return None
      
    def _get_camera_list(self, assets_json):
        camera_names = [asset['data']['common']['label'] for asset in assets_json['results']]
        df_cams = pd.DataFrame(camera_names, columns=['Camera Name'])
        return df_cams
     
    def _get_camera_feeds(self, camera_name, assets_json):
        for asset in assets_json['results']:
            if asset['data']['common']['label'] == camera_name:
                feeds = asset['feeds']
                break
        return feeds

    def _get_camera_products(self, feed_name, feeds, camera_name):
        for feed in feeds:
            if feed['data']['common']['label'] == feed_name:
                products = feed['products']
        return products
                        
    def _get_service_slug(self, product_name, products, feed_name, camera_name, api_base_url, HEADERS):
        for product in products:
            if product['data']['common']['label'] == product_name:
                logging.info(f"Services for camera '{camera_name}', feed '{feed_name}' and product '{product_name}':")
                services = product['services']
                for service in services:
                    service_slug = service['data']['common']['slug']
                    logging.info(service_slug)
                break

        inv_url = f"{api_base_url}/services/{service_slug}/inventory/"
        response = requests.get(inv_url, headers=HEADERS, timeout=15)

        if response.status_code == 200:
            inventory_json = response.json()
        else:
            logging.error(f"Failed to retrieve assets: {response.status_code} {response.text}")

        inventory_data = inventory_json['results'][0]['values']
        df_inv = pd.DataFrame(inventory_data, columns=['Bin Start', 'Has Data?', 'Bin End', 'Count', 'Bytes', 'Data Start', 'Data End'])

        return service_slug, df_inv
    
    def _get_elements(self, service_slug, start_time, end_time, interval_minutes, api_base_url, HEADERS):
        params = {
            'starting_after': start_time,
            'starting_before': end_time,
            'service': service_slug
        }

        base_url = f'{api_base_url}/elements/'
        all_elements = []
        page = 1

        while True:
            logging.info(f"Fetching page: {page}")
            response = requests.get(base_url, headers=HEADERS, params=params, timeout=15)
            if response.status_code != 200:
                logging.error(f"Failed to fetch page {page}: {response.status_code}")
                break
            data = response.json()
            all_elements.extend(data['results'])
            logging.info(f"Received {len(data['results'])} elements, total elements collected: {len(all_elements)}")

            next_url = data.get('pagination', {}).get('next')
            if not next_url:
                logging.info("No more pages.")
                break
            base_url = next_url
            params = None
            page += 1

        filtered_elements = []
        logging.info("Timestamps of filtered elements")
        for element in all_elements:
            timestamp_str = element['data']['extents']['temporal']['min']
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
            if timestamp.minute % interval_minutes == 0:
                filtered_elements.append(element)
                logging.info(timestamp)
        return filtered_elements

    def _download_imagery(self, filtered_elements, save_dir):
        download_urls = []
        for element in filtered_elements:
            try:
                download_url = element['data']['properties']['url']
                download_urls.append(download_url)
            except KeyError:
                logging.error("Unexpected element structure:", element)

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        logging.info("Beginning imagery download")
        filenames = []
        for url in download_urls:
            filename = os.path.join(save_dir, os.path.basename(url)).replace(':','')
            filenames.append(filename)
            
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                logging.info('Downloading')
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status() 
                
                with open(filename, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                logging.info('Download complete')
            else:
                logging.info('File already cached locally, skipping download.')
                
        logging.info(f"Download complete. Downloaded {len(download_urls)} images to {save_dir}")

        return filenames
   
    def _local2ISO(self, local_time, camera_name):
        i_camera = int(np.where(self.cameras['Camera Name'] == camera_name)[0][0])      
        try:
            self.tz = self.assets_json['results'][i_camera]['data']['properties']['timezone']
        except KeyError: 
            try: 
                self.tz = timezones.from_name(camera_name)
            except ValueError:
                self.tz = 'UTC'
                logging.warning('Timezone of camera could not be detected or derived, defaulting to UTC.')
            else:
                logging.info('Camera timezone could not be detected, but was derived from camera name')
        else:
            logging.info('Camera timezone detected')
                
        dt_local = datetime.datetime(int(local_time[0:4]),
                                     int(local_time[4:6]),
                                     int(local_time[6:8]),
                                     int(local_time[8:10]),
                                     int(local_time[10:12]))
        dt_local = pytz.timezone(self.tz).localize(dt_local)
        dt_utc = dt_local.astimezone(pytz.timezone('UTC'))
        ISO = dt_utc.isoformat()
        return ISO
