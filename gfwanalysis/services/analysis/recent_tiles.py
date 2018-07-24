"""EE SENTINEL TILE URL SERVICE"""

import logging
import asyncio
import requests
import functools as funct

import ee
from gfwanalysis.errors import RecentTilesError
from gfwanalysis.config import SETTINGS

SENTINEL_BANDS = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']
S2_TO_L8_DICT = {
    'B12': 'B7',
    'B11': 'B6',
    'B10': None,
    'B9': None,
    'B8': 'B5',
    'B8A': 'B5',
    'B7': None,
    'B6': None,
    'B5': None,
    'B4': 'B4',
    'B3': 'B3',
    'B2': 'B2',
}

class RecentTiles(object):
    """Create dictionary with two urls to be used as webmap tiles for Sentinel 2
    data. One should be the tile outline, and the other is the RGB data visulised.
    Metadata should also be returned, containing cloud score etc.
    Note that the URLs from Earth Engine expire every 3 days.
    """

    ### TEST: http://localhost:4500/api/v1/recent-tiles?lat=-16.644&lon=28.266&start=2017-01-01&end=2017-02-01

    @staticmethod
    def validate_bands(bands, instrument):
        """Validate and serialide bands
        """
        logging.info(f"[RECENT>BANDS] function initiated, validating for {instrument}")

        #Format
        if type(bands) == str:
            bands = bands[1:-1].split(',')
        
        parsed_bands = [ b.upper() if b.upper() in SENTINEL_BANDS else None for b in bands ]

        # Check for dupes
        seen = set()
        uniq = [b for b in bands if b not in seen and not seen.add(b)]  

        #Convert if Landsat
        if 'LANDSAT' in instrument:
            parsed_bands = [ S2_TO_L8_DICT[b] for b in parsed_bands ]

        #Validate bands
        if(len(parsed_bands) != 3 or len(uniq) != 3):
            raise RecentTilesError('Must contain 3 unique elements in the format: [r,b,g].')
        elif(None in parsed_bands):
            raise RecentTilesError('One or more bands are invalid.')
        else:
            logging.info(f"[RECENT>BANDS] bands {parsed_bands} validated")
            return parsed_bands
            

    @staticmethod
    async def async_fetch(loop, f, data_array, bands, fetch_type=None):
        """Takes collection data array and implements batch fetches
        """
        asyncio.set_event_loop(loop)

        if fetch_type == 'first':
            r1 = 0
            r2 = 1

        elif fetch_type == 'rest':
            r1 = 1
            r2 = len(data_array)

        else:
            r1 = 0
            r2 = len(data_array)

        # Set up list of futures (promises)
        futures = [
            loop.run_in_executor(
                None,
                funct.partial(f, data_array[i], bands),
            )
            for i in range(r1, r2)
        ]
        # Fulfill promises
        for response in await asyncio.gather(*futures):
            pass

        return_results = []
        for f in range(0, len(futures)):
            data_array[f] = futures[f].result()

        return data_array

    @staticmethod
    def recent_tiles(col_data, bands=None):
        """Takes collection data array and fetches tiles
        """
        logging.info(f"[RECENT>TILE] {col_data}")

        validated_bands = ["B4", "B3", "B2"]
        if bands: validated_bands = RecentTiles.validate_bands(bands, col_data.get('source'))

        maximum=0.3    
        if 'LANDSAT' in col_data.get('source'): maximum=2
        
        im = ee.Image(col_data['source']).divide(10000).visualize(bands=validated_bands, min=0, max=maximum, opacity=1.0)
        
        m_id = im.getMapId()

        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + m_id['mapid'] + '/{z}/{x}/{y}?token=' + m_id['token'])

        col_data['tile_url'] = url

        return col_data

    @staticmethod
    def recent_thumbs(col_data, bands=None):
        """Takes collection data array and fetches thumbs
        """
        logging.info(f"[RECENT>THUMB] {col_data}")

        validated_bands = ["B4", "B3", "B2"]
        if bands: validated_bands = RecentTiles.validate_bands(bands, col_data.get('source'))

        maximum=0.3    
        if 'LANDSAT' in col_data.get('source'): maximum=2          

        im = ee.Image(col_data['source']).divide(10000).visualize(bands=validated_bands, min=0, max=maximum, opacity=1.0)
        thumbnail = im.getThumbURL({'dimensions':[250,250]})
        logging.info(thumbnail)

        col_data['thumb_url'] = thumbnail

        return col_data

    @staticmethod
    def recent_data(lat, lon, start, end):

        logging.info("[RECENT>DATA] function initiated")
        
        try:
        
            point = ee.Geometry.Point(float(lat), float(lon))
            S2 = ee.ImageCollection('COPERNICUS/S2').filterDate(start,end).filterBounds(point)
            L8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_RT').filterDate(start,end).filterBounds(point)

            collection = S2.toList(52).cat(L8.toList(52)).getInfo()

            data = []

            for c in collection:

                if c.get('properties').get('SPACECRAFT_NAME') and c.get('properties').get('SPACECRAFT_NAME') == 'Sentinel-2A':
                    
                    date_info = c['id'].split('COPERNICUS/S2/')[1]
                    date_time = ''.join([date_info[0:4],'-',date_info[4:6],'-',date_info[6:8],' ',
                                date_info[9:11],':',date_info[11:13],':',date_info[13:15],"Z"])

                    bbox = c['properties']['system:footprint']['coordinates']

                    tmp_ = {

                        'source': c['id'],
                        'cloud_score': c['properties']['CLOUDY_PIXEL_PERCENTAGE'],
                        'bbox': {
                                "geometry": {
                                "type": "Polygon",
                                "coordinates": bbox
                                }
                            },
                        'spacecraft': c['properties']['SPACECRAFT_NAME'],
                        'product_id': c['properties']['PRODUCT_ID'],
                        'date': date_time

                    }
                    data.append(tmp_)

                elif c.get('properties').get('SPACECRAFT_ID') and c.get('properties').get('SPACECRAFT_ID') == 'LANDSAT_8':
                    date_info = c['id'].split('LANDSAT/LC08/C01/T1_RT/LC08_')[1].split('_')[1]
                    time_info = c['properties']['SCENE_CENTER_TIME'].split('.')[0]
                    date_time = ''.join([date_info[0:4],'-',date_info[4:6],'-',date_info[6:8],' ', time_info, 'Z' ])

                    bbox = c['properties']['system:footprint']['coordinates']

                    tmp_ = {

                        'source': c['id'],
                        'cloud_score': c['properties']['CLOUD_COVER'],
                        'bbox': {
                                "geometry": {
                                "type": "Polygon",
                                "coordinates": bbox
                                }
                            },
                        'spacecraft': c['properties']['SPACECRAFT_ID'],
                        'product_id': c['properties']['LANDSAT_PRODUCT_ID'],
                        'date': date_time

                    }
                    data.append(tmp_)

            logging.info('[RECENT>DATA] sorting by cloud cover & date of acquisition')
            sorted_data = sorted(data, key=lambda k: (-k.get('cloud_score',100), k.get('date')), reverse=True)

            return sorted_data

        except:
            raise RecentTilesError('Recent Images service failed to return image.')
