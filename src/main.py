import os
import requests
import json
import CTRegisterMicroserviceFlask
from business import umd
from models.Error import Error, ErrorSchema
from models.Umd import Umd, UmdSchema
from flask import Flask, request, abort, jsonify

app = Flask(__name__)

# Helpers
def load_config_json(name):
  json_path = os.path.abspath(os.path.join(os.pardir,'microservice'))+'/'+name+'.json'
  with open(json_path) as data_file:
    info = json.load(data_file)
  return info

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

def is_error(status):
  first_element = str(status).split()[0][0]
  if first_element == '4' or first_element == '5':
    return True
  else:
    return False

def generate_error(status, error_message):
  error = Error(errors=[
    {
    'status': status,
    'detail': error_message
    }
  ])
  response = ErrorSchema().dump(error)
  return response

def generate_success(data):
  umd = Umd(id=0,
            type='world', #@TODO
            attributes=data)
  response = UmdSchema().dump(umd)
  return response

def generate_response(status, data={}, error_message=None):
  if is_error(status):
    data = generate_error(status, error_message=error_message)
  else:
    data = generate_success(data)
  return jsonify(data), status

@app.route('/umd-loss-gain', methods=['GET'])
def get_world():
  """World Endpoint Controller"""
  # Negative check
  geostore = request.args.get('geostore')
  if not geostore:
    return generate_response(status=400, error_message="geostore not provided")

  # Getting geoJson from Api Gateway if it exists
  url = os.environ['GATEWAY_URL']+'/geostore/'+geostore
  r = requests.get(url)
  if r.status_code != 200:
    return generate_response(status=r.status_code,
                             error_message="geostore not found")

  # Defining args
  args = get_args_from_request(request)
  geojson = r.json()['data']['attributes']['geojson']
  args['geojson'] = geojson

  # Calling UMD
  world = umd.execute(args, 'world')
  return generate_response(status=200, data=world)


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
  # Registering microservice
  info = load_config_json('register')
  swagger = load_config_json('swagger')
  CTRegisterMicroserviceFlask.register(
    app=app,
    name='gfw-umd-gee',
    info=info,
    swagger=swagger,
    mode=CTRegisterMicroserviceFlask.AUTOREGISTER_MODE,
    ct_url=os.environ['GATEWAY_URL'],
    url='http://mymachine:'+os.environ['PORT']
  )
  app.run(host='0.0.0.0',
          port=int(os.environ['PORT']),
          debug=os.environ['DEBUG_MODE'] == 'True')
