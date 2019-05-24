"""Router for classifications"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, Blueprint
from gfwanalysis.routes.api import error
from gfwanalysis.services.analysis.composite_service import CompositeService
from gfwanalysis.errors import CompositeError
from gfwanalysis.serializers import serialize_composite_output
from gfwanalysis.middleware import get_classification_params

composite_service_v1 = Blueprint('composite_service_v1', __name__) 

def composite(geostore_id):
    """
    Get a composite satellite image for a geostore id.
    """
    try:
        data = CompositeService.get_composite_image(geostore_id=geostore_id)
    except CompositeError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    return jsonify(data=serialize_composite_output(data, 'composite_service')), 200


@composite_service_v1.route('/', strict_slashes=False, methods=['GET'])
@get_classification_params
def trigger_compositing(geostore_id):
    """Get composite image for given geostore"""
    logging.info('geostore_id: ' + geostore_id)
    return composite(geostore_id=geostore_id)
