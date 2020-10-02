import asyncio
import functools as funct
import logging

import ee
import geocoder
from shapely.geometry import shape, GeometryCollection


def get_extent_fc(image, fc, method='reduce_regions', bestEffort=False, scale=False, numPixels=10000):
    """ Given an ee.featureCollection (fc) of features each with
    a single geometry calculate the total extent (area_m2) using
    a single band binary image. The single band binary image is
    multiplied by pixel area, ee.Reducer.sum is applied at the nominal scale
    of the image to each geometry in the fc, and the total area in meters squared
    is calculated by summing all feautes in the collection."""
    im = image.multiply(ee.Image.pixelArea())
    ns = image.projection().nominalScale()
    scale = ee.Algorithms.If(scale, scale, ns)
    bn = im.bandNames().get(0)

    def get_reduce_regions(fc):
        res = im.reduceRegions( \
            reducer=ee.Reducer.sum().unweighted(), \
            collection=ee.FeatureCollection(fc), \
            scale=scale, \
            tileScale=1) \
            .aggregate_sum('sum')
        return ee.FeatureCollection(ee.Feature(None, {'area_m2': res}))

    def get_reduce_map(f):
        res = im.reduceRegion( \
            reducer=ee.Reducer.sum().unweighted(), \
            geometry=f.geometry(), \
            scale=scale, \
            bestEffort=bestEffort, \
            maxPixels=1e8, \
            tileScale=1) \
            .get(bn)
        return ee.Feature(None, {'area_m2': res})

    def get_sample(f):
        fc = image.sample(
            region=f.geometry(), \
            numPixels=numPixels, \
            scale=scale, \
            tileScale=1, \
            dropNulls=False)
        tc = fc.filterMetadata(bn, 'equals', 1).aggregate_count(bn)
        tnc = fc.size()
        area = f.geometry().area(1)
        res = ee.Number(tc).divide(tnc).multiply(area)
        return ee.Feature(None, {'total_px': tnc, 'yes_px': tc, 'geom_area_m2': area, 'area_m2': res})

    out = ee.Dictionary({ \
        'reduce_regions': get_reduce_regions(fc),
        'reduce_region_map': ee.FeatureCollection(fc).map(get_reduce_map),
        'sample_region_map': ee.FeatureCollection(fc).map(get_sample)
    })
    return ee.Number(ee.FeatureCollection(out.get(method)).aggregate_sum('area_m2'))


def reduce_extent_fc(image, fc, bestEffort=False, scale=False):
    """ Given an ee.featureCollection (fc) of features each with
    a single geometry calculate the total extent (area_m2) using
    a single band binary image. The single band binary image is
    multiplied by pixel area, ee.Reducer.sum is applied at the nominal scale
    of the image to each geometry in the fc, and the total area in meters squared
    is calculated by summing all feautes in the collection."""
    im = image.multiply(ee.Image.pixelArea())
    ns = image.projection().nominalScale()
    scale = ee.Algorithms.If(scale, scale, ns)
    bn = im.bandNames().get(0)

    def get_reduce(f):
        res = im.reduceRegion( \
            reducer=ee.Reducer.sum().unweighted(), \
            geometry=f.geometry(), \
            scale=scale, \
            bestEffort=bestEffort, \
            maxPixels=1e12, \
            tileScale=4) \
            .get(bn)
        return ee.Feature(None, {'area_m2': res})

    fcc = ee.FeatureCollection(fc).map(get_reduce)
    return ee.Number(fcc.aggregate_sum('area_m2'))


