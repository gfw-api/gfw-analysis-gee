"""Api Router"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import logging

import requests

from flask import jsonify, request
from CTRegisterMicroserviceFlask import request_to_microservice
from gfwumd.routes.api.v1 import endpoints, error
from gfwumd.services import UmdService
from gfwumd.validators import validate_world, validate_use
from gfwumd.errors import HansenError


def set_params():
    thresh = request.args.get('thresh', 30)
    if request.args.get('period'):
        begin = period.split(',')[0]
        end = period.split(',')[1]
    else:
        begin = request.args.get('begin', '2001-01-01')
        end = request.args.get('end', '2013-01-01')
    return thresh, begin, end


@endpoints.route('/', methods=['GET'])
@validate_world
def get_world():
    """World Endpoint"""
    logging.info('[ROUTER]: Getting world')
    geostore = request.args.get('geostore')

    config = {
        'uri': '/geostore/'+geostore,
        'method': 'GET'
    }
    response = request_to_microservice(config)
    if not response:
        return error(status=404, detail='Geostore not found')
    geostore = response.get('data', None).get('attributes', None)

    geojson = geostore.get('geojson', None)
    thresh, begin, end = set_params()

    # Calling UMD
    try:
        data = UmdService.get_world(
            geojson=geojson,
            thresh=thresh,
            begin=begin,
            end=end)
    except HansenError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    return jsonify(data=data), 200


@endpoints.route('/use/<name>/<id>', methods=['GET'])
@validate_use
def get_use(name, id):
    """Use Endpoint"""
    useTable = use_validator(name)
    if useTable == False:
        data, status = generate_response(status=400, error_message='use table not valid')
        return jsonify(data), status

    # Defining args
    args = get_args_from_request(request)
    args['use'] = useTable
    args['useid'] = id

    # Calling UMD
    data, error = umdservice.execute(args, 'use')
    if error == 404:
        data, status = generate_response(status=404, error_message='use not found - '+data['error'][0])
        return jsonify(data), status
    elif error == 500:
        data, status = generate_response(status=500, error_message='ee bad response - '+str(data['error']))
        return jsonify(data), status

    data, status = generate_response(status=200, data=data, umd_type='use')
    return jsonify(data), status


@endpoints.route('/umd-loss-gain/wdpa/<id>', methods=['GET'])
def get_wdpa(id):
    """Wdpa Endpoint Controller
    id -- wdpa id
    """
    # Defining args
    args = get_args_from_request(request)
    args['wdpaid'] = id

    # Calling UMD
    data, error = umdservice.execute(args, 'wdpa')
    if error == 404:
        data, status = generate_response(status=404, error_message='wdpa '+ id +' not found')
        return jsonify(data), status
    elif error == 500:
        data, status = generate_response(status=500, error_message='ee bad response - '+str(data['error']))
        return jsonify(data), status

    data, status = generate_response(status=200, data=data, umd_type='wdpa')
    return jsonify(data), status
