"""EE LANDSAT TILE URL SERVICE"""

import logging
import redis
import json
import ee

from gfwanalysis.errors import LandsatTilesError
from gfwanalysis.config import SETTINGS

r = redis.StrictRedis.from_url(url=SETTINGS.get('redis').get('url'))

class RedisService(object):

    @staticmethod
    def check_year_mapid(year):
        text = r.get(year)
        if text is not None:
            return json.loads(text)
        return None

    @staticmethod
    def get(year):
        text = r.get(year)
        if text is not None:
            return text
        return None

    @staticmethod
    def set_year_mapid(year, mapid, token):
        return r.set(year, json.dumps({'mapid': mapid, 'token': token}), ex=2 * 24 * 60 * 60)


class LandsatTiles(object):
    """Create a target url to be used as webmap tiles for Landsat annual data images.
    Input should be the year of the composited images to create. Note that this is
    necessary because the URLs from Earth Engine expire every 3 days.
    """

    @staticmethod
    def tile_url_gcs(year, z, x, y):
        """Create a target url for tiles in the Google
           Cloud Store.
        """
        base_url = 'https://storage.googleapis.com'
        url = f'{base_url}/landsat-cache/{year}/{z}/{x}/{y}.png'
        return url

    @staticmethod
    def tile_url_gee(image, z, x, y, viz_params=None):
        """Create a target url for tiles for an image. e.g.:
        im = ee.Image("LE7_TOA_1YEAR/" + year).select("B3","B2","B1")
        viz = {'opacity': 1, 'gain':3.5, 'bias':4, 'gamma':1.5}
        url = tile_url(image=im),viz_params=viz)
        """
        if viz_params:
            map_object = image.getMapId(viz_params)
        else:
            map_object = image.getMapId()
        base_url = 'https://earthengine.googleapis.com'
        url = f'{base_url}/map/'+ map_object['mapid']+f'/{z}/{x}/{y}'+'?token='+ map_object['token']
        return url, map_object

    @staticmethod
    def pansharpened_L8_image(year):
        collection = ee.ImageCollection('LANDSAT/LC8_L1T').filterDate(
                            "{0}-01-01T00:00".format(year), "{0}-12-31T00:00".format(year))
        composite = ee.Algorithms.Landsat.simpleComposite(collection=collection,
                            percentile=50, maxDepth=80, cloudScoreRange=1, asFloat=True)
        hsv2 = composite.select(['B4', 'B3', 'B2']).rgbToHsv()
        sharpened = ee.Image.cat([hsv2.select('hue'), hsv2.select('saturation'),
                            composite.select('B8')]).hsvToRgb().visualize(
                            gain=1000, gamma= [1.15, 1.4, 1.15])
        return sharpened

    @staticmethod
    def iker_image(year):
        """Your function should return an EE.Image instance"""
        logging.warning(f"[Iker Image] -- using year {year}")
        pass
        return 
    

    @staticmethod
    def analyze(year, z, x, y, map_object):
        """For a given year, generate a valid url from which to retrieve Landsat
        tiles directly from Earth Engine. This is necessary as the urls expire.
        Currently, only 2015 and 2016 are supported as input years.
        """
        try:
            d = {}
            if int(z) < 12:
                d['url'] = LandsatTiles.tile_url_gcs(year, z, x, y)
            elif int(z) >= 12:
                if map_object is None:
                    logging.debug('Generating mapid')
                    if int(year) in [2013, 2014, 2015, 2016, 2017]:
                        image = LandsatTiles.pansharpened_L8_image(year)
                        d['url'], map_object = LandsatTiles.tile_url_gee(image, z, x, y)
                    elif int(year) in [2012]:
                        image = LandsatTiles.iker_image(year)
                        d['url'], map_object = LandsatTiles.tile_url_gee(image, z, x, y)
                    else:
                        logging.warning("Bad: URL for tiles for year={0} requested".format(year))
                        d['url'] = None

                    logging.debug('Saving in cache')

                    RedisService.set_year_mapid(year, map_object.get('mapid'), map_object.get('token'))
                else:
                    base_url = 'https://earthengine.googleapis.com'
                    url = f'{base_url}/map/'+ map_object['mapid']+f'/{z}/{x}/{y}'+'?token='+ map_object['token']
                    d['url'] = url

            return d
        except Exception as error:
            logging.error(str(error))
            raise LandsatTilesError(message='Landsat Tile URL creation Error')
