"""HISTOGRAM SERVICE"""

import logging

import ee

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import HistogramError
from gfwanalysis.utils.geo import get_region
from gfwanalysis.utils.landcover_lookup import lookup, valid_lulc_codes
from gfwanalysis.utils.parse_gee_response import flatten_area_hist


class HistogramService(object):

    @staticmethod
    def analyze(threshold, geojson, begin, end, layer, count_pixels):
        """Take a user specified raster (currently only globcover) and a threshold,
        and return a dictionary of loss pixel count per year and per raster
        type for a given geometry.

        TODO: build this out
        """
        try:
            hansen_asset_id = SETTINGS['gee']['assets']['hansen']
            lulc_asset_id = SETTINGS['gee']['assets'][layer]
            begin = int(begin.split('-')[0][2:])
            end = int(end.split('-')[0][2:])

            # Grab loss band depending on the threshold of interest
            loss_band_name = 'loss_{0}'.format(threshold)
            loss_band = ee.Image(hansen_asset_id).select(loss_band_name)

            lulc_asset_id = SETTINGS['gee']['assets'][layer]
            band_name = SETTINGS['gee']['lulc_band'].get(layer, 'b1')

            lulc_band = ee.Image(lulc_asset_id).select(band_name)
            masked_lulc = lulc_band.updateMask(loss_band.mask())
            combine_image = loss_band.multiply(500).add(masked_lulc)

            if count_pixels:
                reducer = ee.Reducer.frequencyHistogram().unweighted()

            else:
                reducer = ee.Reducer.frequencyHistogram().unweighted().group()
                combine_image = combine_image.addBands([ee.Image.pixelArea()])

            reduce_args = {'reducer': reducer,
                           'geometry': get_region(geojson),
                           'scale': 27.829872698318393,
                           'bestEffort': False,
                           'maxPixels': 1e10}

            area_stats = combine_image.reduceRegion(**reduce_args).getInfo()

            if count_pixels:
                area_stats = area_stats[loss_band_name]

            else:
                area_stats = flatten_area_hist(area_stats)

            decoded_response = HistogramService.decode_response(begin, end, area_stats, layer)

            add_lulc_names = lookup(layer, decoded_response, count_pixels)

            return {'result': add_lulc_names}

        except Exception as error:
            logging.error(str(error))
            raise HistogramError(message='Error in Histogram Analysis')

    @staticmethod
    def decode_response(begin, end, gee_response, layer):
        requested_years = range(int(begin + 2000), int(end + 2000) + 1)

        lulc_vals = valid_lulc_codes(layer)

        empty_year_dict = {year: 0 for year in requested_years}
        final_dict = {str(val): empty_year_dict.copy() for val in lulc_vals}

        for combine_value, count in gee_response.items():

            if combine_value != 'null':

                # NB with python3 can use // to get the regular integer division
                year = 2000 + int(combine_value) // 500
                lulc = str(int(combine_value) % 500)

                if year in requested_years:
                    final_dict[lulc][year] = count

        return final_dict
