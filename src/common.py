# Global Forest Watch API
# Copyright (C) 2015 World Resource Institute
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

"""Module with common stuff for forestchange."""

import copy
import json
import cdb

def classify_query(args):
  if 'ifl' in args:
    return 'ifl'
  elif 'use' in args:
    return 'use'
  elif 'wdpaid' in args:
    return 'wdpa'
  elif 'latest' in args:
    return 'latest'
  else:
    return 'use'


def args_params(params, args, min_max_sql):
  if args.get('alert_query'):
    params['additional_select'] = min_max_sql
  else:
    params['additional_select'] = ""

  if args.get('iso'):
    params['iso'] = args['iso']
  if args.get('id1'):
    params['id1'] = args['id1']
  if args.get('geojson'):
    params['geojson'] = args['geojson']
  if args.get('wdpaid'):
    params['wdpaid'] = args['wdpaid']
  return params


class SqlError(ValueError):
  def __init__(self, msg):
    super(SqlError, self).__init__(msg)

class Sql(object):

  MIN_MAX_DATE_SQL = ', MIN(date) as min_date, MAX(date) as max_date'

  @classmethod
  def get_query_type(cls, params, args, the_geom_table=''):
    """Return query type (download or analysis) with updated params."""
    query_type = 'analysis'
    if 'format' in args:
      query_type = 'download'
      if args['format'] != 'csv':
        the_geom = ', the_geom' \
          if not the_geom_table \
          else ', %s.the_geom' % the_geom_table
        params['the_geom'] = the_geom
    return query_type, params

  @classmethod
  def cleanAlert(cls, args, query):
    """Remove specified sql for alerts if exists"""
    if (args.get('alert_query') and hasattr(cls, "ALERT_SQL_REMOVALS")):
      for removal_sql in cls.ALERT_SQL_REMOVALS:
        query = query.replace(removal_sql, "")
      query = ' '.join(query.split())
      query = query.replace(', ,', ',')
    return query

  @classmethod
  def clean(cls, sql):
    """Return sql clean  with extra whitespace removed."""
    if sql:
      return ' '.join(sql.split())

  @classmethod
  def process(cls, args):
    begin = args['begin'] if 'begin' in args else '2014-01-01'
    end = args['end'] if 'end' in args else '2015-01-01'
    params = dict(begin=begin, end=end)
    classification = classify_query(args)
    if hasattr(cls, classification):
      return map(cls.clean, getattr(cls, classification)(params, args))

  @classmethod
  def world(cls, params, args):
    params = args_params(params, args, cls.MIN_MAX_DATE_SQL)
    query_type, params = cls.get_query_type(params, args)
    query = cls.WORLD.format(**params)
    query = cls.cleanAlert(args, query)
    download_query = cls.download(query)
    return query, download_query

  @classmethod
  def wdpa(cls, params, args):
    params = args_params(params, args, cls.MIN_MAX_DATE_SQL)
    query_type, params = cls.get_query_type(params, args)
    query = cls.WDPA.format(**params)
    query = cls.cleanAlert(args, query)
    download_query = cls.download(cls.WDPA.format(**params))
    return query, download_query

  @classmethod
  def use(cls, params, args):
    concessions = {
      'mining': 'gfw_mining',
      'oilpalm': 'gfw_oil_palm',
      'fiber': 'gfw_wood_fiber',
      'logging': 'gfw_logging'
    }
    params['use_table'] = concessions.get(args['use']) or args['use']
    params['pid'] = args['useid']
    params = args_params(params, args, cls.MIN_MAX_DATE_SQL)
    query_type, params = cls.get_query_type(params, args)
    query = cls.USE.format(**params)
    download_query = cls.download(cls.USE.format(**params))
    return query, download_query

  @classmethod
  def latest(cls, params, args):
    params['limit'] = args.get('limit') or 3
    query = cls.LATEST.format(**params)
    return query, None


def get_download_urls(query, params):
  urls = {}
  args = copy.copy(params)
  for fmt in ['csv', 'geojson', 'svg', 'kml', 'shp']:
    args['format'] = fmt
    urls[fmt] = cdb.get_url(query, args)
  return urls


class CartoDbExecutor():

  @classmethod
  def _query_response(cls, response, params, query):
    """Return world response."""
    result = {}

    if response.status_code == 200:
      rows = json.loads(response.content)['rows']
      if rows:
          result['rows'] = rows
    else:
      result['error'] = 'CartoDB Error: %s' % response.content

    result['params'] = params
    if 'geojson' in params:
      result['params']['geojson'] = json.loads(params['geojson'])
    if 'dev' in params:
      result['dev'] = {'sql': query}

    return result

  @classmethod
  def execute(cls, args, sql):
    try:
        query, download_query = sql.process(args)

        download_url = cdb.get_url(query, args)

        response = cdb.execute(query)

        #response = cls._query_response(response, args, query)
        #if 'error' in response:
        #  action = 'error'
        return response

    except Exception, e:
      return 'execute() error', e
