"""Soil Carbon SERVICE"""

import logging
import ee
from gfwanalysis.errors import soilCarbonError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region, squaremeters_to_ha


class SoilCarbonService(object):

    @staticmethod
    def analyze(threshold, geojson):
        """For a given Hansen threshold mask on WHRC biomass data
        and geometry return a dictionary of total t/ha.
        """
        #logging.info('[Soil Carbon Service]: In Soil carbon service')
        try:
            d = {}
            hansen_asset = SETTINGS.get('gee').get('assets').get('hansen')
            soil_carbon_asset = SETTINGS.get('gee').get('assets').get('soils_30m')
            region = get_region(geojson)
            reduce_args = {'reducer': ee.Reducer.sum().unweighted(),
                           'geometry': region,
                           'bestEffort': True,
                           'scale': 30}
            tc_mask = ee.Image(hansen_asset).select('tree_'+ str(threshold)).gt(0)
            sc = ee.Image(soil_carbon_asset).multiply(ee.Image.pixelArea().divide(10000)).mask(tc_mask)
            # Identify soil carbon value
            sc_value = sc.reduceRegion(**reduce_args).getInfo()
            d['total_soil_carbon'] = sc_value
            #logging.info(f'[Soil Carbon Service]:d = {d}')
            return d
        except Exception as error:
            logging.error(str(error))
            raise soilCarbonError(message='Error in soil carbon analysis')