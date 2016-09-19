from flask import Flask, jsonify, request
import requests
## import umd

app = Flask(__name__)

@app.route('/umd/<id>')
def get_umd(id):
  """Return the umd"""
  ## call umd function
  return id;

@app.route('/umd')
def get_request():
  r = requests.get('https://www.google.com')
  return r.text

if __name__ == "__main__":
  app.run(host='127.0.0.1', port=8080, debug=True)
