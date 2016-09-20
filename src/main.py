import os
import requests

from flask import Flask, jsonify, request, abort
import umd

app = Flask(__name__)

os.environ['GATEWAY_URL']='http://staging-api.globalforestwatch.org'
os.environ['GATEWAY_TOKEN']='yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Im1pY3Jvc2VydmljZSIsImNyZWF0ZWRBdCI6IjIwMTYtMDktMTQifQ.eUmM_C8WNPBk8EJS3rHo2Zc4wCmYkzyRpRyK8ZzDV2U'

@app.route('/umd-loss-gain', methods=['GET'])
def get_world():
  """Return world"""
  geostore = request.args.get('geostore')
  if not geostore:
    abort(404)

  ## Getting geoJson from Api Gateway
  url = os.environ['GATEWAY_URL']+'/geostore/'+geostore
  r = requests.get(url)
  if r.status_code != 200:
    return jsonify(r.json())

  ## Executing EE
  args = {}
  begin = request.args.get('begin')
  end = request.args.get('end')
  thresh = request.args.get('thresh')

  if begin:
    args['begin'] = begin

  if end:
    args['end'] = end

  if thresh:
    args['thresh'] = thresh

  geojson = r.json()['data']['attributes']['geojson']
  args['geojson'] = geojson
  world = umd.execute(args, 'world')
  return jsonify(world)

@app.route('/umd-loss-gain/use/<name>/<id>', methods=['GET'])
def get_use(name, id):
  """Return use"""
  ## call umd function
  return jsonify(id, name);

@app.route('/umd-loss-gain/wdpa/<id>', methods=['GET'])
def get_wdpa(id):
  """Return wdpa"""
  pass

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8080, debug=True)
