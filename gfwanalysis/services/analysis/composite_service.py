import logging
import json
import ee
from shapely.geometry import shape, GeometryCollection
from datetime import datetime, timedelta
from gfwanalysis.errors import CompositeError
from gfwanalysis.services.analysis.classification_service import create_model, add_indices, classify_image, get_classified_image_url
from gfwanalysis.utils.geo import buffer_geom

class CompositeService(object):
    """Gets a geostore geometry as input and returns a composite, cloud-free image within the geometry bounds.
    Note that the URLs from Earth Engine expire every 3 days.
    """
    @staticmethod
    def get_composite_image(geojson, instrument, date_range, thumb_size,\
                        classify, band_viz, get_dem, get_stats, show_bounds):
        logging.info(f"[COMPOSITE SERVICE]: Creating composite")
        try:
            features = geojson.get('features')
            region = [ee.Geometry(feature['geometry']) for feature in features][0]
            if show_bounds:
                empty = ee.Image().byte()
                fill = empty.paint(
                    featureCollection=ee.FeatureCollection([region])
                ).visualize(bands=["constant"], palette=["C0FF24"], min=14, opacity=0.1)

                outer = empty.paint(
                    featureCollection=ee.FeatureCollection([region]),
                    color='000000',
                    width=5
                ).visualize(bands=["constant"], palette=["000000"], min=14, opacity=1.0)

                inner = empty.paint(
                    featureCollection=ee.FeatureCollection([region]),
                    color='C0FF24',
                    width=2
                ).visualize(bands=["constant"], palette=["C0FF24"], min=14, opacity=1.0)
                region = buffer_geom(region)
            date_range = CompositeService.get_formatted_date(date_range)
            sat_img = CompositeService.get_sat_img(instrument, region, date_range)
            if classify:
                result_dic = CompositeService.get_classified_composite(sat_img, instrument, region, thumb_size, get_stats)
            else:
                if show_bounds:
                    image = sat_img.visualize(**band_viz).blend(fill).blend(outer).blend(inner)
                else:
                    image = sat_img.visualize(**band_viz)
                tmp_thumb = image.getThumbUrl({'dimensions': thumb_size})
                tmp_tile = CompositeService.get_image_url(image)
                result_dic = {'thumb_url': tmp_thumb,
                               'tile_url': tmp_tile}
                logging.error(f'[Composite Service]: result_dic {result_dic}')
            if get_dem:
                result_dic['dem'] = ee.Image('JAXA/ALOS/AW3D30_V1_1').select('AVE').\
                    clip(region).getThumbUrl({'region':region, 'dimensions':thumb_size,\
                        'min':-479, 'max':8859.0})
            return result_dic
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
        result_dic = {'thumb_url':thumb_url, 'tile_url':classified_url}
        if get_stats:
            result_dic['zonal_stats'] = CompositeService.get_zonal_stats(classified_image)
        return result_dic

    @staticmethod
    def get_sat_img(instrument, region, date_range):
        if(instrument == 'landsat'):
            sat_img = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA").filter(ee.Filter.lte('CLOUD_COVER', 3))
        else:
            sat_img = ee.ImageCollection('COPERNICUS/S2').filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 5))
        sat_img = sat_img.filterBounds(region).filterDate(date_range[0].strip(), date_range[1].strip())\
                    .median().clip(region)
        if(instrument == 'sentinel'):
            sat_img = sat_img.divide(100*100)
        return sat_img

    @staticmethod
    def get_image_url(source):
        """
        Returns a tile url for image
        """
        d = source.getMapId()
        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
        return url
