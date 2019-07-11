import pyproj
from functools import partial
from shapely.geometry import shape
from shapely.ops import transform


class AreaService(object):
    """Class for tabulating area of polygon without using the geostore"""

    @staticmethod
    def tabulate_area(geojson):
        area_ha = 0
        gj_type = geojson['type']
        if gj_type == 'FeatureCollection':
            for feature in geojson['features']:
                geom = shape(feature['geometry'])
                area_ha += AreaService.get_polygon_area(geom)
        else:
            geom = shape(geojson['geometry'])
            area_ha = AreaService.get_polygon_area(geom)
        return area_ha

    @staticmethod
    def get_polygon_area(geom):
    # source: https://gis.stackexchange.com/a/166421/30899
        geom_area = transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init='EPSG:4326'),
                pyproj.Proj(
                    proj='aea',
                    lat1=geom.bounds[1],
                    lat2=geom.bounds[3])),
            geom)
        # return area in ha
        return geom_area.area / 10000.
