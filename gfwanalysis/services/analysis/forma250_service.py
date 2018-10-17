"""FORMA250GFW SERVICE"""

import logging

import ee
from gfwanalysis.errors import FormaError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region, squaremeters_to_ha


class Forma250Service(object):

    @staticmethod
    def analyze(geojson, start_date, end_date):
        """Forma250 microservice class. This service uses the latest image in
        'projects/wri-datalab/FormaGlobalGFW' image collection. The bands of
        that image contain 'alert_delta': the percent of clearing per pixel that occured
        within the last 3 months, 'alert_near_term_delta': the percent of clearing
        which occured within the last 1 month, 'alert_date': the first date when
        the delta passed a threshold of an ecogroup. 'alert_clearing': the %
        clearing in pixel over the past year, and 'alert_accuracy': the error of
        clearing based on historical performance.
        We use the alert_date to identify pixels of alert_delta that correspond
        to a specific date range. Mask out the rest. And then calculate both a
        weighted area in ha (weighted by the fractional percent alert_delta), and also
        a simple count of pixels where clearing occured over a date range.
        """
        try:
            region = get_region(geojson)
            asset_id = SETTINGS.get('gee').get('assets').get('forma250GFW')
            logging.info(asset_id)
            ic=ee.ImageCollection(asset_id).sort('system:time_start', False)
            latest = ee.Image(ic.first())
            alert_date_band = latest.select('alert_date')
            milisec_date_start = ee.Date(start_date).millis()
            milisec_date_end = ee.Date(end_date).millis()
            date_mask = alert_date_band.gte(milisec_date_start).And(
                            alert_date_band.lte(milisec_date_end))
            reduce_sum_args = {'reducer': ee.Reducer.sum().unweighted(),
                               'geometry': region,
                               'bestEffort': True,
                               'scale': 231.65635826395828,
                               'crs': "EPSG:4326",
                               'maxPixels': 9999999999}
            area_m2 = latest.select('alert_delta').mask(date_mask).divide(100).multiply(
                        ee.Image.pixelArea()).reduceRegion(**reduce_sum_args).getInfo()
            alert_area_ha = squaremeters_to_ha(area_m2['alert_delta'])
            tmp_counts = date_mask.gt(0).reduceRegion(**reduce_sum_args).getInfo()
            alert_counts = int(tmp_counts['alert_date'])
            #logging.info(f"Number of alerts over time period = {alert_counts}")
            #logging.info(f"Estimated area loss over time period = {alert_area_ha} ha")
            #
            # Need to pass the area from the geojson object to area_ha, and also add the
            # 'area_ha_loss' key/value into the json that is passed to the front-end.
            return {'area_ha_loss': alert_area_ha, 'alert_counts': alert_counts}
        except Exception as error:
            logging.error(str(error))
            raise FormaError(message='Error in Forma250 Analysis')

    @staticmethod
    def latest():
        """Gets the date of the latest image
        """
        try:
            asset_id = SETTINGS.get('gee').get('assets').get('forma250GFW')
            logging.info(asset_id)
            ic=ee.ImageCollection(asset_id)
            latest_im = ic.toList(ic.size()).get(-1).getInfo()
            latest_date = latest_im['properties']['date']

            logging.info('Retreiving latest date: ')
            logging.info(latest_date)

            return {'latest': latest_date}
        except Exception as error:
            logging.error(str(error))
            raise FormaError(message='Error in Forma250 Analysis')
