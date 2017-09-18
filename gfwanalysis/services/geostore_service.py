"""Geostore SERVICE"""

from gfwanalysis.errors import GeostoreNotFound
from CTRegisterMicroserviceFlask import request_to_microservice


class GeostoreService(object):
    """."""

    @staticmethod
    def execute(config):
        try:
            response = request_to_microservice(config)
        except Exception as e:
            raise Exception(str(e))
        if response.get('errors'):
            error = response.get('errors')[0]
            if error.get('status') == 404:
                raise GeostoreNotFound(message='')
            else:
                raise Exception(error.get('detail'))

        geostore = response.get('data', None).get('attributes', None)
        geojson = geostore.get('geojson', None)
        area_ha = geostore.get('areaHa', None)

        return geojson, area_ha

    @staticmethod
    def create(geojson):
        config = {
            'uri': '/geostore',
            'method': 'POST',
            'body': {
                'geojson': geojson
            }
        }
        return GeostoreService.execute(config)

    @staticmethod
    def get(geostore):
        config = {
            'uri': '/geostore/'+geostore,
            'method': 'GET'
        }
        return GeostoreService.execute(config)

    @staticmethod
    def get_national(iso):
        config = {
            'uri': '/geostore/admin/'+iso,
            'method': 'GET'
        }
        return GeostoreService.execute(config)

    @staticmethod
    def get_subnational(iso, id1):
        config = {
            'uri': '/geostore/admin/'+iso+'/'+id1,
            'method': 'GET'
        }
        return GeostoreService.execute(config)

    @staticmethod
    def get_use(name, use_id):
        config = {
            'uri': '/geostore/use/'+name+'/'+use_id,
            'method': 'GET'
        }
        return GeostoreService.execute(config)

    @staticmethod
    def get_wdpa(wdpa_id):
        config = {
            'uri': '/geostore/wdpa/'+wdpa_id,
            'method': 'GET'
        }
        return GeostoreService.execute(config)
