"""API ROUTER"""

import logging

from flask import jsonify, request, Blueprint
from gfwanalysis.routes.api import error, set_params, get_layer, return_pixel_count
from gfwanalysis.services.analysis.histogram_service import HistogramService
from gfwanalysis.validators import validate_geostore, validate_use
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_use, get_geo_by_wdpa, \
    get_geo_by_national, get_geo_by_subnational
from gfwanalysis.serializers import serialize_histogram
from gfwanalysis.utils.landcover_lookup import get_landcover_types

histogram_endpoints_v1 = Blueprint('histogram_endpoints_v1', __name__)


def analyze(geojson, area_ha):
    """Analyze histogram"""
    if not geojson:
        return error(status=400, detail='Geojson is required')

    threshold, begin, end = set_params()
    layer = get_layer()
    count_pixels = return_pixel_count()

    if not layer:
        logging.debug(get_landcover_types())
        return error(status=400, detail='Layer type must ' \
                    'be one of {}'.format(', '.join(get_landcover_types())))

    try:
        data = HistogramService.analyze(
            geojson=geojson,
            threshold=threshold,
            begin=begin,
            end=end,
            layer=layer,
            count_pixels=count_pixels)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    data['area_ha'] = area_ha

    return jsonify(data=serialize_histogram(data, layer)), 200


@histogram_endpoints_v1.route('/', strict_slashes=False, methods=['GET', 'POST'])
@validate_geostore
@get_geo_by_hash
def get_by_geostore(geojson, area_ha):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting histogram by world')
    return analyze(geojson, area_ha)
