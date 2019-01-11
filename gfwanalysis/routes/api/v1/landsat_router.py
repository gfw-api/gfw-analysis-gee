"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, Blueprint, redirect
from gfwanalysis.routes.api import error
from gfwanalysis.services.analysis.landsat_tiles import LandsatTiles
from gfwanalysis.errors import LandsatTilesError
from gfwanalysis.serializers import serialize_landsat_url
from gfwanalysis.middleware import exist_mapid, exist_tile

landsat_tiles_endpoints_v1 = Blueprint('landsat_tiles_endpoints_v1', __name__)


def analyze(year, z, x, y, map_object):
    """Generate Landsat tile url for a requested YEAR"""
    try:
        data = LandsatTiles.analyze(year, z, x, y, map_object)
    except LandsatTilesError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return redirect(data['url'])


@landsat_tiles_endpoints_v1.route('/<year>/<z>/<x>/<y>', strict_slashes=False, methods=['GET'])
@exist_tile
@exist_mapid
def get_tile(year, z, x, y, map_object=None):
    """Get tile Endpoint"""
    logging.info(f"[ROUTER]: Getting url for tiles for year {year}")
    return analyze(year, z, x, y, map_object)
