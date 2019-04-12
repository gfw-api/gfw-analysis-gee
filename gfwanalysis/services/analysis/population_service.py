"""POPULATION SERVICE"""

import logging

import ee
from gfwanalysis.errors import PopulationError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region, squaremeters_to_ha, admin_0_simplify


class PopulationService(object):

    @staticmethod
    def analyze(geojson):
        """For a given geometry and population density data
        return a dictionary of total t/ha.
        """
        try:
            d = {}
            # The number of people per cell
            population_asset = SETTINGS.get('gee').get('assets').get('population')
            region = get_region(geojson)
            reduce_args = {'reducer': ee.Reducer.sum().unweighted(),
                           'geometry': region,
                           'bestEffort': True,
                           'scale': 30}
            # Convert m2 to ha
            scale_factor = ee.Number(1e4)               
            # The number of persons per cell
            population = ee.Image(population_asset)
            #.multiply(ee.Image.pixelArea().divide(scale_factor))
            # Total population value within region
            population_value = population.reduceRegion(**reduce_args).getInfo()
            d['population'] = population_value
            return d
        except Exception as error:
            logging.error(str(error))
            raise PopulationError(message='Error in Population Analysis')