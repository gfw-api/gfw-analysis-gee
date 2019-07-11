"""API ROUTER"""

import logging
from flask import jsonify, Blueprint

from gfwanalysis.middleware import get_geo_by_hash
from gfwanalysis.routes.api import error, get_layer, return_pixel_count
from gfwanalysis.serializers import serialize_landcover
from gfwanalysis.services.analysis.landcover_service import LandcoverService
from gfwanalysis.utils.landcover_lookup import get_landcover_types
from gfwanalysis.validators import validate_geostore

landcover_endpoints_v1 = Blueprint('landcover_endpoints_v1', __name__)


def analyze(geojson, area_ha):
    """Analyze landcover"""

    layer = get_layer()
    count_pixels = return_pixel_count()

    if not layer:
        return error(status=400, detail='Layer type must ' \
                                        'be one of {}'.format(', '.join(get_landcover_types())))

    if not geojson:
        return error(status=400, detail='Geojson is required')

    try:
        data = LandcoverService.analyze(geojson=geojson, layer=layer, count_pixels=count_pixels)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')

    data['area_ha'] = area_ha
    logging.info(data)

    return jsonify(data=serialize_landcover(data, layer)), 200


@landcover_endpoints_v1.route('/', strict_slashes=False, methods=['GET', 'POST'])
@validate_geostore
@get_geo_by_hash
def get_by_geostore(geojson, area_ha):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting histogram by world')
    return analyze(geojson, area_ha)
