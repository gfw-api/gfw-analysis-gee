"""HISTOGRAM SERVICE"""

import logging

import ee
from gfwanalysis.errors import LandcoverError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region
from gfwanalysis.utils.landcover_lookup import lookup


class LandcoverService(object):

    @staticmethod
    def analyze(geojson, layer):
        """Take a user specified raster (currently only globcover)
        and return a dictionary of land cover type and pixel count (or area)
        type for a given geometry.

        TODO: build this out
        """

        try:
            lulc_asset_id = SETTINGS['gee']['assets'][layer]
            band_name = SETTINGS['gee']['lulc_band'].get(layer, 'b1')

            logging.info(lulc_asset_id)
            logging.info(band_name)

            lulc_band = ee.Image(lulc_asset_id).select(band_name)

            reduce_args = {'reducer': ee.Reducer.frequencyHistogram().unweighted(),
                           'geometry': get_region(geojson),
                           'scale': 27.829872698318393,
                           'bestEffort': False,
                           'maxPixels': 1e10}

            area_stats = lulc_band.reduceRegion(**reduce_args).getInfo()[band_name]

            add_lulc_names = lookup(layer, area_stats)

            return {'result': add_lulc_names}

        except Exception as error:
            logging.error(str(error))
            raise LandcoverError(message='Error in Landcover Analysis')
