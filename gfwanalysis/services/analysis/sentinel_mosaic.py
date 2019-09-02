"""EE SENTINEL TILE URL SERVICE"""

import requests
import ee
import logging

from gfwanalysis.errors import SentinelMosaicError
from gfwanalysis.utils.geo import get_region


def sentinel_cloud_mask(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(
        qa.bitwiseAnd(cirrusBitMask).eq(0))

    return image.updateMask(mask).divide(1e4).select("B.*").copyProperties(image, ["system:time_start"])


def buffer_geom(geom):
    buffer_size = geom.bounds(1).area(1).sqrt().multiply(0.5)
    return geom.buffer(buffer_size).bounds(1)

class SentinelMosaic(object):
    """Create dictionary with two urls to be used as webmap tiles for Sentinel 2
    data. One should be the tile outline, and the other is the RGB data visulised.
    Metadata should also be returned, containing cloud score etc.
    Note that the URLs from Earth Engine expire every 3 days.
    """

    @staticmethod
    def sentinel_mosaic_data(geojson, start, end, cloudscore_thresh, bounds):
        """
        """
        logging.info("[RECENT>DATA] function initiated")
        tmp = {}
        try:
            feat_col = get_region(geojson)
            if feat_col:
                feat = feat_col[0]
            else:
                return None

            buffered_geom = buffer_geom(feat.geometry())
            tmp['bbox'] = buffered_geom.getInfo()

            composite = ee.ImageCollection('COPERNICUS/S2').filterBounds(buffered_geom).filterDate(start, end).filter(
                ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloudscore_thresh)).map(sentinel_cloud_mask).median().clip(buffered_geom)

            im = composite.visualize(
                bands=["B4", "B3", "B2"], min=0, max=0.3, opacity=1.0)

            if bounds:
                # Adds vector of aoi bounds as raster to image
                empty = ee.Image().byte()
                fill = empty.paint({
                    featureCollection: feat_col
                }).visualize(bands=["constant"], min=14, opacity=0.1)

                outer = empty.paint({
                    featureCollection: feat_col,
                    color: '000000',
                    width: 4
                }).visualize(bands=["constant"], min=14)

                inner = empty.paint({
                    featureCollection: feat_col,
                    color: 'C0FF24',
                    width: 2
                }).visualize(bands=["constant"], min=14)

                im = im.blend(fill).blend(outer).blend(inner)

            thumbnail = im.getThumbURL({'dimensions': [250, 250]})
            tmp['thumbnail_url'] = thumbnail

            m_id = im.getMapId()
            base_url = 'https://earthengine.googleapis.com'
            url = (base_url + '/map/' +
                   m_id['mapid'] + '/{z}/{x}/{y}?token=' + m_id['token'])
            tmp['tile_url'] = url

            return tmp

        except:
            raise SentinelMosaicError(
                'Recent Images service failed to return image.')
