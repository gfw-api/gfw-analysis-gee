"""Biomass-Loss SERVICE V1"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ee
import logging

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import BiomassLossError
from gfwanalysis.utils.geo import get_thresh_image, get_region, dict_unit_transform, \
    sum_range, dates_selector


class BiomassLossService(object):

    @staticmethod
    def _gee_hansen(geojson, thresh):
        image = get_thresh_image(str(thresh),
                                 SETTINGS.get('gee').get('assets').get('biomassloss_v1').get('hansen_loss_thresh'))
        region = get_region(geojson)

        # Reducer arguments
        reduce_args = {
            'reducer': ee.Reducer.sum(),
            'geometry': region,
            'bestEffort': True,
            'scale': 90
        }

        # Calculate stats
        area_stats = image.divide(10000 * 255.0) \
            .multiply(ee.Image.pixelArea()) \
            .reduceRegion(**reduce_args)

        return area_stats.getInfo()

    @staticmethod
    def _gee_biomass(geom, thresh):

        image1 = get_thresh_image(str(thresh),
                                  SETTINGS.get('gee').get('assets').get('biomassloss_v1').get('hansen_loss_thresh'))
        image2 = ee.Image(SETTINGS.get('gee').get('assets').get('biomassloss_v1').get('biomass_2000'))
        region = get_region(geom)

        # Reducer arguments
        reduce_args = {
            'reducer': ee.Reducer.sum(),
            'geometry': region,
            'bestEffort': True,
            'scale': 90
        }

        # Calculate stats 10000 ha, 10^6 to transform from Mg (10^6g) to Tg(10^12g) and 255 as is the pixel value when true.
        area_stats = image2.multiply(image1) \
            .divide(10000 * 255.0) \
            .multiply(ee.Image.pixelArea()) \
            .reduceRegion(**reduce_args)

        carbon_stats = image2.multiply(ee.Image.pixelArea().divide(10000)).reduceRegion(**reduce_args)
        area_results = area_stats.combine(carbon_stats).getInfo()

        return area_results

    @staticmethod
    def analyze(threshold, geojson, begin, end):
        """
        """
        try:
            # hansen tree cover loss by year
            logging.info('getting hansen')
            hansen_loss_by_year = BiomassLossService._gee_hansen(geojson, threshold)
            # Biomass loss by year
            logging.info('getting biomass')
            loss_by_year = BiomassLossService._gee_biomass(geojson, threshold)
            # biomass (UMD doesn't permit disaggregation of forest gain by threshold).
            biomass = loss_by_year['carbon']
            loss_by_year.pop("carbon", None)

            # Carbon (UMD doesn't permit disaggregation of forest gain by threshold).
            carbon_loss = dict_unit_transform(loss_by_year, 0.5)

            # CO2 (UMD doesn't permit disaggregation of forest gain by threshold).
            carbon_dioxide_loss = dict_unit_transform(carbon_loss, 3.67)

            # Reduce loss by year for supplied begin and end year
            begin = begin.split('-')[0]
            end = end.split('-')[0]
            biomass_loss = sum_range(loss_by_year, begin, end)

            # Prepare result object
            result = {}
            result['biomass'] = biomass
            result['biomass_loss'] = biomass_loss
            result['biomass_loss_by_year'] = dates_selector(loss_by_year, begin, end)
            result['tree_loss_by_year'] = dates_selector(hansen_loss_by_year, begin, end)
            result['c_loss_by_year'] = dates_selector(carbon_loss, begin, end)
            result['co2_loss_by_year'] = dates_selector(carbon_dioxide_loss, begin, end)

            return result

        except Exception as error:
            logging.error(str(error))
            raise BiomassLossError(message='Error in BiomassLoss Analysis')