def sample_extent_fc(image, fc, numPixels=5000, scale=False):
    """ Given an ee.featureCollection (fc) of features each with
    a single geometry calculate the total extent (area_m2) using
    a single band binary image. The single band binary image is
    sampled at the nominal scale of the image to each geometry in the fc
    , the proportion of 1s in the geometry is calculated, and the total area in meters squared
    is calculated by summing all feautes in the collection."""
    numPixels = ee.Number(numPixels)
    ns = image.projection().nominalScale()
    scale = ee.Algorithms.If(scale, scale, ns)
    bn = image.bandNames().get(0)

    def get_sample(f):
        fc = image.sample(
            region=f.geometry(), \
            numPixels=numPixels, \
            scale=scale, \
            tileScale=4, \
            dropNulls=True)
        tc = fc.filterMetadata(bn, 'equals', 1).aggregate_count(bn)
        area = f.geometry().area(1)
        res = ee.Number(tc).divide(numPixels).multiply(area)
        return ee.Feature(None, {'total_px': numPixels, 'yes_px': tc, 'geom_area_m2': area, 'area_m2': res})

    fcc = ee.FeatureCollection(fc).map(get_sample)
    return ee.Number(fcc.aggregate_sum('area_m2'))


def sample_statistics(image, geom, numPixels, scale):
    """ Sample within a region of a single band float image,
    returning a dictionary of statistics:
    accessed as ["values"]["<stat>"]
    Note this is an estimate"""
    bn = image.bandNames().getInfo()[0]
    fc = image.sample(region=geom, numPixels=numPixels, scale=scale, tileScale=16, dropNulls=True)
    return fc.aggregate_stats(bn)


def divide_geometry(feature):
    """ Divide feature geometry
    *
    * Split a features polygon geometry in 4 using its' center point
    * 
    * @param {ee.Feature} A feature with a polygon geometry to split.
    * 
    * @return {ee.FeatureCollection} Collection with 4 features per input feature.
    * 
    * @example aoi = Map.getBounds() fc = divideGeometry(aoi)
    """
    # Get coordinates of polygons bounds
    g = feature.geometry()
    l2 = g.bounds(1).coordinates().flatten()
    c2 = g.centroid(1).coordinates().flatten()
    # Create 4 cells dividing bounds at mid point
    t0 = ee.Feature(ee.Geometry.Polygon( \
        [l2.get(0), l2.get(1), \
         c2.get(0), l2.get(1), \
         c2.get(0), c2.get(1), \
         l2.get(0), c2.get(1), \
         l2.get(0), l2.get(1), \
         ]), {"name": "t0"})
    t1 = ee.Feature(ee.Geometry.Polygon( \
        [c2.get(0), l2.get(3), \
         l2.get(2), l2.get(3), \
         l2.get(2), c2.get(1), \
         c2.get(0), c2.get(1), \
         c2.get(0), l2.get(3), \
         ]), {"name": "t1"})
    t2 = ee.Feature(ee.Geometry.Polygon( \
        [c2.get(0), c2.get(1), \
         l2.get(4), c2.get(1), \
         l2.get(4), l2.get(5), \
         c2.get(0), l2.get(5), \
         c2.get(0), c2.get(1), \
         ]), {"name": "t2"})
    t3 = ee.Feature(ee.Geometry.Polygon( \
        [l2.get(0), c2.get(1), \
         c2.get(0), c2.get(1), \
         c2.get(0), l2.get(7), \
         l2.get(6), l2.get(7), \
         l2.get(0), c2.get(1), \
         ]), {"name": "t3"})
    # Make a featureCollection
    fc = ee.FeatureCollection([t0, t1, t2, t3, ])

    # Map intersection with feature and return cell name
    def tmp_f(f):
        return ee.Feature( \
            feature.geometry().intersection(f.geometry(), 1) \
            , {"name": f.get("name")})

    return ee.FeatureCollection(fc.map(tmp_f))


def ee_squaremeters_to_ha(value):
    """Converts square meters to hectares, and gives val to 2 decimal places"""
    tmp = ee.Number(value).divide(10000)
    tmp1 = ee.Number(ee.Number(tmp).format('%.2f'))
    return ee.Number.parse(tmp1)


def get_geocode(point):
    result = geocoder.osm(point, method='reverse', lang_code='en')
    if 'ERROR' in str(result): result = None
    return result


def loop_future(loop, f, a):
    return loop.run_in_executor(
        None,
        funct.partial(f, a),
    )


def buffer_geom(geom):
    buffer_size = geom.convexHull(1).bounds(1).area(1).sqrt().multiply(0.5)
    return geom.convexHull(1).buffer(buffer_size).bounds(1)


