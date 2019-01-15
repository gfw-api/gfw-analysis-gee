"""VALIDATORS"""

from functools import wraps
from flask import request

from gfwanalysis.routes.api import error


def validate_landsat_year(func):
    """Landsat Years Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        years = ['2013', '2014', '2015', '2016', '2017']
        year = kwargs['year']
        if year not in years:
            return error(status=400, detail='Year is not valid')
        return func(*args, **kwargs)
    return wrapper


def validate_geostore(func):
    """World Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            geostore = request.args.get('geostore')
            if not geostore:
                return error(status=400, detail='Geostore is required')
        return func(*args, **kwargs)
    return wrapper


def validate_use(func):
    """Use Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        names = ['mining', 'oilpalm', 'fiber', 'logging']
        name = request.view_args.get('name')
        if name not in names:
            return error(status=400, detail='Name is not valid')
        return func(*args, **kwargs)
    return wrapper
