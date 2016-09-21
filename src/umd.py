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

import json
import ee
import logging
import config

from common import CartoDbExecutor
from common import Sql

def _get_coords(geojson):
  if geojson.get('features') is not None:
    return geojson.get('features')[0].get('geometry').get('coordinates')
  elif geojson.get('geometry') is not None:
    return geojson.get('geometry').get('coordinates')
  else:
    return geojson.get('coordinates')


def _sum_range(data, begin, end):
  return sum(
    [value for key, value in data.iteritems()
      if (int(key) >= int(begin)) and (int(key) < int(end))])


def _get_thresh_image(thresh, asset_id):
  """Renames image bands using supplied threshold and returns image."""
  image = ee.Image(asset_id)

  # Select out the gain band if it exists
  if 'gain' in asset_id:
    before = image.select('.*_' + thresh, 'gain').bandNames()
  else:
    before = image.select('.*_' + thresh).bandNames()

  after = before.map(
    lambda x: ee.String(x).replace('_.*', ''))

  image = image.select(before, after)
  return image


def _get_type(geojson):
  if geojson.get('features'):
    return geojson.get('features')[0].get('geometry').get('type')
  elif geojson.get('geometry'):
    return geojson.get('geometry').get('type')
  else:
    return geojson.get('type')


def _get_region(geom):
  """Return ee.Geometry from supplied GeoJSON object."""
  poly = _get_coords(geom)
  ptype = _get_type(geom)
  if ptype.lower() == 'multipolygon':
    region = ee.Geometry.MultiPolygon(poly)
  else:
    region = ee.Geometry.Polygon(poly)
  return region


def _ee(geom, thresh, asset_id):
  image = _get_thresh_image(thresh, asset_id)
  region = _get_region(geom)

  # Reducer arguments
  reduce_args = {
    'reducer': ee.Reducer.sum(),
    'geometry': region,
    'bestEffort': True,
    'scale': 90
  }

  # Calculate stats
  area_stats = image.divide(10000 * 255.0) \
    .multiply(ee.Image.pixelArea()) \
    .reduceRegion(**reduce_args)
  area_results = area_stats.getInfo()

  return area_results


def _loss_area(row):
  """Return hectares of loss."""
  return row['year'], row['loss']


def _gain_area(row):
  """Return hectares of gain."""
  return row['year'], row['gain']


class UmdSql(Sql):
  USE = """
    SELECT CASE when ST_NPoints(the_geom)<=8000 THEN ST_AsGeoJson(the_geom)
    WHEN ST_NPoints(the_geom) BETWEEN 8000 AND 20000 THEN ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.001))
    ELSE ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.01))
    END as geojson
    FROM {use_table}
    WHERE cartodb_id = {pid}"""

  WDPA = """
    SELECT CASE when marine::numeric = 2 THEN null
    WHEN ST_NPoints(the_geom)<=18000 THEN ST_AsGeoJson(the_geom)
    WHEN ST_NPoints(the_geom) BETWEEN 18000 AND 50000 THEN ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.001))
    ELSE ST_AsGeoJson(ST_RemoveRepeatedPoints(the_geom, 0.005))
    END as geojson FROM wdpa_protected_areas WHERE wdpaid={wdpaid} """

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


def _execute_geojson(args):
  """Query GEE using supplied args with threshold and geojson."""

  # Authenticate to GEE and maximize the deadline
  ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
  ee.data.setDeadline(60000)

  # The forest cover threshold and polygon
  thresh = str(args.get('thresh'))

  try:
    geojson = json.loads(args.get('geojson'))
  except Exception:
    geojson = args.get('geojson')

  # hansen_all_thresh
  hansen_all = _ee(geojson, thresh, 'HANSEN/gfw2015_loss_tree_gain_threshold')
  # gain (UMD doesn't permit disaggregation of forest gain by threshold).
  gain = hansen_all['gain']
  logging.info('GAIN: %s' % gain)
  # tree extent in 2000
  tree_extent = hansen_all['tree']
  logging.info('TREE_EXTENT: %s' % tree_extent)

  # Loss by year
  loss_by_year = _ee(geojson, thresh, 'HANSEN/gfw_loss_by_year_threshold_2015')
  logging.info('LOSS_RESULTS: %s' % loss_by_year)

  # Reduce loss by year for supplied begin and end year
  begin = args.get('begin').split('-')[0]
  end = args.get('end').split('-')[0]
  loss = _sum_range(loss_by_year, begin, end)

  # Prepare result object
  result = {}
  result['gain'] = gain
  result['loss'] = loss
  result['tree-extent'] = tree_extent

  return result


def _executeWdpa(args):
  """Query GEE using supplied WDPA id."""
  action, data = CartoDbExecutor.execute(args, UmdSql)
  if action == 'error':
    return action, data
  rows = data['rows']
  data.pop('rows')
  data.pop('download_urls')
  if rows[0]['geojson']==None:
    args['geojson'] = rows[0]['geojson']
    args['begin'] = args['begin'] if 'begin' in args else '2001-01-01'
    args['end'] = args['end'] if 'end' in args else '2013-01-01'
    data['params'].pop('geojson')
    data['gain'] = 0
    data['loss'] = 0
    data['tree-extent'] = 0
  elif rows:
    args['geojson'] = rows[0]['geojson']
    args['begin'] = args['begin'] if 'begin' in args else '2001-01-01'
    args['end'] = args['end'] if 'end' in args else '2013-01-01'
    action, data = _execute_geojson(args)
    data['params'].pop('geojson')
  return action, data


def _executeUse(args):
  """Query GEE using supplied concession id."""
  print args
  data = CartoDbExecutor.execute(args, UmdSql)
  #if action == 'error':
  #  return action, data
  rows = data['rows']
  data.pop('rows')
  if rows:
    args['geojson'] = rows[0]['geojson']
    args['begin'] = args['begin'] if 'begin' in args else '2001-01-01'
    args['end'] = args['end'] if 'end' in args else '2013-01-01'
    data = _execute_geojson(args)
  return data


def _executeWorld(args):
  """Query GEE using supplied args with threshold and polygon."""
  return _execute_geojson(args)


def execute(args, query_type=False):
  """Execute wrapper."""
  # Check period and threshold
  args['begin'] = args['begin'] if 'begin' in args else '2001-01-01'
  args['end'] = args['end'] if 'end' in args else '2013-01-01'
  args['thresh'] = int(args['thresh']) if 'thresh' in args else 30

  if query_type == 'world':
    return _executeWorld(args)
  elif query_type == 'use':
    return _executeUse(args)
  elif query_type == 'wdpa':
    return _executeWdpa(args)
  else:
    raise NameError('Invalid umd_execute_query_type')
