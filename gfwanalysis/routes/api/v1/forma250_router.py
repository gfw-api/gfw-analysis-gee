"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request, Blueprint
from gfwanalysis.routes.api import error, set_params
from gfwanalysis.services.analysis.forma250_service import Forma250Service
from gfwanalysis.validators import validate_geostore
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_use, get_geo_by_wdpa, \
    get_geo_by_national, get_geo_by_subnational
from gfwanalysis.errors import FormaError
from gfwanalysis.serializers import serialize_forma

forma250_endpoints_v1 = Blueprint('forma250_endpoints_v1', __name__)


def analyze(geojson, area_ha):
    """Analyze forma250"""
    logging.info('[ROUTER]: Getting forma')
    if not geojson:
        return error(status=400, detail='Geojson is required')

    threshold, begin, end = set_params()

    try:
        data = Forma250Service.analyze(
            geojson=geojson,
            start_date=begin,
            end_date=end)
    except FormaError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    data['area_ha'] = area_ha
    return jsonify(data=serialize_forma(data, 'forma250gfw')), 200


@forma250_endpoints_v1.route('/', strict_slashes=False, methods=['GET', 'POST'])
@validate_geostore
@get_geo_by_hash
def get_by_geostore(geojson, area_ha):
    """By Geostore Endpoint"""
    logging.info('[ROUTER]: Getting forma by geostore')
    return analyze(geojson, area_ha)


@forma250_endpoints_v1.route('/use/<name>/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_use
def get_by_use(name, id, geojson, area_ha):
    """Use Endpoint"""
    logging.info('[ROUTER]: Getting forma by use')
    return analyze(geojson, area_ha)


@forma250_endpoints_v1.route('/wdpa/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_wdpa
def get_by_wdpa(id, geojson, area_ha):
    """Wdpa Endpoint"""
    logging.info('[ROUTER]: Getting forma by wdpa')
    return analyze(geojson, area_ha)


@forma250_endpoints_v1.route('/admin/<iso>', strict_slashes=False, methods=['GET'])
@get_geo_by_national
def get_by_national(iso, geojson, area_ha):
    logging.info('[ROUTER]: Getting forma by national')
    return analyze(geojson, area_ha)


@forma250_endpoints_v1.route('/admin/<iso>/<id1>', strict_slashes=False, methods=['GET'])
@get_geo_by_subnational
def get_by_subnational(iso, id1, geojson, area_ha):
    logging.info('[ROUTER]: Getting forma by subnational')
    return analyze(geojson, area_ha)
