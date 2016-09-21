import os
import requests

from flask import Flask, jsonify, request, abort
import umd

app = Flask(__name__)

os.environ['GATEWAY_URL']='http://staging-api.globalforestwatch.org'
os.environ['GATEWAY_TOKEN']='yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Im1pY3Jvc2VydmljZSIsImNyZWF0ZWRBdCI6IjIwMTYtMDktMTQifQ.eUmM_C8WNPBk8EJS3rHo2Zc4wCmYkzyRpRyK8ZzDV2U'
os.environ['UMD_GEE_API_HOST'] = '0.0.0.0'
os.environ['UMD_GEE_API_PORT'] = '8080'
os.environ['DEBUG_MODE'] = 'True'

def get_args_from_request(request):
  """Helper function to get arguments"""
  args = {}
  period = request.args.get('period')
  thresh = request.args.get('thresh')

  if period:
    args['begin'] = period.split(',')[0]
    args['end'] = period.split(',')[1]
  if thresh:
    args['thresh'] = thresh

  return args


@app.route('/umd-loss-gain', methods=['GET'])
def get_world():
  """World Endpoint Controller"""
  # Negative check
  geostore = request.args.get('geostore')
  if not geostore:
    abort(400)

  # Getting geoJson from Api Gateway if it exists
  url = os.environ['GATEWAY_URL']+'/geostore/'+geostore
  r = requests.get(url)
  if r.status_code != 200:
    return abort(r.status_code)

  # Defining args
  args = get_args_from_request(request)
  geojson = r.json()['data']['attributes']['geojson']
  args['geojson'] = geojson

  # Calling UMD
  world = umd.execute(args, 'world')
  return jsonify(world) #@TODO JSON API FORMAT

@app.route('/umd-loss-gain/use/<name>/<id>', methods=['GET'])
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

@app.route('/umd-loss-gain/wdpa/<id>', methods=['GET'])
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

if __name__ == "__main__":
  app.run(host=os.environ['UMD_GEE_API_HOST'],
          port=int(os.environ['UMD_GEE_API_PORT']),
          debug=os.environ['DEBUG_MODE'] == 'True')
