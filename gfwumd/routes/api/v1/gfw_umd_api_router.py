"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import datetime

from flask import jsonify, request
from CTRegisterMicroserviceFlask import request_to_microservice
from gfwumd.routes.api.v1 import endpoints, error
from gfwumd.services import UmdService
from gfwumd.validators import validate_world, validate_use
from gfwumd.errors import HansenError, CartoError
from gfwumd.serializers import serialize_analysis


def set_params():
    """-"""
    threshold = request.args.get('thresh', 30)
    begin = request.args.get('begin', '2001-01-01')
    end = request.args.get('end', '2013-01-01')
    period = request.args.get('period', None)
    if period and len(period.split(',')) > 1:
        first = period.split(',')[0]
        second = period.split(',')[1]
        try:
            if len(first.split('-')) > 2 and len(second.split('-')) > 2:
                datetime.datetime(year=first.split('-')[0], month=first.split('-')[1], day=first.split('-')[2])
                datetime.datetime(year=second.split('-')[0], month=second.split('-')[1], day=second.split('-')[2])
                begin = first
                end = second
            else:
                pass
        except Exception:
            pass
    else:
        pass
    return threshold, begin, end


@endpoints.route('/world', strict_slashes=False, methods=['GET', 'POST'])
@validate_world
def get_world():
    """World Endpoint"""
    logging.info('[ROUTER]: Getting world')
    geostore = request.args.get('geostore', None)
    if geostore:
        config = {
            'uri': '/geostore/'+geostore,
            'method': 'GET'
        }
        response = request_to_microservice(config)
        if not response or response.get('errors'):
            return error(status=404, detail='Geostore not found')
        geostore = response.get('data', None).get('attributes', None)
        geojson = geostore.get('geojson', None)
    else:
        geojson = request.get_json().get('geojson')

    if not geojson:
        return error(status=400, detail='Geostore is required')

    area_ha = geostore.get('areaHa', None)
    threshold, begin, end = set_params()

    try:
        data = UmdService.get_world(
            geojson=geojson,
            threshold=threshold,
            begin=begin,
            end=end)
    except HansenError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    data['area_ha'] = area_ha
    return jsonify(data=[serialize_analysis(data, 'world')]), 200


@endpoints.route('/use/<name>/<id>', strict_slashes=False, methods=['GET'])
@validate_use
def get_use(name, id):
    """Use Endpoint"""
    threshold, begin, end = set_params()

    try:
        data = UmdService.get_use(
            name=name,
            id=id,
            threshold=threshold,
            begin=begin,
            end=end)
    except HansenError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except CartoError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    return jsonify(data=[serialize_analysis(data, 'use')]), 200


@endpoints.route('/wdpa/<id>', strict_slashes=False, methods=['GET'])
def get_wdpa(id):
    """Use Endpoint"""
    threshold, begin, end = set_params()

    try:
        data = UmdService.get_wdpa(
            id=id,
            threshold=threshold,
            begin=begin,
            end=end)
    except HansenError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except CartoError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    return jsonify(data=[serialize_analysis(data, 'wdpa')]), 200
