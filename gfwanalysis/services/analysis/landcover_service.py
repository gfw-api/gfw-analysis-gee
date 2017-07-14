"""HISTOGRAM SERVICE"""

import logging

import ee
from gfwanalysis.errors import HistogramError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region
from gfwanalysis.utils.landcover_lookup import lookup


class LandcoverService(object):

    @staticmethod
    def analyze(geojson):
        """Take a user specified raster (currently only globcover)
        and return a dictionary of land cover type and pixel count (or area)
        type for a given geometry.

        TODO: build this out
        """

        try:
            globcover_asset_id = SETTINGS['gee']['assets']['globcover']

            globcover_band = ee.Image(globcover_asset_id).select('landcover')

            reduce_args = {'reducer': ee.Reducer.frequencyHistogram().unweighted(),
                           'geometry': get_region(geojson),
                           'scale': 27.829872698318393,
                           'bestEffort': False,
                           'maxPixels': 1e10}

            area_stats = globcover_band.reduceRegion(**reduce_args).getInfo()['landcover']

            add_lulc_names = lookup('globcover', area_stats)

            return {'landcover': add_lulc_names}

        except Exception as error:
            logging.error(str(error))
            raise HistogramError(message='Error in Landcover Analysis')
