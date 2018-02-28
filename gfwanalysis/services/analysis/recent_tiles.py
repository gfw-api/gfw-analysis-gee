"""EE SENTINEL TILE URL SERVICE"""

import logging
import asyncio
import requests
import functools as funct

import ee
from gfwanalysis.errors import RecentTilesError
from gfwanalysis.config import SETTINGS


class RecentTiles(object):
    """Create dictionary with two urls to be used as webmap tiles for Sentinel 2
    data. One should be the tile outline, and the other is the RGB data visulised.
    Metadata should also be returned, containing cloud score etc.
    Note that the URLs from Earth Engine expire every 3 days.
    """

    ### TEST: http://localhost:9000/v1/recent-tiles?lat=-16.644&lon=28.266&start=2017-01-01&end=2017-02-01

    @staticmethod
    async def async_fetch(loop, f, data_array, fetch_type=None):
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
                funct.partial(f, data_array[i]),
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
    def recent_tiles(col_data, viz_params=None):
        """Takes collection data array and fetches tiles
        """
        logging.info(f"[RECENT>TILE] {col_data}")
        im = ee.Image(col_data['source']).divide(10000).visualize(bands=["B4", "B3", "B2"], min=0, max=0.3, opacity=1.0)

        if viz_params:
            m_id = im.getMapId(viz_params)
            logging.info(m_id)
        else:
            m_id = im.getMapId()

        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + m_id['mapid'] + '/{z}/{x}/{y}?token=' + m_id['token'])

        col_data['tile_url'] = url

        return col_data

    @staticmethod
    def recent_thumbs(col_data):
        """Takes collection data array and fetches thumbs
        """

        im = ee.Image(col_data['source']).divide(10000).visualize(bands=["B4", "B3", "B2"], min=0, max=0.3, opacity=1.0)

        m_id = im.getMapId()

        thumbnail = im.getThumbURL({'dimensions':[250,250]})
        logging.info(thumbnail)

        col_data['thumb_url'] = thumbnail

        return col_data

    @staticmethod
    def recent_data(lat, lon, start, end):

        logging.info("[RECENT>DATA] function initiated")

        try:
            point = ee.Geometry.Point(float(lat), float(lon))
            S2 = ee.ImageCollection('COPERNICUS/S2').filterDate(start,end).filterBounds(point).sort('CLOUDY_PIXEL_PERCENTAGE',True)

            collection = S2.toList(30).getInfo()
            data = []

            #Get boundary data (same for every tile)
            boundary_tile = ee.Feature(ee.Geometry.LinearRing(collection[0]['properties']['system:footprint']['coordinates']))

            b_id = boundary_tile.getMapId({'color': '4eff32'})
            base_url = 'https://earthengine.googleapis.com'
            boundary_url = (base_url + '/map/' + b_id['mapid'] + '/{z}/{x}/{y}?token=' + b_id['token'])

            for c in collection:

                date_info = c['id'].split('COPERNICUS/S2/')[1]
                date_time = ''.join([date_info[0:4],'-',date_info[4:6],'-',date_info[6:8],' ',
                            date_info[9:11],':',date_info[11:13],':',date_info[13:15],"Z"])

                bbox = c['properties']['system:footprint']['coordinates']

                tmp_ = {

                    'source': c['id'],
                    'cloud_score': c['properties']['CLOUDY_PIXEL_PERCENTAGE'],
                    'boundary': boundary_url,
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

            return data

        except:
            raise RecentTilesError('Recent Images service failed to return image.')
