"""WHRC BIOMASS SERVICE"""

import ee
import logging

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import WHRCBiomassError
from gfwanalysis.utils.geo import get_region


class WHRCBiomassService(object):

    @staticmethod
    def analyze(threshold, geojson):
        """For a given Hansen threshold mask on WHRC biomass data
        and geometry return a dictionary of total t/ha.
        """
        try:
            d = {}
            hansen_asset = SETTINGS.get('gee').get('assets').get('hansen')
            biomass_asset = SETTINGS.get('gee').get('assets').get('whrc_biomass')
            region = get_region(geojson)
            reduce_args = {'reducer': ee.Reducer.sum().unweighted(),
                           'geometry': region,
                           'bestEffort': True,
                           'scale': 30}
            tc_mask = ee.Image(hansen_asset).select(['tree_' + str(threshold)], ['tree_cover']).gt(0)
            biomass = ee.ImageCollection(biomass_asset).max().multiply(ee.Image.pixelArea().divide(10000)).mask(tc_mask)
            tree_cover = tc_mask.multiply(ee.Image.pixelArea().divide(10000)).mask(tc_mask)
            # Identify thresholded biomass value
            biomass_value = biomass.reduceRegion(**reduce_args).getInfo()
            tree_cover_value = tree_cover.reduceRegion(**reduce_args).getInfo()
            d['biomass'] = biomass_value.get('b1', 0)
            d['tree_cover'] = tree_cover_value.get('tree_cover', 0)
            return d
        except Exception as error:
            logging.error(str(error))
            raise WHRCBiomassError(message='Error in WHRC Biomass Analysis')
