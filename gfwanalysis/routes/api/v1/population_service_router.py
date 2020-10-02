"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, Blueprint

from gfwanalysis.errors import PopulationError
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_use, get_geo_by_wdpa, \
    get_geo_by_national, get_geo_by_subnational, get_geo_by_regional
from gfwanalysis.routes.api import error
from gfwanalysis.serializers import serialize_population
from gfwanalysis.services.analysis.population_service import PopulationService
from gfwanalysis.validators import validate_geostore

population_endpoints_v1 = Blueprint('_population', __name__)


def analyze(geojson, area_ha):
    """Analyze Population"""
    logging.info('[ROUTER]: Population Getting Total')
    try:
        data = PopulationService.analyze(geojson=geojson)
    except PopulationError as e:
        logging.error(f'[ROUTER]: {e.message}')
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error(f'[ROUTER]: {str(e)}')
        return error(status=500, detail='Generic Error')
    data['area_ha'] = area_ha
    data['population_density'] = data['population'].get('population_count') / area_ha
    return jsonify(data=serialize_population(data, 'population')), 200


@population_endpoints_v1.route('/', strict_slashes=False, methods=['GET', 'POST'])
@validate_geostore
@get_geo_by_hash
def get_by_geostore(geojson, area_ha):
    """By Geostore Endpoint"""
    logging.info('[ROUTER]: Getting population by geostore')
    return analyze(geojson, area_ha)


@population_endpoints_v1.route('/use/<name>/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_use
def get_by_use(name, id, geojson, area_ha):
    """Use Endpoint"""
    logging.info('[ROUTER]: Getting population by use')
    return analyze(geojson, area_ha)


@population_endpoints_v1.route('/wdpa/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_wdpa
def get_by_wdpa(id, geojson, area_ha):
    """Wdpa Endpoint"""
    logging.info('[ROUTER]: Getting population by wdpa')
    return analyze(geojson, area_ha)


@population_endpoints_v1.route('/admin/<iso>', strict_slashes=False, methods=['GET'])
@get_geo_by_national
def get_by_national(iso, geojson, area_ha):
    """National Endpoint"""
    logging.info('[ROUTER]: Getting population by iso')
    return analyze(geojson, area_ha)


@population_endpoints_v1.route('/admin/<iso>/<id1>', strict_slashes=False, methods=['GET'])
@get_geo_by_subnational
def get_by_subnational(iso, id1, geojson, area_ha):
    """Subnational Endpoint"""
    logging.info('[ROUTER]: Getting population by admin1')
    return analyze(geojson, area_ha)


@population_endpoints_v1.route('/admin/<iso>/<id1>/<id2>', strict_slashes=False, methods=['GET'])
@get_geo_by_regional
def get_by_regional(iso, id1, id2, geojson, area_ha):
    """Subnational Endpoint"""
    logging.info('[ROUTER]: Getting population by admin2 ')
    return analyze(geojson, area_ha)
