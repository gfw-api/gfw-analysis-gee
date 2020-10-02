"""MANGROVE BIOMASS SERVICE"""

import logging

import ee

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import MangroveBiomassError
from gfwanalysis.utils.geo import get_region


class MangroveBiomassService(object):

    @staticmethod
    def analyze(geojson):
        """For a given geometry and mangrove biomass data
        return a dictionary of total t/ha.
        """
        try:
            d = {}
            biomass_asset = SETTINGS.get('gee').get('assets').get('mangrove_biomass')
            region = get_region(geojson)
            reduce_args = {'reducer': ee.Reducer.sum().unweighted(),
                           'geometry': region,
                           'bestEffort': True,
                           'scale': 30}
            biomass = ee.Image(biomass_asset).multiply(ee.Image.pixelArea().divide(10000))
            # Identify thresholded biomass value
            biomass_value = biomass.reduceRegion(**reduce_args).getInfo()
            d['biomass'] = biomass_value
            return d
        except Exception as error:
            logging.error(str(error))
            raise MangroveBiomassError(message='Error in Mangrove Biomass Analysis')
