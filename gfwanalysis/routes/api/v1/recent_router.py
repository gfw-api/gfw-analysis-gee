"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import asyncio

import logging
from flask import jsonify, Blueprint

from gfwanalysis.errors import RecentTilesError
from gfwanalysis.middleware import get_recent_params, get_recent_tiles, get_recent_thumbs
from gfwanalysis.routes.api import error
from gfwanalysis.serializers import serialize_recent_data
from gfwanalysis.serializers import serialize_recent_url
from gfwanalysis.services.analysis.recent_tiles import RecentTiles

recent_tiles_endpoints_v1 = Blueprint('recent_tiles_endpoints_v1', __name__)


def analyze_recent_data(lat, lon, start, end, bands, bmin, bmax, opacity):
    """Returns metadata and *first* tile url from GEE for all Sentinel images
       in date range ('start'-'end') that intersect with lat,lon.
    #Example of valid inputs (for area focused on Tenerife)
    lat = -16.589
    lon = 28.246
    start ='2017-03-01'
    end ='2017-03-10'
    """
    loop = asyncio.new_event_loop()

    try:
        data = RecentTiles.recent_data(lat=lat, lon=lon, start=start, end=end)
        data = loop.run_until_complete(RecentTiles.async_fetch(loop, RecentTiles.recent_tiles, data, bands, bmin, bmax, opacity, 'first'))
    except RecentTilesError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_recent_data(data, 'recent_tiles_data')), 200


def analyze_recent_tiles(data_array, bands, bmin, bmax, opacity):
    """Takes an array of JSON objects with a 'source' key for each tile url
    to be returned. Returns an array of 'source' names and 'tile_url' values.
    """

    loop = asyncio.new_event_loop()

    try:
        data = loop.run_until_complete(RecentTiles.async_fetch(loop, RecentTiles.recent_tiles, data_array, bands, bmin, bmax, opacity))
    except RecentTilesError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_recent_url(data, 'recent_tiles_url')), 200


def analyze_recent_thumbs(data_array, bands, bmin, bmax, opacity):
    """Takes an array of JSON objects with a 'source' key for each tile url
    to be returned. Returns an array of 'source' names and 'thumb_url' values.
    """
    loop = asyncio.new_event_loop()
    try:
        data = loop.run_until_complete(RecentTiles.async_fetch(loop, RecentTiles.recent_thumbs, data_array, bands, bmin, bmax, opacity))
    except RecentTilesError as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_recent_url(data, 'recent_thumbs_url')), 200


@recent_tiles_endpoints_v1.route('/', strict_slashes=False, methods=['GET'])
@get_recent_params
def get_by_geostore(lat, lon, start, end, bands, bmin, bmax, opacity):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting data for tiles for Recent Sentinel Images')
    data = analyze_recent_data(lat=lat, lon=lon, start=start, end=end, bands=bands, bmin=bmin, bmax=bmax, opacity=opacity)
    return data


@recent_tiles_endpoints_v1.route('/tiles', strict_slashes=False, methods=['POST'])
@get_recent_tiles
def get_by_tile(data_array, bands, bmin, bmax, opacity):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting tile url(s) for tiles for Recent Sentinel Images')
    data = analyze_recent_tiles(data_array=data_array, bands=bands, bmin=bmin, bmax=bmax, opacity=opacity)
    return data


@recent_tiles_endpoints_v1.route('/thumbs', strict_slashes=False, methods=['POST'])
@get_recent_thumbs
def get_by_thumb(data_array, bands, bmin, bmax, opacity):
    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting thumb url(s) for tiles for Recent Sentinel Images')
    data = analyze_recent_thumbs(data_array=data_array, bands=bands, bmin=bmin, bmax=bmax, opacity=opacity)
    return data
