"""HISTOGRAM SERVICE"""

import logging

import ee

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import LandcoverError
from gfwanalysis.utils.geo import get_region
from gfwanalysis.utils.landcover_lookup import lookup
from gfwanalysis.utils.parse_gee_response import flatten_area_hist


class LandcoverService(object):

    @staticmethod
    def analyze(geojson, layer, count_pixels):
        """Take a user specified raster (currently only globcover)
        and return a dictionary of land cover type and pixel count (or area)
        type for a given geometry.
        """

        try:
            lulc_asset_id = SETTINGS['gee']['assets'][layer]
            band_name = SETTINGS['gee']['lulc_band'].get(layer, 'b1')

            logging.info(lulc_asset_id)
            logging.info(band_name)

            lulc_band = ee.Image(lulc_asset_id).select(band_name)

            if count_pixels:
                reducer = ee.Reducer.frequencyHistogram().unweighted()

            else:
                reducer = ee.Reducer.frequencyHistogram().unweighted().group()
                lulc_band = lulc_band.addBands([ee.Image.pixelArea()])

            reduce_args = {'reducer': reducer,
                           'geometry': get_region(geojson),
                           'scale': 27.829872698318393,
                           'bestEffort': False,
                           'maxPixels': 1e13}

            area_stats = lulc_band.reduceRegion(**reduce_args).getInfo()
            if count_pixels:
                area_stats = area_stats[band_name]

            if not count_pixels:
                area_stats = flatten_area_hist(area_stats)

            add_lulc_names = lookup(layer, area_stats, count_pixels)

            return {'result': add_lulc_names}

        except Exception as error:
            logging.error(str(error))
            raise LandcoverError(message='Error in Landcover Analysis')
