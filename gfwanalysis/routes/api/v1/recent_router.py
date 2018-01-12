"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import asyncio
import requests
import functools as funct

from flask import jsonify, Blueprint
from gfwanalysis.routes.api import error
from gfwanalysis.services.analysis.recent_tiles import RecentTiles
from gfwanalysis.errors import RecentTilesError
from gfwanalysis.serializers import serialize_recent_url
from gfwanalysis.middleware import get_recent_params
from gfwanalysis.middleware import get_recent_tiles
from gfwanalysis.middleware import get_recent_thumbs

recent_tiles_endpoints_v1 = Blueprint('recent_tiles_endpoints_v1', __name__) 

def analyze_recent_data(lat, lon, start, end):
    """Returns metadata and *first* tile url from GEE for all Sentinel images
       in date range ('start'-'end') that intersect with lat,lon.
    #Example of valid inputs (for area focused on Tenerife)
    lat = -16.589
    lon = 28.246
    start ='2017-03-01'
    end ='2017-03-10'
    """
    logging.info("[ANALYSIS>DATA] function initiated")
    
    try:
        data = RecentTiles.recent_data(lat=lat, lon=lon, start=start, end=end)
        data = RecentTiles.async_fetch(RecentTiles.recent_tiles, data)
        data = RecentTiles.async_fetch(RecentTiles.recent_thumbs, data)
        logging.info("[ANALYSIS>DATA] Complete!")
    except RecentTilesError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_recent_url(data, 'recent_tiles_url')), 200

def analyze_recent_tiles(lat, lon, start, end):
    """Returns metadata and *first* tile url from GEE for all Sentinel images
       in date range ('start'-'end') that intersect with lat,lon.
    #Example of valid inputs (for area focused on Tenerife)
    lat = -16.589
    lon = 28.246
    start ='2017-03-01'
    end ='2017-03-10'
    """
    logging.info("[ANALYSIS>TILES] function initiated")
    
    try:
        data = RecentTiles.recent_data(lat=lat, lon=lon, start=start, end=end)
        data = RecentTiles.async_fetch(RecentTiles.recent_tiles, data)
        logging.info("[ANALYSIS>DATA] Complete!")
    except RecentTilesError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_recent_url(data, 'recent_tiles_url')), 200

def analyze_recent_thumbs(lat, lon, start, end):
    """Returns metadata and *first* tile url from GEE for all Sentinel images
       in date range ('start'-'end') that intersect with lat,lon.
    #Example of valid inputs (for area focused on Tenerife)
    lat = -16.589
    lon = 28.246
    start ='2017-03-01'
    end ='2017-03-10'
    """
    logging.info("[ANALYSIS>THUMBS] function initiated")
    
    try:
        data = RecentTiles.recent_data(lat=lat, lon=lon, start=start, end=end)
        data = RecentTiles.async_fetch(RecentTiles.recent_thumbs, data)
        logging.info("[ANALYSIS>DATA] Complete!")
    except RecentTilesError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=serialize_recent_url(data, 'recent_tiles_url')), 200

@recent_tiles_endpoints_v1.route('/', strict_slashes=False, methods=['GET'])
@get_recent_params
def get_by_geostore(lat, lon, start, end):

    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting url(s) for tiles for Recent Sentinel Images')
    data = analyze_recent_data(lat=lat, lon=lon, start=start, end=end)   
    return data

@recent_tiles_endpoints_v1.route('/tiles', strict_slashes=False, methods=['GET'])
@get_recent_tiles
def get_by_tile(lat, lon, start, end):

    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting url(s) for tiles for Recent Sentinel Images')
    data = analyze_recent_tiles(lat=lat, lon=lon, start=start, end=end)   
    return data

@recent_tiles_endpoints_v1.route('/thumbs', strict_slashes=False, methods=['GET'])
@get_recent_thumbs
def get_by_thumb(lat, lon, start, end):

    """Analyze by geostore"""
    logging.info('[ROUTER]: Getting url(s) for tiles for Recent Sentinel Images')
    data = analyze_recent_thumbs(lat=lat, lon=lon, start=start, end=end)   
    return data