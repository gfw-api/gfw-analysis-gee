"""MIDDLEWARE"""

from flask import request
from functools import wraps
import json
import logging
from gfwanalysis.errors import GeostoreNotFound
from gfwanalysis.routes.api import error
from gfwanalysis.services.analysis.landsat_tiles_v2 import RedisService
from gfwanalysis.services.area_service import AreaService
from gfwanalysis.services.geostore_service import GeostoreService


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

def get_classification_params(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            img_id = request.args.get('img_id')
            if not img_id:
                return error(status=400, detail='An img_id string is needed (from Landsat-8 or Sentinel-2 collections).')
        kwargs["img_id"] = img_id
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

def get_sentinel_mosaic_params(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if request.method == 'GET':
            start = request.args.get('start', None)
            end = request.args.get('end', None)
            cloudscore_thresh = request.args.get('cloudscore_thresh', 10)
            bounds = request.args.get('bounds', False)
        kwargs["start"] = start
        kwargs["end"] = end
        kwargs["cloudscore_thresh"] = cloudscore_thresh
        kwargs["bounds"] = bounds
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
            sort_by = request.args.get('sort_by', None)
            bmin = request.args.get('min', None)
            bmax = request.args.get('max', None)
            opacity = request.args.get('opacity', 1.0)
            bands = request.args.get('bands', None)
            if not lat or not lon or not start or not end:
                return error(status=400, detail='[RECENT] Parameters: (lat, lon. start, end) are needed')
        kwargs["lat"] = lat
        kwargs["lon"] = lon
        kwargs["start"] = start
        kwargs["end"] = end
        kwargs["sort_by"] = sort_by
        kwargs["bmin"] = bmin
        kwargs["bmax"] = bmax
        kwargs["opacity"] = float(opacity)
        kwargs["bands"] = bands
        return func(*args, **kwargs)

    return wrapper


def get_recent_tiles(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'POST':
            data_array = request.get_json().get('source_data')
            bands = request.args.get('bands', None)
            bmin = request.args.get('min', None)
            bmax = request.args.get('max', None)
            opacity = request.args.get('opacity', 1.0)
            if not data_array:
                return error(status=400, detail='[TILES] Some parameters are needed')
        kwargs["data_array"] = data_array
        kwargs["bands"] = bands
        kwargs["data_array"] = data_array
        kwargs["bands"] = bands
        kwargs["bmin"] = bmin
        kwargs["bmax"] = bmax
        kwargs["opacity"] = float(opacity)
        return func(*args, **kwargs)

    return wrapper


def get_recent_thumbs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if request.method == 'POST':
            data_array = request.get_json().get('source_data')
            bands = request.args.get('bands', None)
            bmin = request.args.get('min', None)
            bmax = request.args.get('max', None)
            opacity = request.args.get('opacity', 1.0)
            if not data_array:
                return error(status=400, detail='[THUMBS] Some parameters are needed')
        kwargs["data_array"] = data_array
        kwargs["bands"] = bands
        kwargs["bmin"] = bmin
        kwargs["bmax"] = bmax
        kwargs["opacity"] = float(opacity)
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
                logging.info(f"[middleware geo hash] Exception")
                return error(status=500, detail=str(e))

        kwargs["geojson"] = geojson
        kwargs["area_ha"] = area_ha
        return func(*args, **kwargs)

    return wrapper

def get_composite_params(func):
    """Get instrument"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method in ['GET','POST']:
            instrument = request.args.get('instrument', False)
            if not instrument:
                instrument = 'landsat'
            date_range = request.args.get('date_range', False)
            if not date_range:
                date_range = ""
            thumb_size = request.args.get('thumb_size', False)
            if not thumb_size:
                thumb_size = [500, 500]
            else:
                thumb_size = [int(size.strip()) for size in thumb_size.replace('[', '').replace(']', '').split(',')]
            classify = request.args.get('classify', False)
            if classify and classify.lower() == 'true':
                classify = True
            else:
                classify = False
            band_viz = request.args.get('band_viz', False)
            if not band_viz:
                band_viz = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.4}
            else:
                band_viz = json.loads(band_viz)
            get_dem = request.args.get('get_dem', False)
            if get_dem and get_dem.lower() == 'true':
                get_dem = True
            else:
                get_dem = False
            get_stats = request.args.get('get_stats', False)
            if get_stats and get_stats.lower() == 'true':
                get_stats = True
            else:
                get_stats = False
            show_bounds = request.args.get('show_bounds', False)
            if show_bounds and show_bounds.lower() == 'true':
                show_bounds = True
            else:
                show_bounds = False
            cloudscore_thresh = request.args.get('cloudscore_thresh', False)
            if not cloudscore_thresh:
                cloudscore_thresh = 5
            else:
                cloudscore_thresh = int(cloudscore_thresh)
        kwargs['get_stats'] = get_stats
        kwargs['get_dem'] = get_dem
        kwargs['classify'] = classify
        kwargs['thumb_size'] = thumb_size
        kwargs['date_range'] = date_range
        kwargs['instrument'] = instrument
        kwargs['band_viz'] = band_viz
        kwargs['show_bounds'] = show_bounds
        kwargs['cloudscore_thresh'] = cloudscore_thresh
        return func(*args, **kwargs)
    return wrapper


def get_geo_by_geom(func):
    """Get geometry data"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            #logging.info(f'[decorater - geom]: Getting area by GET {request}')
            geojson = request.args.get('geojson')
            if not geojson:
                return error(status=400, detail='geojson is required')
        elif request.method == 'POST':
            geojson = request.get_json().get('geojson', None) if request.get_json() else None
        try:
            area_ha = AreaService.tabulate_area(geojson)
        except Exception as e:
            return error(status=500, detail=str(e))
        kwargs["geojson"] = geojson
        kwargs['area_ha'] = area_ha
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
