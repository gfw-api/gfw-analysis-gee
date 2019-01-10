"""HANSEN SERVICE"""

import logging

import ee
from gfwanalysis.errors import HansenError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region, squaremeters_to_ha


class HansenService(object):

    @staticmethod
    def analyze(threshold, geojson, begin, end, aggregate_values=True):
        """For a given threshold and geometry return a dictionary of ha area.
        The threshold is used to identify which band of loss and tree to select.
        asset_id should be 'projects/wri-datalab/HansenComposite_14-15'
        Methods used to identify data:

        Gain band is a binary (0 = 0, 255=1) of locations where tree cover increased
        over data collction period. Calculate area of gain, by converting 255 values
        to 1, and then using a trick to convert this to pixel area
        (1 * pixelArea()). Finally, we sum the areas over a given polygon using a
        reducer, and convert from square meters to hectares.

        Tree_X bands show percentage canopy cover of forest, If missing, no trees
        present. Therefore, to count the tree area of a given canopy cover, select
        the band, convert it to binary (0=no tree cover, 1 = tree cover), and
        identify pixel area via a trick, multiplying all 1 vals by image.pixelArea.
        Then, sum the values over a region. Finally, divide the result (meters
        squared) by 10,000 to convert to hectares
        """
        try:
            d = {}
            asset_id = SETTINGS.get('gee').get('assets').get('hansen')
            extent_2010_asset = SETTINGS.get('gee').get('assets').get('hansen_2010_extent')
            hansen_v1_5_asset = SETTINGS.get('gee').get('assets').get('hansen_2017_v1_5')
            begin = int(begin.split('-')[0][2:])
            end = int(end.split('-')[0][2:])
            d['loss_start_year'] = begin
            d['loss_end_year'] = end
            region = get_region(geojson)
            reduce_args = {'reducer': ee.Reducer.sum().unweighted(),
                           'geometry': region,
                           'bestEffort': True,
                           'scale': 30,
                           'tileScale': 16}
            gfw_data = ee.Image(asset_id)
            hansen_v1_5 = ee.Image(hansen_v1_5_asset)
            loss_band = 'loss_{0}'.format(threshold)
            cover_band = 'tree_{0}'.format(threshold)
            # Identify 2000 forest cover at given threshold
            tree_area = hansen_v1_5.select('treecover2000').gt(float(threshold)).multiply(
                            ee.Image.pixelArea()).reduceRegion(**reduce_args).getInfo()
            d['tree_extent'] = squaremeters_to_ha(tree_area['treecover2000'])
            # Identify 2010 forest cover at given threshold
            extent2010_image = ee.Image(extent_2010_asset)
            extent2010_area = extent2010_image.gt(float(threshold)).multiply(
                                ee.Image.pixelArea()).reduceRegion(**reduce_args).getInfo()
            d['tree_extent2010'] = squaremeters_to_ha(extent2010_area['b1'])
            # Identify tree gain over data collection period
            gain = gfw_data.select('gain').divide(255.0).multiply(
                            ee.Image.pixelArea()).reduceRegion(**reduce_args).getInfo()
            d['gain'] = squaremeters_to_ha(gain['gain'])
            # Mask loss with itself to avoid overcounting errors
            tmp_img = gfw_data.select(loss_band).mask(gfw_data.select(loss_band))
            if aggregate_values:
                # Identify one loss area from begin year up untill end year
                loss_area_img = tmp_img.gte(begin).And(tmp_img.lte(end)).multiply(ee.Image.pixelArea())
                loss_total = loss_area_img.reduceRegion(**reduce_args).getInfo()
                d['loss'] = squaremeters_to_ha(loss_total[loss_band])
            else:
                # Identify loss area per year from beginning year to end year (inclusive)
                def reduceFunction(img):
                    out = img.reduceRegion(**reduce_args)
                    return ee.Feature(None, out)

                ## Calculate annual biomass loss - add subset images to a collection and then map a reducer to it
                collectionG = ee.ImageCollection([tmp_img.updateMask(tmp_img.eq(year)).divide(year).multiply(
                                ee.Image.pixelArea()).set({'year': 2000+year}) for year in range(begin, end + 1)])
                output = collectionG.map(reduceFunction).getInfo()
                d['loss'] = {}
                for row, yr in zip(output.get('features'), range(begin, end+1)):
                    d['loss'][yr+2000] = squaremeters_to_ha(row.get('properties').get(loss_band))
            return d
        except Exception as error:
            logging.error(str(error))
            raise HansenError(message='Error in Hansen Analysis')
