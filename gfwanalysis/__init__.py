"""The GFW ANALYSIS API MODULE"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os

import RWAPIMicroservicePython
import ee
from flask import Flask

from gfwanalysis.config import SETTINGS
from gfwanalysis.routes.api import error
from gfwanalysis.routes.api.v1 import hansen_endpoints_v1, forma250_endpoints_v1, \
    biomass_loss_endpoints_v1, landsat_tiles_endpoints_v1, histogram_endpoints_v1, \
    landcover_endpoints_v1, sentinel_tiles_endpoints_v1, highres_tiles_endpoints_v1, \
    recent_tiles_endpoints_v1, whrc_biomass_endpoints_v1, mangrove_biomass_endpoints_v1, \
    population_endpoints_v1, soil_carbon_endpoints_v1, mc_analysis_endpoints_v1, \
    recent_tiles_classifier_v1, composite_service_v1, geodescriber_endpoints_v1
from gfwanalysis.routes.api.v2 import biomass_loss_endpoints_v2, landsat_tiles_endpoints_v2, nlcd_landcover_endpoints_v2
from gfwanalysis.utils.files import load_config_json

logging.basicConfig(
    level=SETTINGS.get('logging', {}).get('level'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y%m%d-%H:%M%p',
)

# Initializing GEE
gee = SETTINGS.get('gee')
ee_user = gee.get('service_account')
private_key_file = gee.get('privatekey_file')
if private_key_file:
    logging.info(f'Initializing EE with privatekey.json credential file: {ee_user} | {private_key_file}')
    credentials = ee.ServiceAccountCredentials(ee_user, private_key_file)
    ee.Initialize(credentials)
    ee.data.setDeadline(60000)
else:
    raise ValueError("privatekey.json file not found. Unable to authenticate EE.")

# Flask App
app = Flask(__name__)

# Routing
app.register_blueprint(hansen_endpoints_v1, url_prefix='/api/v1/umd-loss-gain')
app.register_blueprint(forma250_endpoints_v1, url_prefix='/api/v1/forma250gfw')
app.register_blueprint(biomass_loss_endpoints_v1, url_prefix='/api/v1/biomass-loss')
app.register_blueprint(biomass_loss_endpoints_v2, url_prefix='/api/v2/biomass-loss')
app.register_blueprint(landsat_tiles_endpoints_v1, url_prefix='/api/v1/landsat-tiles')
app.register_blueprint(landsat_tiles_endpoints_v2, url_prefix='/api/v2/landsat-tiles')
app.register_blueprint(sentinel_tiles_endpoints_v1, url_prefix='/api/v1/sentinel-tiles')
app.register_blueprint(highres_tiles_endpoints_v1, url_prefix='/api/v1/highres-tiles')
app.register_blueprint(recent_tiles_endpoints_v1, url_prefix='/api/v1/recent-tiles')
app.register_blueprint(histogram_endpoints_v1, url_prefix='/api/v1/loss-by-landcover')
app.register_blueprint(landcover_endpoints_v1, url_prefix='/api/v1/landcover')
app.register_blueprint(mangrove_biomass_endpoints_v1, url_prefix='/api/v1/mangrove-biomass')
app.register_blueprint(population_endpoints_v1, url_prefix='/api/v1/population')
app.register_blueprint(whrc_biomass_endpoints_v1, url_prefix='/api/v1/whrc-biomass')
app.register_blueprint(soil_carbon_endpoints_v1, url_prefix='/api/v1/soil-carbon')
app.register_blueprint(recent_tiles_classifier_v1, url_prefix='/api/v1/recent-tiles-classifier')
app.register_blueprint(composite_service_v1, url_prefix='/api/v1/composite-service')
app.register_blueprint(geodescriber_endpoints_v1, url_prefix="/api/v1/geodescriber")
app.register_blueprint(mc_analysis_endpoints_v1, url_prefix="/api/v1/mc-analysis")
app.register_blueprint(nlcd_landcover_endpoints_v2, url_prefix='/api/v2/nlcd-landcover')

# CT
info = load_config_json('register')
swagger = load_config_json('swagger')
RWAPIMicroservicePython.register(
    app=app,
    name='gfw-umd',
    info=info,
    swagger=swagger,
    mode=RWAPIMicroservicePython.AUTOREGISTER_MODE if os.getenv('CT_REGISTER_MODE') and os.getenv('CT_REGISTER_MODE') == 'auto' else RWAPIMicroservicePython.NORMAL_MODE,
    ct_url=os.getenv('CT_URL'),
    url=os.getenv('LOCAL_URL'),
    token=os.getenv('CT_TOKEN'),
    api_version=os.getenv('API_VERSION')
)


@app.errorhandler(403)
def forbidden(e):
    return error(status=403, detail='Forbidden')


@app.errorhandler(404)
def page_not_found(e):
    return error(status=404, detail='Not Found')


@app.errorhandler(405)
def method_not_allowed(e):
    return error(status=405, detail='Method Not Allowed')


@app.errorhandler(410)
def gone(e):
    return error(status=410, detail='Gone')


@app.errorhandler(500)
def internal_server_error(e):
    return error(status=500, detail='Internal Server Error')
