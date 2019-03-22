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
            # If one exists restore it from local storage
            model = create_model(instrument)
            # grab the image specified by the ID
            image = get_image(img_id)
            # Apply classifer to specified L8 or S2 image
            #logging.info(f"[classification_service]: classified version = {classified_image}")
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
    logging.info(f'[classification_service]: attempting to get url')
    viz = {'min': 0, 'max': 3, 'palette': ['yellow', 'blue', 'grey', 'green']}
    d = classified_image.getMapId(viz)
    logging.info(f'[classification_service]: d object = {d}')
    base_url = 'https://earthengine.googleapis.com'
    url = (base_url + '/map/' + d['mapid'] + '/{z}/{x}/{y}?token=' + d['token'])
    return url

def classify_image(image, model, instrument):
    if (instrument == "sentinel"):
        return image.select("B4","B3","B2").divide(100*100).classify(model)
    if (instrument == "landsat"):
        return image.select("B4","B3","B2").classify(model)
def create_model(instrument):
    try:
        simple_bands = ['B2', 'B3', 'B4']
        labeled_bands = simple_bands
        labeled_bands.append('cropland')
        if (instrument == 'sentinel'):
            trainingPoints = ee.FeatureCollection('projects/wri-datalab/trainingPoints')
        elif (instrument == 'landsat'):
            trainingPoints = ee.FeatureCollection('projects/wri-datalab/trainingLandsatPoints')
        classifier_args = {'features': trainingPoints, 'classProperty':'cropland',\
                                    'inputProperties':labeled_bands}
        classifier = ee.Classifier.randomForest(15).train(**classifier_args)
        return classifier
    except:
        return None

def get_image(img_id):
    """Check if S2 or L8 image and treat image accordingly"""
    try:
        result_img = ee.Image(img_id)
        return result_img
    except:
        return None


def get_model_from_bucket():
    logging.info(f'[classification_service]: attempting to get model from bucket')
    bucket_name = 'skydipper_materials'
    source_blob_name = 'classifier.pkl'
    destination_file_name = '/opt/downl_classif.pkl'
    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        print('Blob {} downloaded to {}.'.format(source_blob_name,destination_file_name))
        loaded_model = joblib.load("/opt/downl_classif.pkl")             #careful to change path when loading locally according to where it was downloaded
        return loaded_model
    except:
        return None