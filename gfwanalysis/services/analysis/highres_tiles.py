"""EE SENTINEL TILE URL SERVICE"""

import logging

import ee
from gfwanalysis.errors import LandsatTilesError
from gfwanalysis.config import SETTINGS


class HighResTiles(object):
    """Create dictionary with two urls to be used as webmap tiles for Sentinel 2
    data. One should be the tile outline, and the other is the RGB data visulised.
    Metadata should also be returned, containing cloud score etc.
    Note that the URLs from Earth Engine expire every 3 days.
    """

    @staticmethod
    def tile_url2(image, viz_params=None):
        logging.info("[TILE_URL] function initiated")
        """Create a target url for tiles for an image.
        """
        if viz_params:
            d = image.getMapId(viz_params)
            logging.info(d)
        else:
            d = image.getMapId()
        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
        logging.info(url)
        return url

    @staticmethod
    def proxy_highres(lat, lon, start, end):
        """
        Sentinel covers all continental land surfaces (including inland waters) between latitudes 56° south and 83° north
            all coastal waters up to 20 km from the shore
            all islands greater than 100 km2
            all EU islands
            the Mediterranean Sea
            all closed seas (e.g. Caspian Sea).

        This will return a JSON object of n elements, with each element containing an image url, thumbnail url, boundary tiles
        (and related metadata) for each Sentinel image taken  at (lat, lon) within the time range (start - end).

        Note the url generated expires after a few days and needs to be refreshed.
        e.g. variables
        lat = -16.66
        lon = 28.24
        start = '2017-01-01'
        end = '2017-03-01'
        """
        logging.info("[HIGH RES] function initiated")

        try:
            point = ee.Geometry.Point(float(lon), float(lat))
            S2 = ee.ImageCollection('COPERNICUS/S2').filterDate(start,end).filterBounds(point)
            S2_list = S2.toList(S2.size().getInfo())

            output = []

            for x in range (0, S2.size().getInfo()):

                d = S2_list.getInfo()[x] ##access asset id
                S2 = ee.Image(d.get('id'))
                S2 = S2.divide(10000)  # Convert to Top of the atmosphere reflectance
                S2 = S2.visualize(bands=["B4", "B3", "B2"], min=0, max=0.3, opacity=1.0)

                image_tiles = HighResTiles.tile_url2(S2)
                thumbnail = S2.getThumbURL({'dimensions':[250,250]})

                boundary = ee.Feature(ee.Geometry.LinearRing(d.get('properties').get("system:footprint").get('coordinates')))
                boundary_tiles = HighResTiles.tile_url2(boundary, {'color': '4eff32'})

                meta = HighResTiles.get_image_metadata2(d)

                temp_output = {

                    'boundary_tiles': boundary_tiles,
                    'tile_url': image_tiles,
                    'thumbnail_url': thumbnail,
                    'metadata': meta,
                    'success': True

                }

                output.append(temp_output)
            return output

        except:
            raise ValueError('High Res service failed to return image.')

    @staticmethod
    def get_image_metadata2(d):
        """Return a dictionary of metadata"""
        image_name = d.get('id')
        source = d["properties"]['SPACECRAFT_NAME']
        cloud_score = d["properties"]['CLOUDY_PIXEL_PERCENTAGE']
        date_info = image_name.split('COPERNICUS/S2/')[1]
        date_time = ''.join([date_info[0:4],'-',date_info[4:6],'-',date_info[6:8],' ',
                        date_info[9:11],':',date_info[11:13],':',date_info[13:15],"Z"])
        product_id = d.get('properties').get('PRODUCT_ID')
        meta = {}
        meta = {'source': source, 'image_name': image_name, 'cloud_score': cloud_score, 'date_time': date_time, 'product_id': product_id}
        return meta