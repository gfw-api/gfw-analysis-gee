"""Geostore SERVICE"""

from gfwanalysis.errors import GeostoreNotFound
from CTRegisterMicroserviceFlask import request_to_microservice


class GeostoreService(object):
    """."""

    @staticmethod
    def execute(config):
        try:
            response = request_to_microservice(config)
            if not response or response.get('errors'):
                raise GeostoreNotFound
            geostore = response.get('data', None).get('attributes', None)
            geojson = geostore.get('geojson', None)
            area_ha = geostore.get('areaHa', None)
        except Exception as e:
            raise GeostoreNotFound(message=str(e))
        return geojson, area_ha

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
