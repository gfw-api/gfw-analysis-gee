"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, Blueprint
from gfwanalysis.routes.api import error
from gfwanalysis.services.analysis.highres_tiles import HighResTiles
from gfwanalysis.errors import HighResTilesError
from gfwanalysis.serializers import serialize_highres_url
from gfwanalysis.middleware import get_highres_params

highres_tiles_endpoints_v1 = Blueprint('highres_tiles_endpoints_v1', __name__) 

def analyze2(lat, lon, start, end):
    """Generate Sentinel tile url for a requested lat lon point and time prd
    #Example of valid inputs (for area focused on Tenerife)
    lat = -16.589
    lon = 28.246
    start ='2017-03-01'
    end ='2017-03-10'
    """
    logging.info("[ANALYSIS] function initiated")

    try:
        data = HighResTiles.proxy_highres(lat=lat, lon=lon,
                                            start=start, end=end)
    except HighResTilesError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_highres_url(data, 'highres_tiles_url')), 200


@highres_tiles_endpoints_v1.route('/', strict_slashes=False, methods=['GET'])
@get_highres_params
def get_by_geostore(lat, lon, start, end):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting url(s) for tiles for Sentinel')
    return analyze2(lat=lat, lon=lon, start=start, end=end)