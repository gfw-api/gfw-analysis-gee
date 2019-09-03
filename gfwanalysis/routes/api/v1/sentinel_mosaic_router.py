"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from flask import jsonify, Blueprint

from gfwanalysis.errors import SentinelMosaicError
from gfwanalysis.middleware import get_geo_by_hash, get_sentinel_mosaic_params
from gfwanalysis.routes.api import error
from gfwanalysis.serializers import serialize_sentinel_mosaic
from gfwanalysis.services.analysis.sentinel_mosaic import SentinelMosaic

sentinel_mosaic_endpoints_v1 = Blueprint('sentinel_mosaic_endpoints_v1', __name__)


def analyze_sentinel_mosaic(geojson, start, end, cloudscore_thresh, bounds):
    """
    ...
    """
    logging.info("[SENTIINEL MOSAIC>ROUTER] function initiated")
    try:
        data = SentinelMosaic.sentinel_mosaic_data(geojson=geojson, start=start, end=end, cloudscore_thresh=cloudscore_thresh, bounds=bounds)
    except SentinelMosaicError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_sentinel_mosaic(data, 'sentinel_mosaic')), 200


@sentinel_mosaic_endpoints_v1.route('/', strict_slashes=False, methods=['GET'])
@get_geo_by_hash
@get_sentinel_mosaic_params
def get_by_geostore(geojson, start, end, cloudscore_thresh, bounds):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting mosaic for tiles for Sentinel Images')
    data = analyze_sentinel_mosaic(geojson=geojson, start=start, end=end, cloudscore_thresh=cloudscore_thresh, bounds=bounds)
    return data