async def reverse_geocode_a_geostore(loop, shape):
    """ Take a shapely shape object and return geocoding results on the min/max coordinate locations"""
    w, s, e, n = shape.bounds
    bl = [s, w]
    br = [s, e]
    tl = [n, w]
    tr = [n, e]
    cd = list(shape.centroid.coords[0])[::-1]
    locs = [bl, tr, br, tl, cd]

    asyncio.set_event_loop(loop)

    futures = [loop_future(loop, get_geocode, loc) for loc in locs]
    for response in await asyncio.gather(*futures):
        # logging.info(f'Response: {response}')
        pass

    return [future.result() for future in futures]


def check_equivence(item1, item2):
    """Check to see if the two items are equal and neither is equal to None"""
    if item1 is None or item2 is None:
        return None
    else:
        return item1 == item2


def get_clip_vertex_list(geojson):
    """
    Take a geojson object and return a list of geometry vertices that ee can use as an argument to get thumbs
    """
    tmp_poly = []
    s = GeometryCollection([shape(feature["geometry"]).buffer(0) for feature in geojson.get('features')])
    simple = s[0].simplify(tolerance=0.01, preserve_topology=True)
    try:
        for x, y in zip(simple.exterior.coords.xy[0], simple.exterior.coords.xy[1]):
            tmp_poly.append([x, y])
    except:
        for x, y in zip(simple[0].exterior.coords.xy[0], simple[0].exterior.coords.xy[1]):
            tmp_poly.append([x, y])
    return tmp_poly


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'k', 'M', 'G', 'T', 'P'][magnitude])


def get_region(geom):
    """Take a valid geojson object, iterate over all features in that object.
        Build up a list of EE Polygons, and finally return an EE Feature
        collection. New as of 19th Sep 2017 (needed to fix a bug where the old
        function ignored multipolys)
    """
    polygons = []
    for feature in geom.get('features'):
        shape_type = feature.get('geometry').get('type')
        coordinates = feature.get('geometry').get('coordinates')
        if shape_type == 'MultiPolygon':
            polygons.append(ee.Geometry.MultiPolygon(coordinates))
        elif shape_type == 'Polygon':
            polygons.append(ee.Geometry.Polygon(coordinates))
        else:
            pass
    return ee.FeatureCollection(polygons)


def squaremeters_to_ha(value):
    """Converts square meters to hectares, and gives val to 2 decimal places"""
    tmp = value / 10000.
    return float('{0:4.2f}'.format(tmp))


def get_thresh_image(thresh, asset_id):
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


def dict_unit_transform(data, num):
    dasy = {}
    for key in data:
        dasy[key] = data[key] * num

    return dasy


def indicator_selector(row, indicator, begin, end):
    """Return Tons of biomass loss."""
    dasy = {}
    if indicator == 4:
        return row[2]['value']

    for i in range(len(row)):
        if row[i]['indicator_id'] == indicator and row[i]['year'] >= int(begin) and row[i]['year'] <= int(end):
            dasy[str(row[i]['year'])] = row[i]['value']

    return dasy


def dates_selector(data, begin, end):
    """Return Tons of biomass loss."""
    dasy = {}
    for key in data:
        if int(key) >= int(begin) and int(key) <= int(end):
            dasy[key] = data[key]

    return dasy


def sum_range(data, begin, end):
    return sum([data[key] for key in data if (int(key) >= int(begin)) and (int(key) < int(end))])


