"""EE SENTINEL TILE URL SERVICE"""

import logging
import asyncio
import requests
import functools as funct

import ee
from gfwanalysis.errors import CompositeError
from gfwanalysis.config import SETTINGS

class CompositeService(object):
    """Gets a geostore geometry as input and returns a composite, cloud-free image within the geometry bounds.
    Note that the URLs from Earth Engine expire every 3 days.
    """
    visParamsTOA = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.4}
    def get_formatted_date(date_range):
        if (date_range == ""):
            date_range = get_last_3months()
        else:                           
            date_range = date_range.split(',')
        return date_range

    def get_last_3months():
        date_weeks_ago = datetime.now() - timedelta(weeks=21)
        date_weeks_ago = date_weeks_ago.strftime("%Y-%m-%d")
        return [date_weeks_ago, datetime.today().strftime('%Y-%m-%d')]

    def get_zonal_stats(image, classified=False):
        if(not classified):   #image classification functionality not implemented yet
            pass
        else:
            pass
        #higher tileScale allows inspecting larger areas
        reduce_args = {'reducer':ee.Reducer.histogram(),\
        'geometry':image.geometry(), 'tileScale':2,
        'scale':30, 'maxPixels':1e13, 'bestEffort':True}
        stats = image.reduceRegion(**reduce_args)
        return stats
    def get_composite_image(geostore_id, instrument='landsat', date_range="", thumb_size=[500,500],\
                            band_viz=visParamsTOA, classify=False, get_dem=False):
        #date range inputted as “YYYY-MM-DD, YYYY-MM-DD”
        try:
            geostore_polyg = LMIPy.Geometry(id_hash=geostore_id)
            region = get_region(geostore_polyg.attributes.get('geojson'))[0]
            date_range = get_formatted_date(date_range)
            if(instrument == 'landsat'):
                sat_img = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA").filter(ee.Filter.lte('CLOUD_COVER', 3))
            elif(instrument == 'sentinel'):
                sat_img = ee.ImageCollection('COPERNICUS/S2').filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 1))
            sat_img = sat_img.filterBounds(region).filterDate(date_range[0].strip(), date_range[1].strip())\
                        .median().clip(region)
            if(instrument == 'sentinel'):
                sat_img = sat_img.divide(100*100)
            region_bounds = region.bounds().getInfo()['coordinates']
            image = sat_img.visualize(**band_viz)
            thumb_url = url = image.getThumbUrl({
                'region':region_bounds, 'dimensions':thumb_size})
            zonal_stats = get_zonal_stats(sat_img, classify)
            if(get_dem):
                dem = ee.Image('JAXA/ALOS/AW3D30_V1_1').select('AVE').clip(region)
                dem_thumb_url = dem.getThumbUrl({'region':region_bounds, 'dimensions':thumb_size})
                return {'thumb_url':thumb_url, 'tile_zyx':get_image_url(sat_img), 'dem':dem_thumb_url,\
                    'zonal_stats':zonal_stats}                                      
            else:
                return {'thumb_url':thumb_url, 'tile_zyx':get_image_url(sat_img), 'zonal_stats':zonal_stats}   
        except Exception as error:
            logging.error(str(error))
            raise CompositeError(message='Error in composite imaging')

    def get_image_url(source):  
        """
        Returns a tile url for image
        """
        #image = ee.Image(source)
        d = source.getMapId()#.select("B4","B3","B2").getMapId()
        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
        return url
    def get_region(geom):
        """Take a valid geojson object, iterate over all features in that object.
            Build up a list of EE Polygons, and finally return an EE Feature
            collection. New as of 19th Sep 2017 (needed to fix a bug where the old
            function ignored multipolys)
        """
        polygons = []
        for feature in geom.get('features'):
            shape_type = feature.get('geometry').get('type')
            coordinates = feature.get('geometry').get('coordinates')
            if shape_type == 'MultiPolygon':
                polygons.append(ee.Geometry.MultiPolygon(coordinates))
            elif shape_type == 'Polygon':
                polygons.append(ee.Geometry.Polygon(coordinates))
            else:
                pass
        return polygons
