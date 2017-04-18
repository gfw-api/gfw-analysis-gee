"""GEFAPI VALIDATORS"""

import logging
import re

from gefapi.routes.api.v1 import error

from functools import wraps
from flask import request, jsonify


def validate_world(func):
    """World Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
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


def use_validator(name):
  useTable = False
  if name == 'mining':
    useTable = 'gfw_mining'
  elif name == 'oilpalm':
    useTable = 'gfw_oil_palm'
  elif name == 'fiber':
    useTable = 'gfw_wood_fiber'
  elif name == 'logging':
    useTable = 'gfw_logging'
  return useTable
