"""HISTOGRAM SERVICE"""

import logging

import ee
from gfwanalysis.errors import HistogramError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region
from gfwanalysis.utils.landcover_lookup import lookup


class HistogramService(object):

    @staticmethod
    def analyze(threshold, geojson, begin, end):
        """Take a user specified raster (currently only globcover) and a threshold,
        and return a dictionary of loss pixel count per year and per raster
        type for a given geometry.

        TODO: build this out
        """
        try:
            hansen_asset_id = SETTINGS['gee']['assets']['hansen']
            globcover_asset_id = SETTINGS['gee']['assets']['globcover']
            begin = int(begin.split('-')[0][2:])
            end = int(end.split('-')[0][2:])

            # Grab loss band depending on the threshold of interest
            loss_band_name = 'loss_{0}'.format(threshold)
            loss_band = ee.Image(hansen_asset_id).select(loss_band_name)

            globcover_band = ee.Image(globcover_asset_id).select('landcover')
            masked_globcover = globcover_band.updateMask(loss_band.mask())
            combine_image = loss_band.multiply(500).add(masked_globcover)

            reduce_args = {'reducer': ee.Reducer.frequencyHistogram().unweighted(),
                           'geometry': get_region(geojson),
                           'scale': 27.829872698318393,
                           'bestEffort': False,
                           'maxPixels': 1e10}

            area_stats = combine_image.reduceRegion(**reduce_args).getInfo()[loss_band_name]

            decoded_response = HistogramService.decode_response(begin, end, area_stats)

            add_lulc_names = lookup('globcover', decoded_response)

            return {'histogram': add_lulc_names}

        except Exception as error:
            logging.error(str(error))
            raise HistogramError(message='Error in Histogram Analysis')

    @staticmethod
    def decode_response(begin, end, gee_response):
        requested_years = range(int(begin + 2000), int(end + 2000) + 1)

        globcover_vals = [11, 14, 20, 30, 40, 50, 60, 70, 90, 100, 110, 120,
                          130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230]

        empty_year_dict = {year: 0 for year in requested_years}
        final_dict = {str(val): empty_year_dict.copy() for val in globcover_vals}

        for combine_value, count in gee_response.items():

            if combine_value != 'null':

                # NB with python3 can use // to get the regular integer division
                year = 2000 + int(combine_value) // 500
                globcover = str(int(combine_value) % 500)

                if year in requested_years:
                    final_dict[globcover][year] = count

        return final_dict
