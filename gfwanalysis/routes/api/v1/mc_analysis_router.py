"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from flask import jsonify, request, Blueprint

from gfwanalysis.errors import MCAnalysisError
from gfwanalysis.middleware import  get_mc_info
from gfwanalysis.routes.api import error, set_params
from gfwanalysis.serializers import serialize_mc
from gfwanalysis.services.analysis.mc_analysis_service import MCAnalysisService

mc_analysis_endpoints_v1 = Blueprint('mc_analsysis_endpoints_v1', __name__)


def analyze(timeseries, window=None, mc_number=None, bin_number=None):
    """Analyze Monte Carlo"""
    if not timeseries:
        return error(status=400, detail='A timeseries is required')
    logging.info(f'[ROUTER MC]: timeseries={timeseries}')
    try:
        data = MCAnalysisService.analyze(
            timeseries=timeseries,
            window=window,
            mc_number=mc_number,
            bin_number=bin_number)
    except MCAnalysisError as e:
        logging.error(f'[ROUTER MC]:  {e.message}')
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error(f'[ROUTER MC]: {e}')
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_mc(data, 'mc_timeseries_analysis')), 200


@mc_analysis_endpoints_v1.route('/', strict_slashes=False, methods=['POST'])
@get_mc_info
def get_timeseries(timeseries, window, mc_number, bin_number):
    """Analyze timeseries"""
    logging.info(f'[ROUTER MC getter]: {timeseries}, {window}, {mc_number}, {bin_number}')
    return analyze(timeseries=timeseries, window=window,
                     mc_number=mc_number, bin_number=bin_number)

