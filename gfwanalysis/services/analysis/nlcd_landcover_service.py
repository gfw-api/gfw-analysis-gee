"""NLCD-Landcover SERVICE V2"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ee
import logging

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import NLCDLandcoverError
from gfwanalysis.utils.geo import get_region
from gfwanalysis.utils.image_col_reducer import ImageColIntersect
from gfwanalysis.utils.landcover_lookup import lookup, valid_lulc_codes, get_landcover_types

class NLCDLandcover(object):
    @staticmethod
    def analyze(geojson):
        """
        Analyze NLCD Landcover
        """
        try:
            logging.info(f'[nlcd-landcover-service]: Initialize analysis')
            # nlcd land cover
            d = {}
            # Extract int years to work with for time range
            valid_years = [
                {'id':'NLCD2001', 'year': 2001},
                {'id':'NLCD2006', 'year': 2006},
                {'id':'NLCD2011', 'year': 2011},
                {'id':'NLCD2016', 'year': 2016}
          ]

            # Gather assets
            band_name = 'landcover'
            landcover_asset = SETTINGS.get('gee').get('assets').get('us_landcover')
            image_list = [ee.Image(f"{landcover_asset}/{year.get('id')}") for year in valid_years]
            us_landcover = ee.ImageCollection(image_list).select(band_name)
            # region = ee.Feature(geojson).geometry()
            region = get_region(geojson)
            scale = 30
            logging.info(f'[nlcd-landcover-service]: built assets for analysis, using {band_name}')


            # Calculate landcover with a collection operation method
            stats = us_landcover.map(ImageColIntersect(region, scale, ee.Reducer.frequencyHistogram())).getInfo()
            logging.info(f'[nlcd-landcover-service]: retreived {stats}')

            # Format data structure

            data = [{
                'id': d['id'],
                'stats': { k: v * 30 * 30 * 1e-4 for k,v in d['properties'][band_name].items() }
                }
                for d in stats['features']]

            tmp = {}
            for el in data:
                
                year = [y['year'] for y in valid_years if y['id']== el['id']][0] 
                tmp[year] = lookup('nlcd_landcover', el['stats'], False)


            d['nlcd_landcover'] = tmp

            return d

        except Exception as error:
            logging.error(str(error))
            raise NLCDLandcoverError(message='Error in LandCover Analysis')
