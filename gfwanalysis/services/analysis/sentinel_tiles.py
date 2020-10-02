"""EE SENTINEL TILE URL SERVICE"""

import logging

import ee


class SentinelTiles(object):
    """Create dictionary with two urls to be used as webmap tiles for Sentinel 2
    data. One should be the tile outline, and the other is the RGB data visulised.
    Metadata should also be returned.
    Note that the URLs from Earth Engine expire every 3 days.
    """

    @staticmethod
    def tile_url(image, viz_params=None):
        logging.info("TILE_URL function")
        """Create a target url for tiles for an image.
        """
        if viz_params:
            d = image.getMapId(viz_params)
            logging.info(d)
        else:
            d = image.getMapId()
        base_url = 'https://earthengine.googleapis.com'
        url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
        logging.info(url)
        return url

    @staticmethod
    def proxy_sentinel(lat, lon, start, end):
        """
        Sentinel covers all continental land surfaces (including inland waters) between latitudes 56° south and 83° north
            all coastal waters up to 20 km from the shore
            all islands greater than 100 km2
            all EU islands
            the Mediterranean Sea
            all closed seas (e.g. Caspian Sea).

        Filter by tiles that intersect a lat,lon point, and are within a date range, and have less than
        10% cloud cover, then find the lowest scoring cloud image.

        Note, we first filter by cloud less than X% and then pick the top, rather than just directly pick
        the best cloud scoring image, as these operations default to a subset of images. So we want to
        pick the best image, from a pre-selected subset of good images.

        Note the url generated expires after a few days and needs to be refreshed.
        e.g. variables
        lat = -16.66
        lon = 28.24
        start = '2017-01-01'
        end = '2017-03-01'
        """
        try:
            point = ee.Geometry.Point(float(lon), float(lat))
            S2 = ee.ImageCollection('COPERNICUS/S2'
                                    ).filterDate(
                start, end).filterBounds(
                point).sort('CLOUDY_PIXEL_PERCENTAGE', True).first()
            S2 = ee.Image(S2)
            d = S2.getInfo()  # grab a dictionary of the image metadata
            # logging.debug(d)
            S2 = S2.divide(10000)  # Convert to Top of the atmosphere reflectance
            S2 = S2.visualize(bands=["B4", "B3", "B2"], min=0, max=0.3, opacity=1.0)  # Convert to styled RGB image
            image_tiles = SentinelTiles.tile_url(S2)
            logging.info(image_tiles)
            boundary = ee.Feature(
                ee.Geometry.LinearRing(d.get('properties').get("system:footprint").get('coordinates')))
            boundary_tiles = SentinelTiles.tile_url(boundary, {'color': '4eff32'})
            meta = SentinelTiles.get_image_metadata(d)
            logging.info(meta)
            output = {}
            output = {'boundary_tiles': boundary_tiles,
                      'image_tiles': image_tiles,
                      'metadata': meta,
                      'sucsess': True}

            return output
        except:
            raise ValueError('Sentinel service failed to return image.')

    @staticmethod
    def get_image_metadata(d):
        """Return a dictionary of metadata"""
        image_name = d.get('id')
        date_info = image_name.split('COPERNICUS/S2/')[1]
        date_time = ''.join([date_info[0:4], '-', date_info[4:6], '-', date_info[6:8], ' ',
                             date_info[9:11], ':', date_info[11:13], ':', date_info[13:15], "Z"])
        product_id = d.get('properties').get('PRODUCT_ID')
        meta = {}
        meta = {'image_name': image_name, 'date_time': date_time, 'product_id': product_id}
        return meta
