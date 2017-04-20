"""CARTO SQL SERVICE"""

import logging

import requests
from gfwanalysis.errors import CartoError
from gfwanalysis.config import SETTINGS

USE = """
        SELECT CASE when ST_NPoints(the_geom)<=8000 THEN ST_AsGeoJson(the_geom) \
        WHEN ST_NPoints(the_geom) BETWEEN 8000 AND 20000 THEN ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.001)) \
        ELSE ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.01)) \
        END as geojson,  (ST_Area(geography(the_geom))/10000) as area_ha  \
        FROM {{table}} \
        WHERE cartodb_id = {{id}}"""


WDPA = """
        SELECT CASE when marine::numeric = 2 then null \
        WHEN ST_NPoints(the_geom)<=18000 THEN ST_AsGeoJson(the_geom) \
        WHEN ST_NPoints(the_geom) BETWEEN 18000 AND 50000 THEN ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.001)) \
        ELSE ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.005)) \
        END as geojson, (ST_Area(geography(the_geom))/10000) as area_ha FROM wdpa_protected_areas where wdpaid={{id}}"""


def use_lookup_table(name):
    """."""
    if name == 'mining':
        use_table = 'gfw_mining'
    elif name == 'oilpalm':
        use_table = 'gfw_oil_palm'
    elif name == 'fiber':
        use_table = 'gfw_wood_fiber'
    elif name == 'logging':
        use_table = 'gfw_logging'
    return use_table


class CartoService(object):
    """."""

    carto = SETTINGS.get('carto')
    url = 'https://'+carto.get('service_account')+'.'+carto.get('uri')+'?q='

    @staticmethod
    def query(sql):
        url = CartoService.url+sql
        try:
            r = requests.get(url)
            data = r.json()
            if not data or len(data.get('rows')) == 0:
                raise CartoError(message='Carto Error')
        except Exception as e:
            raise e
        return data

    @staticmethod
    def get_use_geojson(name, use_id):
        table = use_lookup_table(name)
        sql = USE.replace("{{table}}", table).replace("{{id}}", use_id)
        return CartoService.query(sql)

    @staticmethod
    def get_wdpa_geojson(wdpa_id):
        sql = WDPA.replace("{{id}}", wdpa_id)
        return CartoService.query(sql)
