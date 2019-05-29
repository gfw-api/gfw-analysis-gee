"""Router for compositing"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, Blueprint
import json
from gfwanalysis.routes.api import error
from gfwanalysis.services.analysis.composite_service import CompositeService
from gfwanalysis.errors import CompositeError
from gfwanalysis.serializers import serialize_composite_output
from gfwanalysis.middleware import get_geo_by_hash,get_composite_params

composite_service_v1 = Blueprint('composite_service_v1', __name__)

def composite(geojson, instrument, date_range, thumb_size, classify, band_viz, get_dem, get_stats):
    """
    Get a composite satellite image for a geostore id .
    """
    try:
        data = CompositeService.get_composite_image(geojson=geojson, instrument=instrument\
            , date_range=date_range, thumb_size=thumb_size, classify=classify,\
                 band_viz=band_viz, get_stats=get_stats, get_dem=get_dem)
    except CompositeError as e:
        logging.error(f'[ROUTER]: {e.message}')
        return error(status=500, detail=e.message)
    return jsonify(serialize_composite_output(data, 'composite_service')), 200


@composite_service_v1.route('/', strict_slashes=False, methods=['GET'])
@get_geo_by_hash
@get_composite_params
def trigger_compositing(geojson, area_ha, instrument, date_range, thumb_size, classify, band_viz, get_dem, get_stats):
    """Get composite image for given geostore"""
    return composite(geojson, instrument, date_range, thumb_size, classify, band_viz, get_dem, get_stats)
