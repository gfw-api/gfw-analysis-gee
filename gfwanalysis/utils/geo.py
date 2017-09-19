
import ee


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
