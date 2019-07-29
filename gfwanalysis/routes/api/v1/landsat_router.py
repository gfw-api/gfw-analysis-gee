"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from flask import jsonify, Blueprint

from gfwanalysis.errors import LandsatTilesError
from gfwanalysis.routes.api import error
from gfwanalysis.serializers import serialize_landsat_url
from gfwanalysis.services.analysis.landsat_tiles_v1 import LandsatTiles
from gfwanalysis.validators import validate_landsat_year

landsat_tiles_endpoints_v1 = Blueprint('landsat_tiles_endpoints_v1', __name__)


def analyze(year):
    """Generate Landsat tile url for a requested YEAR"""
    try:
        data = LandsatTiles.analyze(year=year)
    except LandsatTilesError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_landsat_url(data, 'landsat_tiles_url')), 200


@landsat_tiles_endpoints_v1.route('/<year>', strict_slashes=False, methods=['GET'])
@validate_landsat_year
# def get_by_geostore(year):
def get_tile(year):
    """Get tile Endpoint"""
    logging.info(f"[ROUTER]: Getting url for tiles for year {year}")
    return analyze(year)
