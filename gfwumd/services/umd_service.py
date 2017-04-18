# Global Forest Watch API
# Copyright (C) 2013 World Resource Institute
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""This module supports accessing UMD data."""


from utils.sql import Sql
from utils.cdb import CartoDbExecutor
from gfwumd.services import GeeService, CartoDBService


class UmdSql(Sql):
    USE = """
        SELECT CASE when ST_NPoints(the_geom)<=8000 THEN ST_AsGeoJson(the_geom)
        WHEN ST_NPoints(the_geom) BETWEEN 8000 AND 20000 THEN ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.001))
        ELSE ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.01))
        END as geojson,  (ST_Area(geography(the_geom))/10000) as area_ha  \
        FROM {use_table}
        WHERE cartodb_id = {pid} """

    WDPA = """
        SELECT CASE when marine::numeric = 2 THEN null
        WHEN ST_NPoints(the_geom)<=18000 THEN ST_AsGeoJson(the_geom)
        WHEN ST_NPoints(the_geom) BETWEEN 18000 AND 50000 THEN ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.001))
        ELSE ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.005))
        END as geojson, (ST_Area(geography(the_geom))/10000) as area_ha FROM wdpa_protected_areas where wdpaid={wdpaid} """

    @classmethod
    def download(cls, sql):
        """ TODO """
        return ""

    @classmethod
    def use(cls, params, args):
        params['thresh'] = args['thresh']
        return super(UmdSql, cls).use(params, args)

    @classmethod
    def wdpa(cls, params, args):
        params['thresh'] = args['thresh']
        return super(UmdSql, cls).wdpa(params, args)


class UmdService(object):
    """."""

    @staticmetod
    def get_world(geojson, thresh=30, begin='2001-01-01', end='2013-01-01'):
        """Query GEE using supplied args with threshold and polygon."""
        try:
            return GeeService.hansen_all(
                threshold=thresh,
                geojson=geojson,
                begin=begin,
                end=end)
        except HansenError as e:
            raise e
        except Exception as e:
            raise e


    @staticmethod
    def get_use(args):
        """Query GEE using supplied concession id."""
        data = CartoDbExecutor.execute(args, UmdSql)
        if 'error' in data:
            return data, 404

        rows = data['rows']
        args['geojson'] = rows[0]['geojson']
        args['areaHa'] = rows[0]['area_ha']
        return _execute_geojson(args)

    @staticmethod
    def get_wdpa(args):
        """Query GEE using supplied WDPA id."""
        data = CartoDbExecutor.execute(args, UmdSql)
        if len(data['rows']) == 0:
            return data, 404

        rows = data['rows']
        args['geojson'] = rows[0]['geojson']
        args['areaHa'] = rows[0]['area_ha']
        return _execute_geojson(args)
