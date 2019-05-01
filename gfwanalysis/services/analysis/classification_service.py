"""CLASSIFICATION SERVICE"""

import logging
import ee
from gfwanalysis.errors import ClassificationError
from gfwanalysis.config import SETTINGS


class ClassificationService(object):

    @staticmethod
    def classify(img_id):
        """
        For a given area classify the forest amount and return a image with the classified forest and amount.
            example of a valid img_id = 'COPERNICUS/S2/20181222T115211_20181222T115210_T28RCS'
        """
        try:
            instrument = ""     #figure out if instrument is sentinel or landsat
            if (img_id.startswith("COPERNICUS")):
                instrument = "sentinel"
            elif (img_id.startswith("LANDSAT")):
                instrument = "landsat"
            #logging.info(f'instrument={instrument}')
            # If one exists restore it from local storage
            model = create_model(instrument)
            # grab the image specified by the ID
            image = get_image(img_id, instrument)
            # Apply classifer to specified L8 or S2 image
            classified_image = classify_image(image, model, instrument)
            # Generate tile url and return in d['url'] object
            url = get_image_url(classified_image)
            logging.info(f'[classification_service]: passed main logic url={url}')
            d = {}
            d['url'] = url
            return d
        except Exception as error:
            logging.error(str(error))
            raise ClassificationError(message='Error in Classification Analysis')


def get_image_url(classified_image):
    #logging.info(f'[classification_service]: attempting to get url')
    viz = {'min': 0, 'max': 5, 'palette': ['yellow', 'blue', 'grey', 'green', 'orange', 'darkgreen'], 'format':'png'}
    d = classified_image.getMapId(viz)
    #logging.info(f'[classification_service]: d object = {d}')
    base_url = 'https://earthengine.googleapis.com'
    url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
    return url

def classify_image(image, model, instrument):
    bands = ['B2', 'B3', 'B4', 'NDVI', 'NDWI', 'NDBI']
    if (instrument == "sentinel"):
        return image.select(bands).divide(100*100).classify(model)
    if (instrument == "landsat"):
        return image.select(bands).classify(model)

def create_model(instrument):
    try:
        bands = ['B2', 'B3', 'B4', 'NDVI', 'NDWI', 'NDBI']
        labeled_bands = bands
        labeled_bands.append('cropland')
        if (instrument == 'sentinel'):
            trainingPoints = ee.FeatureCollection('users/nicolaerigheriu/sentinel/sent_glob30Jaxa35k').\
                merge(ee.FeatureCollection('users/nicolaerigheriu/sentinel/sent_usCan_glob30Jaxa5k'))
        elif (instrument == 'landsat'):
            trainingPoints = ee.FeatureCollection('users/nicolaerigheriu/landsat/landsat_glob30_jaxa35k_toa').\
                merge(ee.FeatureCollection('landsat_usCan_glob30Jaxa5ktoa'))
        classifier_args = {'features': trainingPoints, 'classProperty':'cropland',\
                                    'inputProperties':labeled_bands}
        randomForest_args = {'numberOfTrees':17}
        classifier = ee.Classifier.randomForest(**randomForest_args)\
            .train(**classifier_args)
        return classifier
    except:
        return None

def get_image(img_id, instrument):
    """Check if S2 or L8 image and treat image accordingly"""
    try:
        result_img = ee.Image(img_id)
        result_img = addNDVIBands(result_img, instrument)
        return result_img
    except:
        return None

def addNDVIBands(image, instrument):
    if (instrument == 'landsat'):
        rawBands = [['B4', 'B3'], ['B4', 'B5'], ['B6', 'B5']]
    else:
        rawBands = [['B8', 'B4'], ['B3', 'B8'], ['B11', 'B8']]
    rawBands = ee.List(rawBands)
    image = insertBands(image, rawBands)
    return image

def insertBands(image, rawBands):
    NDVI = image.addBands(image.normalizedDifference(rawBands.get(0)))
    NDWI = NDVI.addBands(NDVI.normalizedDifference(rawBands.get(1)))
    NDWI = NDWI.addBands(NDWI.select(["nd"], ["NDVI"]))
    NDWI = NDWI.addBands(NDWI.select(["nd_1"], ["NDWI"]))
    NDBI = NDWI.addBands(NDWI.normalizedDifference(rawBands.get(2)))
    return NDBI.addBands(NDBI.select(["nd_2"], ["NDBI"]))