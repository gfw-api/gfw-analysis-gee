"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, Blueprint

from gfwanalysis.errors import SentinelTilesError
from gfwanalysis.middleware import get_sentinel_params
from gfwanalysis.routes.api import error
from gfwanalysis.serializers import serialize_sentinel_url
from gfwanalysis.services.analysis.sentinel_tiles import SentinelTiles

sentinel_tiles_endpoints_v1 = Blueprint('sentinel_tiles_endpoints_v1', __name__)


def analyze(lat, lon, start, end):
    """Generate Sentinel tile url for a requested lat lon point and time prd
    #Example of valid inputs (for area focused on Tenerife)
    lat = -16.589
    lon = 28.246
    start ='2017-03-01'
    end ='2017-03-10'
    """
    try:
        data = SentinelTiles.proxy_sentinel(lat=lat, lon=lon,
                                            start=start, end=end)
    except SentinelTilesError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_sentinel_url(data, 'sentinel_tiles_url')), 200


@sentinel_tiles_endpoints_v1.route('/', strict_slashes=False, methods=['GET'])
@get_sentinel_params
def get_by_geostore(lat, lon, start, end):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting url for tiles for Sentinel')
    return analyze(lat=lat, lon=lon, start=start, end=end)
