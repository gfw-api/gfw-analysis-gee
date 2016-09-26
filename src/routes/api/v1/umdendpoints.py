import os
import requests
from flask import request, jsonify, Blueprint
from serializers import errorserializer, umdserializer
from validators.umdvalidator import world_validator, use_validator
from services import umdservice
from utils.helpers import get_args_from_request, request_is_error

# Creating endpoints blueprint
umd_endpoints = Blueprint('umd_endpoints', __name__,)

# Serializers Interface
def generate_response(status, data={}, umd_type=None, error_message=None):
  if request_is_error(status):
    data = errorserializer.serialize(status, error_message=error_message)
  else:
    data = umdserializer.serialize(data, umd_type=umd_type)
  return data, status


@umd_endpoints.route('/umd-loss-gain', methods=['GET'])
def get_world():
  """World Endpoint Controller"""
  # Negative check
  if world_validator(request) == False:
    data, status = generate_response(status=400,
                                     error_message="geostore not provided")
    return jsonify(data), status

  geostore = request.args.get('geostore')
  # Getting geoJson from Api Gateway if it exists
  url = os.environ['GATEWAY_URL']+'/geostore/'+geostore
  r = requests.get(url)
  if r.status_code != 200:
    data, status = generate_response(status=r.status_code,
                             error_message="geostore not found")
    return jsonify(data), status

  # Defining args
  args = get_args_from_request(request)
  args['geojson'] = r.json()['data']['attributes']['geojson']
  args['areaHa'] = r.json()['data']['attributes']['areaHa']

  # Calling UMD
  data, error = umdservice.execute(args, 'world')
  if error != None:
    pass # do something managing the error

  #@TODO sometimes use is not valid Check for error
  #gotta change umdservice when ee returns an error
  data, status = generate_response(status=200, data=data, umd_type='world')
  return jsonify(data), status


@umd_endpoints.route('/umd-loss-gain/use/<name>/<id>', methods=['GET'])
def get_use(name, id):
  """Use Endpoint Controller
  name -- resource name
  id -- use id
  """
  # Negative Check
  useTable = use_validator(name)
  if useTable == False:
    data, status = generate_response(status=400,
                             error_message='use table not valid')
    return jsonify(data), status

  # Defining args
  args = get_args_from_request(request)
  args['use'] = useTable
  args['useid'] = id

  # Calling UMD
  data, error = umdservice.execute(args, 'use')
  if error == 404:
    print data['error'][0]
    data, status = generate_response(status=404,
                 error_message='use not found - '+data['error'][0])
    return jsonify(data), status
  elif error == 500:
    data, status = generate_response(status=500,
                             error_message='ee bad response')
    return jsonify(data), status

  #@TODO sometimes use is not valid Check for error
  #gotta change umdservice when ee returns an error
  data, status = generate_response(status=200, data=data, umd_type='use')
  return jsonify(data), status


@umd_endpoints.route('/umd-loss-gain/wdpa/<id>', methods=['GET'])
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
    data, status = generate_response(status=404,
                 error_message='wdpa '+ id +' not found')
    return jsonify(data), status
  elif error == 500:
    data, status = generate_response(status=500,
                             error_message='ee bad response')
    return jsonify(data), status

  #@TODO sometimes use is not valid Check for error
  #gotta change umdservice when ee returns an error
  data, status = generate_response(status=200, data=data, umd_type='wdpa')
  return jsonify(data), status
