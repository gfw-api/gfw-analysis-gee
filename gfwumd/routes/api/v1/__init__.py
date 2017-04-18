
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from flask import Blueprint, jsonify


# GENERIC Error

def error(status=400, detail='Bad Request'):
    return jsonify({
        'status': status,
        'detail': detail
    }), status

endpoints = Blueprint('endpoints', __name__)
import gfwumd.routes.api.v1.gfw_umd_api_router
