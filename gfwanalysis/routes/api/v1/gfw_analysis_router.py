"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import datetime

from flask import jsonify, request
from CTRegisterMicroserviceFlask import request_to_microservice
from gfwanalysis.routes.api.v1 import endpoints, error
from gfwanalysis.services import AnalysisService
from gfwanalysis.validators import validate_world, validate_use, validate_forma
from gfwanalysis.errors import HansenError, CartoError, FormaError
from gfwanalysis.serializers import serialize_umd, serialize_forma


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
                datetime.datetime(year=int(first.split('-')[0]), month=int(first.split('-')[1]), day=int(first.split('-')[2]))
                datetime.datetime(year=int(second.split('-')[0]), month=int(second.split('-')[1]), day=int(second.split('-')[2]))
                begin = first
                end = second
            else:
                pass
        except Exception:
            pass
    else:
        pass
    return threshold, begin, end


@endpoints.route('/umd-loss-gain', strict_slashes=False, methods=['GET', 'POST'])
@validate_world
def get_world():
    """World Endpoint"""
    logging.info('[ROUTER]: Getting world')
    geostore = None
    if request.args and 'geostore' in request.args:
        geostore = request.args.get('geostore', None)
        config = {
            'uri': '/geostore/'+geostore,
            'method': 'GET'
        }
        response = request_to_microservice(config)
        if not response or response.get('errors'):
            return error(status=404, detail='Geostore not found')
        geostore = response.get('data', None).get('attributes', None)
        geojson = geostore.get('geojson', None)
        area_ha = geostore.get('areaHa', None)
    else:
        geojson = request.get_json().get('geojson')
        area_ha = None

    if not geojson:
        return error(status=400, detail='Geostore is required')

    threshold, begin, end = set_params()

    try:
        data = AnalysisService.get_umd_world(
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
    return jsonify(data=serialize_umd(data, 'umd')), 200


@endpoints.route('/umd-loss-gain/use/<name>/<id>', strict_slashes=False, methods=['GET'])
@validate_use
def get_use(name, id):
    """Use Endpoint"""
    threshold, begin, end = set_params()

    try:
        data = AnalysisService.get_umd_use(
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

    return jsonify(data=serialize_umd(data, 'umd')), 200


@endpoints.route('/umd-loss-gain/wdpa/<id>', strict_slashes=False, methods=['GET'])
def get_wdpa(id):
    """Use Endpoint"""
    threshold, begin, end = set_params()

    try:
        data = AnalysisService.get_umd_wdpa(
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

    return jsonify(data=serialize_umd(data, 'umd')), 200


@endpoints.route('/forma250gfw', strict_slashes=False, methods=['GET'])
@validate_forma
def get_forma():
    """World Endpoint"""
    logging.info('[ROUTER]: Getting forma')
    geostore = request.args.get('geostore', None)
    config = {
        'uri': '/geostore/'+geostore,
        'method': 'GET'
    }
    response = request_to_microservice(config)
    if not response or response.get('errors'):
        return error(status=404, detail='Geostore not found')
    geostore = response.get('data', None).get('attributes', None)
    geojson = geostore.get('geojson', None)
    geoarea = geostore.get('areaHa')
    threshold, begin, end = set_params()
    try:
        data = AnalysisService.get_forma(
            geojson=geojson,
            begin=begin,
            end=end)
        data['area_ha'] = geoarea
    except FormaError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_forma(data, 'forma250gfw')), 200


@endpoints.route('/forma250gfw/use/<name>/<id>', strict_slashes=False, methods=['GET'])
@validate_use
def get_use_forma(name, id):
    """Use Endpoint"""
    threshold, begin, end = set_params()

    try:
        data = AnalysisService.get_forma_use(
            name=name,
            id=id,
            begin=begin,
            end=end)
    except FormaError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except CartoError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    return jsonify(data=serialize_forma(data, 'forma')), 200


@endpoints.route('/forma250gfw/wdpa/<id>', strict_slashes=False, methods=['GET'])
def get_forma_wdpa(id):
    """WDPA Forma Endpoint"""
    threshold, begin, end = set_params()

    try:
        data = AnalysisService.get_forma_wdpa(
            id=id,
            begin=begin,
            end=end)
    except FormaError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except CartoError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    return jsonify(data=serialize_forma(data, 'forma250gfw')), 200


@endpoints.route('/forma250gfw/admin/<iso>', strict_slashes=False, methods=['GET'])
def get_forma_iso(iso):
    """Forma250 with ISO code Endpoint"""
    logging.info('[ROUTER]: Getting forma250/iso')
    config = {
        'uri': '/geostore/admin/'+iso,
        'method': 'GET'
    }
    response = request_to_microservice(config)
    if not response or response.get('errors'):
        return error(status=404, detail='Geostore not found')
    geostore = response.get('data', None).get('attributes', None)
    geojson = geostore.get('geojson', None)
    geoarea = geostore.get('areaHa')
    threshold, begin, end = set_params()
    try:
        data = AnalysisService.get_forma(
            geojson=geojson,
            begin=begin,
            end=end)
        data['area_ha'] = geoarea
    except FormaError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_forma(data, 'forma250gfw')), 200


@endpoints.route('/forma250gfw/admin/<iso>/<admin>', strict_slashes=False, methods=['GET'])
def get_forma_iso_admin(iso, admin):
    """Forma250 with ISO/Admin (sub-nation) code Endpoint"""
    logging.info('[ROUTER]: Getting forma250/iso')
    config = {
        'uri': ''.join(['/geostore/admin/', str(iso), '/', str(admin)]),
        'method': 'GET'
    }
    response = request_to_microservice(config)
    if not response or response.get('errors'):
        return error(status=404, detail='Geostore not found')
    geostore = response.get('data', None).get('attributes', None)
    geojson = geostore.get('geojson', None)
    geoarea = geostore.get('areaHa')
    threshold, begin, end = set_params()
    try:
        data = AnalysisService.get_forma(
            geojson=geojson,
            begin=begin,
            end=end)
        data['area_ha'] = geoarea
    except FormaError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_forma(data, 'forma250gfw')), 200
