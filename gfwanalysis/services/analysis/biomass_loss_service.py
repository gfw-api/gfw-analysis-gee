"""Biomass-Loss SERVICE"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

import ee
from gfwanalysis.errors import BiomassLossError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_thresh_image, get_region, dict_unit_transform, \
     sum_range, dates_selector, squaremeters_to_ha


class BiomassLossService(object):

    @staticmethod
    def analyze(threshold, geojson, begin, end):
        """
        Takes WHRC Carbon and Hansen loss data and returns amount of biomass, carbon and co2 lost
        by time.
        """
        try:
            logging.info(f'[biomass-loss-service]: with properties passed: {threshold}, {begin}, {end}')
            # hansen tree cover loss by year
            d = {}
            # Extract int years to work with for time range
            start_year = int(begin.split('-')[0]) - 2000
            end_year = int(end.split('-')[0]) - 2000

            # Gather assets
            band_name = f'loss_{threshold}'
            hansen_asset = SETTINGS.get('gee').get('assets').get('hansen')
            biomass_asset = SETTINGS.get('gee').get('assets').get('whrc_biomass')
            hansen = ee.Image(hansen_asset).select(band_name)
            biomass = ee.ImageCollection(biomass_asset).max()
            region = get_region(geojson)
            logging.info(f'[biomass-loss-service]: built assets for analysis, using Hansen band {band_name}')

            # Reducer arguments
            reduce_args = {
                'reducer': ee.Reducer.sum().unweighted(),
                'geometry': region,
                'bestEffort': True,
                'scale': 30,
                'tileScale': 16
            }

            # mask hasen data with itself (important step to prevent over-counting)
            hansen = hansen.mask(hansen)

            # Calculate annual biomass loss with a collection operation method
            def reduceFunction(img):
                out = img.reduceRegion(**reduce_args)
                return ee.Feature(None, img.toDictionary().combine(out))

            # Calculate annual biomass loss - add subset images to a collection and then map a reducer to it
            # Calculate stats 10000 ha, 10^6 to transform from Mg (10^6g) to Tg(10^12g) and 255 as is the pixel value
            collectionG = ee.ImageCollection([biomass.multiply(ee.Image.pixelArea().divide(10000)).mask(hansen.updateMask(hansen.eq(year))).set({'year': 2000+year})
                                               for year in range(start_year, end_year + 1)])
            output = collectionG.map(reduceFunction).getInfo()

            # # Convert to carbon and co2 values and add to output dictionary
            biomass_to_carbon = 0.5
            carbon_to_co2 = 3.67

            d['biomassLossByYear'] = {}
            d['cLossByYear'] = {}
            d['co2LossByYear'] = {}
            for row in output.get('features'):
                yr = row.get('properties').get('year')
                d['biomassLossByYear'][yr] = row.get('properties').get('b1')
                d['cLossByYear'][yr] = float(f"{d.get('biomassLossByYear').get(yr) * biomass_to_carbon :3.2f}")
                d['co2LossByYear'][yr] = float(f"{d.get('cLossByYear').get(yr) * carbon_to_co2 :3.2f}")

            # # Calculate total biomass loss
            d['biomassLoss'] = sum([d.get('biomassLossByYear').get(y) for y in d.get('biomassLossByYear')])
            return d

        except Exception as error:
            logging.error(str(error))
            raise BiomassLossError(message='Error in BiomassLoss Analysis')
