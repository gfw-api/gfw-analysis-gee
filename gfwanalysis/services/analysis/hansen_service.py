import logging
import inspect
import ee

from gfwanalysis.config import SETTINGS
from gfwanalysis.errors import HansenError
from gfwanalysis.utils.geo import get_region, ee_squaremeters_to_ha, get_extent_fc, divide_geometry

if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec


class HansenService(object):
    """For a given threshold, geometry, start and end date, apply a GEE method
      to calculate the total area (Ha) of tree cover in the year 2000 and 2010,
      the gain in tree cover between 2000 and 2012, and either the time-aggregated
      or annual tree cover loss within the geometry. This analysis requires a
      pre generated optimised gee asset (hansen_optimised) to be created that
      converts the latest Hansen tree cover loss and tree cover in 2010 products
      into binary rasters.

      # Arguments

      threshold -- The threshold for % tree cover in the year 2000, used to mask
                   treecover2000, treecover2010, and lossyear.
      geojson -- A valid geojson object.
      begin -- The start date for the analysis ('YYYY-MM-DD').
      end -- The end date for the analysis ('YYYY-MM-DD').
      aggregate_values -- Return the total aggregated loss during time period or
                          annual loss ('True).
      n_divisions -- Divide the geometry into n parts, apply analysis to each part
                     and return the total. 'n0' does no divisions, ('n4', 'n16',
                     'n32', 'n64'). Note for complex analysis too many divisions
                     can give GEE errors.
      method -- Which method is used to calculate area; 'reduce_regions' apply the
                .reduceRegions method to the geometry FeatureCollection,
                'reduce_region_map' map .reduceRegion over the geometry
                FeatureCollection, sample_region_map' map .sample over the
                geometry FeatureCollection.
      numPixels -- The total number of pixels to sample when using
                   'map_sample', note this is divided between splits.
      bestEffort -- Use the 'bestEffort=True' option when using 'map_reduce'. Note
                    care should be taken to ensure the bands pyramid policy
                    matches the data type (after transformation) to avoid errors
                    of upto 20%.
      """

    @staticmethod
    def analyze(threshold, geojson, begin, end, aggregate_values=True,
                n_divisions='n4', method='reduce_regions', num_pixels=10000, best_effort=False):
        try:
            # logging.info("Starting hansen analysis")
            # Set constants for the analysis
            # make all objects SERVER
            # returns ee.Number
            num_pixels = ee.Number(num_pixels).long()
            threshold = ee.Number(threshold)
            begin = ee.Number.parse(ee.Date(begin).format('yy').slice(0, 2))
            end = ee.Number.parse(ee.Date(end).format('yy').slice(0, 2))
            # returns ee.String
            n_divisions = ee.String(n_divisions)
            lossyear_band = ee.String('lossyear_').cat(threshold.format())
            treecover2000_band = ee.String('treecover2000_').cat(threshold.format())
            treecover2010_band = ee.String('treecover2010_').cat(threshold.format())
            gain20002012_band = ee.String('gain20002012')
            asset_id = ee.String(SETTINGS.get('gee').get('assets').get('hansen_optimised'))
            # Get the feature collection of geometries
            # returns ee.FeatureCollection
            region_nosplit = get_region(geojson)

            # logging.info("Got the feature collection of geometries")
            def divide_geometry_ntimes(feature, n_divisions=n_divisions):
                """
                  Optionally divide each of the fc's geoms by nX and return fc.
                  returns ee.FeatureCollection
                """
                fc4 = ee.FeatureCollection(divide_geometry(feature))
                fc16 = ee.FeatureCollection(fc4.map(divide_geometry)).flatten()
                fc64 = ee.FeatureCollection(fc16.map(divide_geometry)).flatten()
                fc256 = ee.FeatureCollection(fc64.map(divide_geometry)).flatten()
                out = ee.Dictionary({
                    'n0': ee.FeatureCollection(feature),
                    'n4': fc4,
                    'n16': fc16,
                    'n64': fc64,
                    'n256': fc256,
                })
                return ee.FeatureCollection(out.get(n_divisions))

            region_split = ee.FeatureCollection(region_nosplit).map(divide_geometry_ntimes).flatten()
            # logging.info("Divided the feature collection of geometries")
            # Choose if to split region
            # Note code for region_split OR region_nosplit is called depending
            # value of Boolean split_geometry=True
            # returns ee.FeatureCollection
            region_fc = ee.Algorithms.If(n_divisions, region_split, region_nosplit)
            n_features = ee.Number(ee.FeatureCollection(region_fc).size())

            # logging.info(f'Number of features is {n_features.getInfo()}')
            def get_area(f):
                return ee.Feature(None, {
                    'area_ha': ee_squaremeters_to_ha(f.geometry().area()),
                    'px': f.geometry().area().divide(30.0)
                })

            area_feature = ee.FeatureCollection(region_fc).map(get_area)
            total_area = area_feature.aggregate_sum('area_ha')
            # logging.info(f"Total area (Ha) is {total_area.getInfo()}")
            # logging.info(f"Area (Ha) per feature is {area_feature.aggregate_array('area_ha').getInfo()}")
            # logging.info(f"Pixels per feature is {area_feature.aggregate_array('px').getInfo()}")
            # if split_geometry divide numPixels by number of splits
            num_pixels = ee.Algorithms.If(n_divisions, ee.Number(num_pixels).divide(n_features).long(), num_pixels)
            # logging.info("Divided the feature collection of geometries")
            # Get the optimised hansen asset
            # these are all binary bands, except lossyear
            hansen_optimised = ee.Image(asset_id)

            # Identify year 2000 tree cover at given threshold
            # returns ee.Image
            treecover2000_image = ee.Image(hansen_optimised.select(treecover2000_band))
            treecover2000_image = treecover2000_image.updateMask(treecover2000_image)
            # returns ee.Number
            extent2000 = get_extent_fc(treecover2000_image, region_fc, method=method, bestEffort=best_effort,
                                       scale=False, numPixels=num_pixels)
            extent2000 = ee_squaremeters_to_ha(extent2000)
            # logging.info(f"Calculated tree cover extent in year 2000: {type(extent2000)}")
            # Identify 2010 tree cover at given threshold
            # returns ee.Image
            treecover2010_image = ee.Image(hansen_optimised.select(treecover2010_band))
            treecover2010_image = treecover2010_image.updateMask(treecover2010_image)
            # returns ee.Number
            extent2010 = get_extent_fc(treecover2010_image, region_fc, method=method, bestEffort=best_effort,
                                       scale=False, numPixels=num_pixels)
            extent2010 = ee_squaremeters_to_ha(extent2010)
            # logging.info(f"Calculated tree cover extent in year 2010: {type(extent2010)}")
            # Identify tree gain over data collection period
            # returns ee.Image
            # NOTE GAIN IS NOT THRESHOLDED BY TREECOVER2000!
            # FIXME IT MAKES NO SENSE TO EXPORT THRESHOLDED GAIN!
            gain20002012_image = ee.Image(hansen_optimised.select('gain20002012'))
            gain20002012_image = gain20002012_image.updateMask(gain20002012_image)
            # returns ee.Number
            gain = get_extent_fc(gain20002012_image, region_fc, method=method, bestEffort=best_effort, scale=False,
                                 numPixels=num_pixels)
            gain = ee_squaremeters_to_ha(gain)
            # logging.info(f"Calculated tree cover gain between 2000 and 2012:")
            # Identify loss
            # returns ee.Image
            lossyear_image = ee.Image(hansen_optimised.select(lossyear_band))
            lossyear_image = lossyear_image.updateMask(lossyear_image)
            # Select loss pixels from begin year till end year (0-18)
            # returns ee.Image
            loss_image_ag = lossyear_image.gte(begin).And(lossyear_image.lte(end))
            # returns ee.Number
            loss_ag = get_extent_fc(loss_image_ag, region_fc, method=method, bestEffort=best_effort, scale=False,
                                    numPixels=num_pixels)
            loss_ag = ee_squaremeters_to_ha(loss_ag)
            # logging.info("Calculated aggregated tree cover loss in period")
            # logging.info("Begin calculating yearly tree cover loss during period")
            # Identify loss area per year from beginning year to end year (inclusive)
            # Calculate annual biomass loss - add subset images to a collection
            # and then map a reducer over image collection
            # returns ee.List()
            year_list = ee.List.sequence(begin, end, 1)

            # returns ee.ImageCollection
            def tmp_f(year):
                year = ee.Number(year)
                return lossyear_image \
                    .updateMask(lossyear_image.eq(ee.Image.constant(year))) \
                    .divide(year) \
                    .set({'year': ee.Number(2000).add(year)})

            yearly_loss_collection = ee.ImageCollection(year_list.map(tmp_f))

            # logging.info("Created annual biomass loss image collection")
            # returns ee.FeatureCollection
            def reduceFunction(img):
                tmp = get_extent_fc(img, region_fc, method=method, bestEffort=best_effort, scale=False,
                                    numPixels=num_pixels)
                out = ee_squaremeters_to_ha(tmp)
                year = ee.Number(img.get('year')).format('%.0f')
                return ee.Feature(None, {'year': year, 'loss': out})

            output = yearly_loss_collection.map(reduceFunction)
            # returns ee.Dictionary
            loss_years = ee.Dictionary.fromLists( \
                output.aggregate_array('year'), \
                output.aggregate_array('loss'))
            # logging.info("Calculated yearly tree cover loss during period")
            # Choose which loss type to return
            # Note code for loss_ag OR loss_years is called depending
            # value of Boolean aggregate_values=True
            loss = ee.Algorithms.If(aggregate_values, loss_ag, loss_years)
            # Create dictionary of results
            # ee.Dictionary
            d = ee.Dictionary({
                'areaHa': total_area,
                'loss_start_year': begin,
                'loss_end_year': end,
                'treeExtent': extent2000,
                'treeExtent2010': extent2010,
                'gain': gain,
                'loss': loss

            })
            # Evaluate the dictionary of results
            tmp_d = d.getInfo()
            return tmp_d
        except Exception as error:
            logging.error(str(error))
            raise HansenError(message='Error in Hansen Analysis')
