"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request, Blueprint
from gfwanalysis.routes.api import error, set_params
from gfwanalysis.validators import validate_geostore
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_geom
from gfwanalysis.services.analysis.geodescriber import GeodescriberService
from gfwanalysis.errors import GeodescriberError

geodescriber_endpoints_v1 = Blueprint('geodescriber_endpoints_v1', __name__)


def analyze(geojson, area_ha):
    """Call Geodescriber"""
    app = request.args.get('app', 'gfw')
    lang = request.args.get('lang','en')
    gd_result = GeodescriberService.analyze(geojson=geojson,
                                            area_ha=area_ha, app=app, lang=lang)
    logging.info(f'[ROUTER]: result {gd_result}')
    return jsonify(data=gd_result), 200


@geodescriber_endpoints_v1.route('/', strict_slashes=False, methods=['GET'])
@validate_geostore
@get_geo_by_hash
def get_by_geostore(geojson, area_ha):
    """By Geostore Endpoint"""
    logging.info('[ROUTER - geodescriber]: Getting area by geostore')
    return analyze(geojson, area_ha)


@geodescriber_endpoints_v1.route('/geom/', strict_slashes=False, methods=['GET','POST'])
@get_geo_by_geom
def get_by_geom(geojson, area_ha):
    """By Geostore Endpoint"""
    logging.info('[ROUTER - geodescriber]: Getting area by geom')
    return analyze(geojson, area_ha)