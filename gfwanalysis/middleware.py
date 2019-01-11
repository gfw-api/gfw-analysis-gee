"""MIDDLEWARE"""

from functools import wraps
from flask import request

import logging

from gfwanalysis.routes.api import error
from gfwanalysis.services.geostore_service import GeostoreService
from gfwanalysis.services.area_service import AreaService
from gfwanalysis.errors import GeostoreNotFound
from gfwanalysis.services.analysis.landsat_tiles import RedisService


def exist_tile(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        url = RedisService.get(request.path)
        if url is None:
            return func(*args, **kwargs)
        else:
            return redirect(url)
    return wrapper


def exist_mapid(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        year = kwargs['year']
        kwargs["map_object"] = RedisService.check_year_mapid(year)
        return func(*args, **kwargs)
    return wrapper


def get_sentinel_params(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            lat = request.args.get('lat')
            lon = request.args.get('lon')
            start = request.args.get('start')
            end = request.args.get('end')
            if not lat or not lon or not start or not end:
                return error(status=400, detail='Some parameters are needed')
        kwargs["lat"] = lat
        kwargs["lon"] = lon
        kwargs["start"] = start
        kwargs["end"] = end
        return func(*args, **kwargs)
    return wrapper

def get_highres_params(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if request.method == 'GET':
            lat = request.args.get('lat')
            lon = request.args.get('lon')
            start = request.args.get('start')
            end = request.args.get('end')
            if not lat or not lon or not start or not end:
                return error(status=400, detail='Some parameters are needed')
        kwargs["lat"] = lat
        kwargs["lon"] = lon
        kwargs["start"] = start
        kwargs["end"] = end
        return func(*args, **kwargs)
    return wrapper

def get_recent_params(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if request.method == 'GET':
            lat = request.args.get('lat')
            lon = request.args.get('lon')
            start = request.args.get('start')
            end = request.args.get('end')
            bands = request.args.get('bands', None)
            if not lat or not lon or not start or not end:
                return error(status=400, detail='[RECENT] Parameters: (lat, lon. start, end) are needed')
        kwargs["lat"] = lat
        kwargs["lon"] = lon
        kwargs["start"] = start
        kwargs["end"] = end
        kwargs["bands"] = bands
        return func(*args, **kwargs)
    return wrapper

def get_recent_tiles(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if request.method == 'POST':
            data_array = request.get_json().get('source_data')
            bands = request.get_json().get('bands', None)
            if not data_array:
                return error(status=400, detail='[TILES] Some parameters are needed')
        kwargs["data_array"] = data_array
        kwargs["bands"] = bands

        return func(*args, **kwargs)
    return wrapper

def get_recent_thumbs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if request.method == 'POST':
            data_array = request.get_json().get('source_data')
            bands = request.get_json().get('bands', None)
            if not data_array:
                return error(status=400, detail='[THUMBS] Some parameters are needed')
        kwargs["data_array"] = data_array
        kwargs["bands"] = bands

        return func(*args, **kwargs)
    return wrapper

def get_geo_by_hash(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            geostore = request.args.get('geostore')
            if not geostore:
                return error(status=400, detail='Geostore is required')
            try:
                geojson, area_ha = GeostoreService.get(geostore)
            except GeostoreNotFound:
                return error(status=404, detail='Geostore not found')
        elif request.method == 'POST':
            geojson = request.get_json().get('geojson', None) if request.get_json() else None
            try:
                area_ha = AreaService.tabulate_area(geojson)
            except Exception as e:
                return error(status=500, detail=str(e))

        kwargs["geojson"] = geojson
        kwargs["area_ha"] = area_ha
        return func(*args, **kwargs)
    return wrapper


def get_geo_by_national(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            try:
                iso = request.view_args.get('iso')
                geojson, area_ha = GeostoreService.get_national(iso)
            except GeostoreNotFound:
                return error(status=404, detail='Geostore not found')
            kwargs["geojson"] = geojson
            kwargs["area_ha"] = area_ha
        return func(*args, **kwargs)
    return wrapper


def get_geo_by_subnational(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            try:
                iso = request.view_args.get('iso')
                id1 = request.view_args.get('id1')
                geojson, area_ha = GeostoreService.get_subnational(iso, id1)
            except GeostoreNotFound:
                return error(status=404, detail='Geostore not found')
            kwargs["geojson"] = geojson
            kwargs["area_ha"] = area_ha
        return func(*args, **kwargs)
    return wrapper

def get_geo_by_regional(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            try:
                iso = request.view_args.get('iso')
                id1 = request.view_args.get('id1')
                id2 = request.view_args.get('id2')
                geojson, area_ha = GeostoreService.get_regional(iso, id1, id2)
            except GeostoreNotFound:
                return error(status=404, detail='Geostore not found')
            kwargs["geojson"] = geojson
            kwargs["area_ha"] = area_ha
        return func(*args, **kwargs)
    return wrapper

def get_geo_by_use(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            try:
                name = request.view_args.get('name')
                use_id = request.view_args.get('id')
                geojson, area_ha = GeostoreService.get_use(name, use_id)
            except GeostoreNotFound:
                return error(status=404, detail='Geostore not found')
            kwargs["geojson"] = geojson
            kwargs["area_ha"] = area_ha
        return func(*args, **kwargs)
    return wrapper


def get_geo_by_wdpa(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            try:
                wdpa_id = request.view_args.get('id')
                geojson, area_ha = GeostoreService.get_wdpa(wdpa_id)
            except GeostoreNotFound:
                return error(status=404, detail='Geostore not found')
            kwargs["geojson"] = geojson
            kwargs["area_ha"] = area_ha
        return func(*args, **kwargs)
    return wrapper
