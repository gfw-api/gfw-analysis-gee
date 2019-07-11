"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from flask import jsonify, Blueprint

from gfwanalysis.errors import BiomassLossError
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_use, get_geo_by_wdpa, \
    get_geo_by_national, get_geo_by_subnational, get_geo_by_regional
from gfwanalysis.routes.api import error, set_params
from gfwanalysis.serializers import serialize_biomass_v2, serialize_biomass_table_v2
from gfwanalysis.services.analysis.biomass_loss_service_v2 import BiomassLossService
from gfwanalysis.validators import validate_geostore

biomass_loss_endpoints_v2 = Blueprint('biomass_loss_endpoints_v2', __name__)


def analyze(geojson, area_ha):
    """Analyze BiomassLoss"""
    logging.info('[ROUTER]: Getting biomassloss v2')
    if not geojson:
        return error(status=400, detail='Geojson is required')

    threshold, begin, end, table = set_params()

    try:
        data = BiomassLossService.analyze(
            geojson=geojson,
            threshold=threshold,
            begin=begin,
            end=end)
    except BiomassLossError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')

    data['area_ha'] = area_ha
    if table:
        return jsonify(data=serialize_biomass_table_v2(data, 'biomass-loss')), 200
    else:
        return jsonify(data=serialize_biomass_v2(data, 'biomass-loss')), 200


@biomass_loss_endpoints_v2.route('/', strict_slashes=False, methods=['GET', 'POST'])
@validate_geostore
@get_geo_by_hash
def get_by_geostore(geojson, area_ha):
    """By Geostore Endpoint"""
    logging.info('[ROUTER]: Getting biomassloss by geostore')
    return analyze(geojson, area_ha)


@biomass_loss_endpoints_v2.route('/use/<name>/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_use
def get_by_use(name, id, geojson, area_ha):
    """Use Endpoint"""
    logging.info('[ROUTER]: Getting biomassloss by use')
    return analyze(geojson, area_ha)


@biomass_loss_endpoints_v2.route('/wdpa/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_wdpa
def get_by_wdpa(id, geojson, area_ha):
    """Wdpa Endpoint"""
    logging.info('[ROUTER]: Getting biomassloss by wdpa')
    return analyze(geojson, area_ha)


@biomass_loss_endpoints_v2.route('/admin/<iso>', strict_slashes=False, methods=['GET'])
@get_geo_by_national
def get_by_national(iso, geojson, area_ha):
    """National Endpoint"""
    logging.info('[ROUTER]: Getting biomassloss by iso')
    return analyze(geojson, area_ha)


@biomass_loss_endpoints_v2.route('/admin/<iso>/<id1>', strict_slashes=False, methods=['GET'])
@get_geo_by_subnational
def get_by_subnational(iso, id1, geojson, area_ha):
    """Subnational Endpoint"""
    logging.info('[ROUTER]: Getting biomassloss by admin1')
    logging.info(f'[ROUTER]: admin1 area_ha = {area_ha}')
    return analyze(geojson, area_ha)


@biomass_loss_endpoints_v2.route('/admin/<iso>/<id1>/<id2>', strict_slashes=False, methods=['GET'])
@get_geo_by_regional
def get_by_regional(iso, id1, id2, geojson, area_ha):
    """Subnational Endpoint"""
    logging.info('[ROUTER]: Getting biomassloss by admin2')
    return analyze(geojson, area_ha)
