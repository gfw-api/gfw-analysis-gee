"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request, Blueprint
from gfwanalysis.routes.api import error, get_layer
from gfwanalysis.services.analysis.landcover_service import LandcoverService
from gfwanalysis.validators import validate_geostore, validate_use
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_use, get_geo_by_wdpa, \
    get_geo_by_national, get_geo_by_subnational
from gfwanalysis.errors import HansenError
from gfwanalysis.serializers import serialize_landcover

landcover_endpoints_v1 = Blueprint('landcover_endpoints_v1', __name__)


def analyze(geojson, area_ha):
    """Analyze landcover"""

    layer = get_layer()

    if not geojson:
        return error(status=400, detail='Geojson is required')

    try:
        data = LandcoverService.analyze(geojson=geojson, layer=layer)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
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
