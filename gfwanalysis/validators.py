"""VALIDATORS"""

from functools import wraps
from flask import request

from gfwanalysis.routes.api import error


def validate_world(func):
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
            return error(status=400, detail='Name not valid')
        return func(*args, **kwargs)
    return wrapper
