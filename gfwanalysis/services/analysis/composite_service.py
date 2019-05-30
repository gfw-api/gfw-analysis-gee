import logging
import asyncio
import requests
import functools as funct


import ee
from datetime import datetime, timedelta
from gfwanalysis.errors import CompositeError
from gfwanalysis.config import SETTINGS
from gfwanalysis.services.analysis.classification_service import create_model, add_indices, classify_image, get_classified_image_url

class CompositeService(object):
    """Gets a geostore geometry as input and returns a composite, cloud-free image within the geometry bounds.
    Note that the URLs from Earth Engine expire every 3 days.
    """
    def get_composite_image(geojson, instrument, date_range, thumb_size,\
                        classify, band_viz, get_dem, get_stats):
        #date range inputted as “YYYY-MM-DD, YYYY-MM-DD”
        try:
            features = geojson.get('features')
            region = [ee.Geometry(feature['geometry']) for feature in features][0]
            polyg_geom = [feature['geometry'] for feature in features][0]['coordinates']
            date_range = CompositeService.get_formatted_date(date_range)
            sat_img = CompositeService.get_sat_img(instrument, region, date_range)
            if classify:
                result_dict = CompositeService.get_classified_composite(sat_img, instrument, polyg_geom, thumb_size, get_stats)
            else:
                image = sat_img.visualize(**band_viz)
                result_dict = {'thumb_url':image.getThumbUrl({'region':polyg_geom, 'dimensions':thumb_size}),\
                        'tile_zyx':CompositeService.get_image_url(sat_img)}
            if(get_dem):
                result_dict['dem'] = ee.Image('JAXA/ALOS/AW3D30_V1_1').select('AVE').\
                    clip(region).getThumbUrl({'region':polyg_geom, 'dimensions':thumb_size})
            return result_dict
        except Exception as error:
            logging.error(str(error))
            raise CompositeError(message='Error in composite imaging')

    @staticmethod
    def get_formatted_date(date_range):
        if not date_range:
            date_range = CompositeService.get_last_3months()
        else:
            date_range = date_range.split(',')
        return date_range

    @staticmethod
    def get_last_3months():
        date_weeks_ago = datetime.now() - timedelta(weeks=21)
        date_weeks_ago = date_weeks_ago.strftime("%Y-%m-%d")
        return [date_weeks_ago, datetime.today().strftime('%Y-%m-%d')]

    @staticmethod
    def get_zonal_stats(image):
        #higher tileScale allows inspecting larger areas
        reduce_args = {'reducer':ee.Reducer.frequencyHistogram(),
                        'geometry':image.geometry(),
                        'tileScale':2,
                        'scale':30,
                        'maxPixels':1e13,
                        'bestEffort':True}
        stats = image.reduceRegion(**reduce_args).getInfo()
        return stats

    @staticmethod
    def get_classified_composite(sat_img, instrument, polyg_geom, thumb_size, get_stats):
        model = create_model(instrument)
        indices_image = add_indices(sat_img, instrument)
        classified_image = classify_image(indices_image, model, instrument)
        classif_viz_params = {'min': 0, 'max': 5, 'palette': ['yellow', 'blue', 'grey', 'green', 'orange', 'darkgreen'], 'format':'png'}
        classif_viz_params['region'] = polyg_geom
        classif_viz_params['dimensions'] = thumb_size
        thumb_url = classified_image.getThumbUrl(classif_viz_params)  
        classified_url = get_classified_image_url(classified_image)
        result_dict = {'thumb_url':thumb_url, 'tile_zyx':classified_url}
        if get_stats:
            result_dict['zonal_stats'] = CompositeService.get_zonal_stats(classified_image)
        return result_dict

    @staticmethod
    def get_sat_img(instrument, region, date_range):
        if(instrument == 'landsat'):
            sat_img = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA").filter(ee.Filter.lte('CLOUD_COVER', 3))
        else:
            sat_img = ee.ImageCollection('COPERNICUS/S2').filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 1))
        sat_img = sat_img.filterBounds(region).filterDate(date_range[0].strip(), date_range[1].strip())\
                    .median().clip(region)
        if(instrument == 'sentinel'):
            sat_img = sat_img.divide(100*100)
        return sat_img

    def get_image_url(source):
        """
        Returns a tile url for image
        """
        d = source.getMapId()
        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
        return url
