import ee
import logging

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
    tmp = value/10000.
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
        dasy[key] = data[key]*num

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
    #logging.info(f'[admin_0_simplify]: passed {iso}')
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