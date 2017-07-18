"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request, Blueprint
from gfwanalysis.routes.api import error, set_params, get_layer
from gfwanalysis.services.analysis.histogram_service import HistogramService
from gfwanalysis.validators import validate_geostore, validate_use
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_use, get_geo_by_wdpa, \
    get_geo_by_national, get_geo_by_subnational
from gfwanalysis.errors import HansenError
from gfwanalysis.serializers import serialize_histogram

histogram_endpoints_v1 = Blueprint('histogram_endpoints_v1', __name__)


def analyze(geojson, area_ha):
    """Analyze histogram"""
    if not geojson:
        return error(status=400, detail='Geojson is required')

    threshold, begin, end = set_params()
    layer = get_layer()

    try:
        data = HistogramService.analyze(
            geojson=geojson,
            threshold=threshold,
            begin=begin,
            end=end,
            layer=layer)
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