def admin_0_simplify(iso):
    """Check admin areas and return a relevant simplification or None"""
    # logging.info(f'[admin_0_simplify]: passed {iso}')
    admin_0_dic = {'ATA': 0.3,
                   'RUS': 0.3,
                   'CAN': 0.3,
                   'GRL': 0.3,
                   'USA': 0.3,
                   'CHN': 0.3,
                   'AUS': 0.1,
                   'BRA': 0.1,
                   'KAZ': 0.1,
                   'ARG': 0.1,
                   'IND': 0.1,
                   'MNG': 0.1,
                   'DZA': 0.1,
                   'MEX': 0.1,
                   'COD': 0.1,
                   'SAU': 0.1,
                   'IRN': 0.1,
                   'SWE': 0.1,
                   'LBY': 0.1,
                   'SDN': 0.1,
                   'IDN': 0.1,
                   'FIN': 0.01,
                   'NOR': 0.01,
                   'SJM': 0.01,
                   'ZAF': 0.01,
                   'UKR': 0.01,
                   'MLI': 0.01,
                   'TCD': 0.01,
                   'PER': 0.01,
                   'AGO': 0.01,
                   'NER': 0.01,
                   'CHL': 0.01,
                   'TUR': 0.01,
                   'EGY': 0.01,
                   'MRT': 0.01,
                   'BOL': 0.01,
                   'PAK': 0.01,
                   'ETH': 0.01,
                   'FRA': 0.01,
                   'COL': 0.01}
    simplification = admin_0_dic.get(iso, None)
    return simplification


def admin_1_simplify(iso, admin1):
    # logging.info(f'[admin_1_simplify]: passed {iso}/{admin1}')
    admin_1_dic = {'RUS': {60: 0.3,
                           35: 0.3,
                           12: 0.1,
                           80: 0.1,
                           18: 0.1,
                           28: 0.1,
                           30: 0.1,
                           4: 0.1,
                           40: 0.1,
                           32: 0.1,
                           24: 0.1,
                           83: 0.1,
                           3: 0.01,
                           69: 0.01,
                           9: 0.01,
                           46: 0.01,
                           26: 0.01,
                           45: 0.01,
                           66: 0.01,
                           55: 0.01,
                           50: 0.01},
                   'CAN': {8: 0.3,
                           6: 0.3,
                           11: 0.3,
                           9: 0.1,
                           2: 0.1,
                           1: 0.1,
                           3: 0.1,
                           12: 0.1,
                           13: 0.1,
                           5: 0.1},
                   'GRL': {2: 0.3, 3: 0.3, 5: 0.1},
                   'USA': {2: 0.3,
                           44: 0.1,
                           27: 0.01,
                           5: 0.01,
                           32: 0.01,
                           29: 0.01,
                           3: 0.01,
                           23: 0.01,
                           38: 0.01,
                           6: 0.01,
                           51: 0.01,
                           24: 0.01,
                           13: 0.01},
                   'AUS': {11: 0.3, 7: 0.3, 6: 0.1, 8: 0.1, 5: 0.1},
                   'CHN': {28: 0.3,
                           19: 0.1,
                           29: 0.1,
                           21: 0.1,
                           11: 0.1,
                           26: 0.01,
                           5: 0.01,
                           30: 0.01},
                   'BRA': {4: 0.1,
                           14: 0.1,
                           12: 0.1,
                           13: 0.01,
                           5: 0.01,
                           11: 0.01,
                           9: 0.01,
                           10: 0.01,
                           21: 0.01},
                   'NER': {1: 0.1},
                   'DZA': {41: 0.01, 1: 0.01, 22: 0.01},
                   'KAZ': {9: 0.01, 3: 0.01, 5: 0.01, 11: 0.01, 10: 0.01, 1: 0.01},
                   'SAU': {8: 0.01, 7: 0.01},
                   'MLI': {9: 0.01},
                   'LBY': {6: 0.01},
                   'EGY': {14: 0.01},
                   'ZAF': {8: 0.01},
                   'PAK': {2: 0.01},
                   'SDN': {10: 0.01, 8: 0.01},
                   'IND': {29: 0.01, 19: 0.01, 20: 0.01},
                   'ARG': {1: 0.01, 20: 0.01, 4: 0.01},
                   'PER': {17: 0.01},
                   'BOL': {8: 0.01},
                   'ETH': {8: 0.01, 9: 0.01},
                   'IDN': {23: 0.01},
                   'SJM': {2: 0.01}}
    try:
        admin1 = int(admin1)
    except:
        admin1 = -999
    simplification = None
    if admin_1_dic.get(iso):
        simplification = admin_1_dic.get(iso, None).get(admin1, None)
        logging.info(f'[admin_1_simplify]: {simplification}')
    return simplification
