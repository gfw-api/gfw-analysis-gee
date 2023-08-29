"""Geostore SERVICE"""

from RWAPIMicroservicePython import request_to_microservice

from gfwanalysis.errors import GeostoreNotFound
from gfwanalysis.utils.geo import admin_0_simplify, admin_1_simplify


class GeostoreService(object):
    """."""

    @staticmethod
    def execute(uri, api_key, method="GET", body=None):
        try:
            response = request_to_microservice(
                uri=uri, api_key=api_key, method=method, body=body
            )
        except Exception as e:
            raise Exception(str(e))
        if response.get("errors"):
            error = response.get("errors")[0]
            if error.get("status") == 404:
                raise GeostoreNotFound(message="")
            else:
                raise Exception(error.get("detail"))

        geostore = response.get("data", None).get("attributes", None)
        geojson = geostore.get("geojson", None)
        area_ha = geostore.get("areaHa", None)

        return geojson, area_ha

    @staticmethod
    def create(geojson, api_key):
        return GeostoreService.execute(
            "/v2/geostore", api_key, body=geojson, method="POST"
        )

    @staticmethod
    def get(geostore, api_key):
        uri = f"/v2/geostore/{geostore}"
        return GeostoreService.execute(uri, api_key)

    @staticmethod
    def get_national(iso, api_key):
        # Lookup table here to reduce complexity
        # logging.info('[geostore service]: in get_national function')
        simplification = admin_0_simplify(iso)
        # logging.info(f'[geostore service]: simplification={simplification}')
        if simplification:
            url = f"/v2/geostore/admin/{iso}?simplify={simplification}"
        else:
            url = f"/v2/geostore/admin/{iso}"
        return GeostoreService.execute(url, api_key)

    @staticmethod
    def get_subnational(iso, id1, api_key):
        # logging.info('[geostore service]: in get_subnational function')
        simplification = admin_1_simplify(iso, id1)
        # logging.info(f'[geostore service]: simplification={simplification}')
        if simplification:
            url = f"/v2/geostore/admin/{iso}/{id1}?simplify={simplification}"
        else:
            url = f"/v2/geostore/admin/{iso}/{id1}"
        return GeostoreService.execute(url, api_key)

    @staticmethod
    def get_regional(iso, id1, id2, api_key):
        uri = f"/v2/geostore/admin/{iso}/{id1}/{id2}"
        return GeostoreService.execute(uri, api_key)

    @staticmethod
    def get_use(name, use_id, api_key):
        uri = f"/v2/geostore/use/{name}/{use_id}"
        return GeostoreService.execute(uri, api_key)

    @staticmethod
    def get_wdpa(wdpa_id, api_key):
        uri = f"/v2/geostore/wdpa/{wdpa_id}"
        return GeostoreService.execute(uri, api_key)
