import logging
import json
import ee
from shapely.geometry import shape, GeometryCollection
from datetime import datetime, timedelta
from gfwanalysis.errors import CompositeError
from gfwanalysis.services.analysis.classification_service import create_model, add_indices, classify_image, get_classified_image_url
from gfwanalysis.utils.geo import buffer_geom, get_clip_vertex_list

class CompositeService(object):
    """Gets a geostore geometry as input and returns a composite, cloud-free image within the geometry bounds.
    Note that the URLs from Earth Engine expire every 3 days.
    """
    @staticmethod
    def get_composite_image(geojson, instrument, date_range, thumb_size,\
                        classify, band_viz, get_dem, get_stats, cloudscore_thresh): ## removes the stats, the classify, the show_bounds and adds bbx and get files
        logging.info(f"[COMPOSITE SERVICE]: Creating composite")
        result_dic = {}
        try:
            features = geojson.get('features')
            region = [ee.Geometry(feature['geometry']) for feature in features][0]
            clip_region = ee.Geometry({'type': 'Polygon',
                                       'coordinates': [get_clip_vertex_list(geojson)]
                                   })
            clip_bbox = clip_region.bounds()
            geom_list = geojson.get('features')[0].get('geometry').get('coordinates')
            logging.info(f"[service GEOM 🤪 {geom_list }")
            if not date_range:
                dates = CompositeService.get_last_3months()
            else:
                dates = date_range[1:-1].split(',')
            if instrument.lower() == 'landsat':
                sat_img = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA").filter(ee.Filter.lte('CLOUD_COVER', cloudscore_thresh))
                sat_img = sat_img.filterDate(dates[0].strip(), dates[1].strip()).median()
            elif instrument.lower() == 'sentinel':
                sat_img = ee.ImageCollection('COPERNICUS/S2').filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloudscore_thresh))
                sat_img = sat_img.filterBounds(region).filterDate(dates[0].strip(), dates[1].strip()).median()
                sat_img = sat_img.divide(100*100)
            if classify:
                result_dic = CompositeService.get_classified_composite(sat_img, instrument, geom_list, thumb_size, get_stats)
            else:
                image = sat_img.clip(clip_region).visualize(**band_viz)
                result_dic['thumb_url'] = image.getThumbUrl({'dimensions': thumb_size, 'region': geom_list})
                result_dic['tile_url'] = CompositeService.get_image_url(image)
            if get_dem:
                dem_img = ee.Image('JAXA/ALOS/AW3D30_V1_1').select('AVE').clip(clip_region)
                dem_url = dem_img.getThumbUrl({'dimensions':thumb_size, 'min':-479, 'max':8859.0, 'region': geom_list})
                result_dic['dem'] = dem_url
            return result_dic
        except Exception as error:
            logging.error(str(error))
            raise CompositeError(message=f'Error in composite imaging {error}')
        


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
    def get_sat_img(instrument, region, date_range, cloudscore_thresh):
        if(instrument == 'landsat'):
            sat_img = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA").filter(ee.Filter.lte('CLOUD_COVER', cloudscore_thresh))
        else:
            sat_img = ee.ImageCollection('COPERNICUS/S2').filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloudscore_thresh))
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
