import os
import json
import CTRegisterMicroserviceFlask
from routes.api.v1.umdendpoints import umd_endpoints
from utils.helpers import load_config_json
from flask import Flask


app = Flask(__name__) # Flask app
app.register_blueprint(umd_endpoints) # Matching routing (api/v1)


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
