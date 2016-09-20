import ee
import os
import json
import logging
import config
import sys


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
    if geojson.get('features') is not None:
        return geojson.get('features')[0].get('geometry').get('type')
    elif geojson.get('geometry') is not None:
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


def _execute_geojson(thresh, geojson, begin, end):
    """Query GEE using supplied args with threshold and geojson."""

    # Authenticate to GEE and maximize the deadline
    ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
    # ee.Initialize()
    ee.data.setDeadline(60000)
    geojson = json.loads(geojson)
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
    begin = begin.split('-')[0]
    end = end.split('-')[0]
    loss = _sum_range(loss_by_year, begin, end)

    # Prepare result object
    result = {}
    # result['params'] = args
    # result['params']['geojson'] = json.loads(result['params']['geojson'])
    result['gain'] = gain
    result['loss'] = loss
    result['tree-extent'] = tree_extent

    return result



thresh = sys.argv[1]
geojsonPath = sys.argv[2]
begin = sys.argv[3]
end = sys.argv[4]


txt_file = open(geojsonPath)

print (json.dumps(_execute_geojson(thresh, txt_file.read(), begin, end)))
