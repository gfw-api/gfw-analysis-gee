"""EE LANDSAT TILE URL SERVICE"""

import logging

import ee
from gfwanalysis.errors import LandsatTilesError
from gfwanalysis.config import SETTINGS


class LandsatTiles(object):
    """Create a target url to be used as webmap tiles for Landsat annual data images.
    Input should be the year of the composited images to create. Note that this is
    necessary because the URLs from Earth Engine expire every 3 days.
    """

    @staticmethod
    def tile_url(image, viz_params=None):
        """Create a target url for tiles for an image. e.g.:
        im = ee.Image("LE7_TOA_1YEAR/" + year).select("B3","B2","B1")
        viz = {'opacity': 1, 'gain':3.5, 'bias':4, 'gamma':1.5}
        url = tile_url(image=im),viz_params=viz)
        """
        if viz_params:
            d = image.getMapId(viz_params)
        else:
            d = image.getMapId()
        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
        return url

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
    def analyze(year):
        """For a given year, generate a valid url from which to retrieve Landsat
        tiles directly from Earth Engine. This is necessary as the urls expire.
        Currently, only 2015 and 2016 are supported as input years.
        """
        try:
            d = {}
            if int(year) in [2013, 2014, 2015, 2016]:
                image = LandsatTiles.pansharpened_L8_image(year)
                d['url'] = LandsatTiles.tile_url(image)
            else:
                logging.warning("Bad: URL for tiles for year={0} requested".format(year))
                d['url'] = None
            return d
        except Exception as error:
            logging.error(str(error))
            raise LandsatTilesError(message='Landsat Tile URL creation Error')
