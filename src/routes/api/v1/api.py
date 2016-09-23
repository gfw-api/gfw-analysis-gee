import os
import requests
from serializers import Error, Umd
from flask import request, jsonify, Blueprint
from utils.helpers import get_args_from_request, request_is_error
from services import umd

# Creating endpoints blueprint
endpoints = Blueprint('endpoints', __name__,)

# Serializers Interface
def generate_response(status, data={}, error_message=None):
 if request_is_error(status):
   data = Error.serialize(status, error_message=error_message)
 else:
   data = Umd.serialize(data)
 return data, status


@endpoints.route('/umd-loss-gain', methods=['GET'])
def get_world():
  """World Endpoint Controller"""
  # Negative check
  geostore = request.args.get('geostore')
  if not geostore:
    data, status = generate_response(status=400,
                                     error_message="geostore not provided")
    return jsonify(data), status

  # Getting geoJson from Api Gateway if it exists
  url = os.environ['GATEWAY_URL']+'/geostore/'+geostore
  r = requests.get(url)
  if r.status_code != 200:
    data, status = generate_response(status=r.status_code,
                             error_message="geostore not found")
    return jsonify(data), status

  # Defining args
  args = get_args_from_request(request)
  geojson = r.json()['data']['attributes']['geojson']
  args['geojson'] = geojson

  # Calling UMD
  world = umd.execute(args, 'world')
  data, status = generate_response(status=200, data=world)
  return jsonify(data), status


@endpoints.route('/umd-loss-gain/use/<name>/<id>', methods=['GET'])
def get_use(name, id):
  """Use Endpoint Controller
  name -- resource name
  id -- use id
  """
  # Negative Check
  useTable = None
  if name == 'mining':
    useTable = 'gfw_mining'
  elif name == 'oilpalm':
    useTable = 'gfw_oil_palm'
  elif name == 'fiber':
    useTable = 'gfw_wood_fiber';
  elif name == 'logging':
    useTable = 'gfw_logging';
  else:
    abort(400)

  # Defining args
  args = get_args_from_request(request)
  args['use'] = useTable
  args['useid'] = id

  # Calling UMD
  use = umd.execute(args, 'use')
  return jsonify(use) #@TODO JSON API FORMAT


@endpoints.route('/umd-loss-gain/wdpa/<id>', methods=['GET'])
def get_wdpa(id):
  """Wdpa Endpoint Controller
  id -- wdpa id
  """
  if id == None:
    abort(400)

  # Defining args
  args = get_args_from_request(request)
  args['wdpaid'] = id

  # Calling UMD
  wdpa = umd.execute(args, 'wdpa')
  return jsonify(wdpa) #@TODO JSON API FORMAT
